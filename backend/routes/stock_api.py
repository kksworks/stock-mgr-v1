import logging
from flask import Blueprint, request, jsonify
from backend import crawler, database
from backend import config_loader
from backend.cache_utils import query_cache
from backend.services import ticker_collection
from backend.routes.auth_api import admin_required, login_required

bp = Blueprint('stock', __name__)
_config = config_loader.load_config()
_QUERY_CACHE_TTL_SEC = max(1, config_loader.get_int(_config, 'performance', 'query_cache_ttl_sec', 5))
_QUERY_CACHE_WAIT_SEC = max(1, config_loader.get_int(_config, 'performance', 'query_cache_wait_timeout_sec', 3))


@bp.route('/tickers', methods=['GET'])
@login_required
def list_tickers():
    """티커 목록 (검색 지원)"""
    query = request.args.get('q')
    if query:
        tickers = database.search_tickers(ticker_collection, query)
    else:
        # 검색어 없으면 상위 100개
        tickers = list(ticker_collection.find({}, {'_id': 0}).limit(100))
    return jsonify(tickers)


@bp.route('/tickers/<ticker>', methods=['GET'])
@login_required
def get_ticker_detail(ticker):
    """특정 티커 상세 정보"""
    data = ticker_collection.find_one({'ticker': ticker}, {'_id': 0})
    if data:
        return jsonify(data)
    return jsonify({'success': False, 'message': '티커를 찾을 수 없습니다.'}), 404


@bp.route('/tickers/prices', methods=['GET'])
# 지수 등 공용 정보 조회를 위해 로그인을 요구하지 않도록 변경
def get_ticker_prices():
    """여러 티커의 현재가를 한 번에 조회 (필요 시 크롤링)"""
    tickers_str = request.args.get('tickers', '')
    if not tickers_str:
        return jsonify({})
    
    ticker_list = [t.strip() for t in tickers_str.split(',') if t.strip()]
    if not ticker_list:
        return jsonify({})
    
    # 1. 가격 갱신 (threshold는 config.ini 기본값 사용)
    try:
        threshold = max(1, config_loader.get_int(_config, 'performance', 'price_refresh_threshold_minutes', 10))
        price_map = crawler.update_stale_prices(ticker_collection, ticker_list, threshold)
    except Exception as e:
        logging.error(f"Error updating stale prices in batch: {e}")
        # 실패 시 DB에 있는 거라도 반환하기 위해 빈 맵으로 진행
        price_map = {}

    sorted_tickers = sorted(set(ticker_list))
    # 크롤/upsert 직후 티커 문서 캐시가 이전 스냅샷이면 병합 결과가 어긋날 수 있어 무효화
    if price_map:
        query_cache.invalidate(('stock_api_ticker_docs', tuple(sorted_tickers)))

    # 2. 티커 정보(이름 등) 조회

    def _load_docs():
        docs_cursor = ticker_collection.find(
            {'ticker': {'$in': sorted_tickers}},
            {
                '_id': 0,
                'ticker': 1,
                'name': 1,
                'current_price': 1,
                'prev_day_change': 1,
                'prev_day_change_pct': 1,
                'price_updated_at': 1,
            },
        )
        return list(docs_cursor)

    docs = query_cache.get_or_load(
        key=('stock_api_ticker_docs', tuple(sorted_tickers)),
        ttl_seconds=_QUERY_CACHE_TTL_SEC,
        loader=_load_docs,
        wait_timeout=_QUERY_CACHE_WAIT_SEC,
    )

    result = {}
    db_map = {d['ticker']: d for d in docs}

    for t in ticker_list:
        d = db_map.get(t)
        qm = price_map.get(t)
        if isinstance(qm, dict):
            pr = qm.get('price')
            if pr is None:
                p = d.get('current_price', 0) if d else 0
            else:
                p = pr
            pch = qm.get('prev_day_change')
            pcp = qm.get('prev_day_change_pct')
        else:
            p = qm if qm is not None else (d.get('current_price', 0) if d else 0)
            pch = d.get('prev_day_change') if d else None
            pcp = d.get('prev_day_change_pct') if d else None
        
        # Ensure p is numeric (float or int)
        try:
            p = float(p)
        except (TypeError, ValueError):
            p = 0.0
            
        n = d.get('name', t) if d else t
        if pch is None and d:
            pch = d.get('prev_day_change')
        if pcp is None and d:
            pcp = d.get('prev_day_change_pct')
        pu = d.get('price_updated_at') if d else None
        if pu is not None and hasattr(pu, 'isoformat'):
            pu = pu.isoformat()
        result[t] = {
            'price': p,
            'name': n,
            'prev_day_change': pch,
            'prev_day_change_pct': pcp,
            'price_updated_at': pu,
        }
    return jsonify(result)


@bp.route('/crawl', methods=['POST'])
@admin_required
def crawl_stock_data():
    """주식 정보 크롤링"""
    try:
        count = crawler.fetch_tickers(ticker_collection)
        # 티커 메타데이터가 크게 바뀔 수 있어 캐시 전체를 무효화.
        query_cache.clear()
        return jsonify({'success': True, 'message': f'성공적으로 {count}개의 주식 정보를 업데이트했습니다.', 'count': count})
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        logging.error(f"크롤링 프로세스 중 치명적 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'크롤링 중 오류 발생: {str(e)}'}), 500


@bp.route('/add_field', methods=['POST'])
@admin_required
def add_custom_field():
    """티커에 커스텀 필드 추가"""
    data = request.get_json(silent=True) or {}
    ticker = data.get('ticker') or request.form.get('ticker')
    field_name = data.get('field_name') or request.form.get('field_name')
    field_value = data.get('field_value') or request.form.get('field_value')

    if not ticker or not field_name:
        return jsonify({'success': False, 'message': '티커와 필드명은 필수입니다.'}), 400

    try:
        result = database.update_custom_field(ticker_collection, ticker, field_name, field_value)
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': f'{ticker} 종목에 {field_name} 필드가 추가/수정되었습니다.'})
        return jsonify({'success': False, 'message': f'티커 {ticker}를 찾을 수 없습니다.'}), 404
    except Exception as e:
        logging.error(f"필드 추가 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/tickers/<ticker>/asset_class', methods=['POST'])
@admin_required
def update_asset_class(ticker):
    """특정 티커의 자산분류 업데이트 (관리자 전용)"""
    data = request.get_json(silent=True) or {}
    asset_class = data.get('asset_class')

    try:
        result = database.update_custom_field(ticker_collection, ticker, 'asset_class', asset_class)
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': f'티커 {ticker}의 자산 분류가 업데이트되었습니다.'})
        return jsonify({'success': False, 'message': f'티커 {ticker}를 찾을 수 없습니다.'}), 404
    except Exception as e:
        logging.error(f"자산분류 업데이트 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
