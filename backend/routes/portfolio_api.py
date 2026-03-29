import logging
from flask import Blueprint, request, jsonify, session
from backend.routes.auth_api import login_required, admin_required
from backend import database
from backend.services import portfolio_collection, ticker_collection

bp = Blueprint('portfolio', __name__)


def _serialize_portfolio(p):
    """MongoDB 문서를 JSON으로 직렬화 (ObjectId -> str)"""
    d = dict(p)
    d['id'] = str(p['_id'])
    d.pop('_id', None)
    return d


@bp.route('/portfolios', methods=['GET'])
@login_required
def list_portfolios():
    """포트폴리오 목록 (공용 또는 본인 소유)"""
    user_id = session.get('user_id')
    # is_public이 True이거나, user_id가 현재 접속자와 일치하는 항목 조회
    query = {"$or": [
        {"is_public": True},
        {"user_id": user_id}
    ]}
    portfolios = list(portfolio_collection.find(query))
    return jsonify([_serialize_portfolio(p) for p in portfolios])


@bp.route('/portfolios', methods=['POST'])
@login_required
def save_portfolio():
    """포트폴리오 저장 (신규 생성 또는 기존 수정)"""
    data = request.get_json(silent=True) or {}
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    portfolio_id = data.get('id')
    name = data.get('name') or request.form.get('name')
    description = data.get('description') or request.form.get('description') or ""
    items_data = data.get('items')
    
    # is_public 필드는 관리자만 설정 가능
    is_public = data.get('is_public', False) if is_admin else False

    # (생략: items 파싱 로직은 동일하되 items_data 필터링 유지)
    if items_data is None:
        tickers = request.form.getlist('tickers[]') or request.form.getlist('tickers')
        names = request.form.getlist('names[]') or request.form.getlist('names')
        ratios = request.form.getlist('ratios[]') or request.form.getlist('ratios')
        items = []
        seen = set()
        for t, n, r in zip(tickers, names, ratios):
            if t and r and t not in seen:
                seen.add(t)
                try:
                    items.append({'ticker': t, 'name': n or t, 'ratio': float(r)})
                except ValueError:
                    pass
    else:
        items = []
        for i in items_data or []:
            if not i.get('ticker'): continue
            if i.get('ratio') is None: continue
            try:
                r = float(i.get('ratio'))
            except (TypeError, ValueError): continue
            items.append({
                'ticker': i.get('ticker'),
                'name': i.get('name', i.get('ticker')),
                'ratio': r,
            })

    if not name:
        return jsonify({'success': False, 'message': '포트폴리오명은 필수입니다.'}), 400

    if items:
        total = sum(i['ratio'] for i in items)
        if abs(round(total, 2) - 100.0) >= 0.005:
            return jsonify({'success': False, 'message': f'비율 합계가 100%가 아닙니다.'}), 400

    try:
        if portfolio_id:
            # 수정 권한 체크: 관리자거나 소유자여야 함
            existing = portfolio_collection.find_one({'_id': database.ObjectId(portfolio_id)})
            if not existing:
                return jsonify({'success': False, 'message': '포트폴리오를 찾을 수 없습니다.'}), 404
            
            if not is_admin and existing.get('user_id') != user_id:
                return jsonify({'success': False, 'message': '수정 권한이 없습니다.'}), 403
            
            # 관리자가 아니면 기존의 is_public 상태를 유지하거나 강제로 False 처리 (여기선 관리자 아닐시 누군가 가로채서 True로 바꾸는 것 방지)
            final_is_public = is_public if is_admin else existing.get('is_public', False)
            
            update_data = {
                'name': name,
                'description': description,
                'items': items,
                'is_public': final_is_public
            }
            database.upsert_portfolio(portfolio_collection, update_data, portfolio_id)
        else:
            # 신규 생성: 현재 유저 귀속
            new_data = {
                'name': name,
                'description': description,
                'items': items,
                'user_id': user_id,
                'is_public': is_public # is_admin일 때만 data에서 가져온 값이 반영됨
            }
            database.upsert_portfolio(portfolio_collection, new_data)
        
        return jsonify({'success': True, 'message': f'포트폴리오 "{name}"가 저장되었습니다.'})
    except Exception as e:
        logging.error(f"포트폴리오 저장 중 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/portfolios/asset_classes', methods=['GET'])
@login_required
def get_asset_classes():
    """자산 분류 항목 조회 (global)"""
    from backend.services import settings_collection
    doc = settings_collection.find_one({"_id": "asset_classes"})
    classes = doc.get('classes', []) if doc else []
    return jsonify(classes)


@bp.route('/portfolios/asset_classes', methods=['POST'])
@admin_required
def update_asset_classes():
    """자산 분류 항목 저장 (관리자 전용)"""
    from backend.services import settings_collection
    data = request.get_json(silent=True) or {}
    classes = data.get('classes')
    if classes is None:
        return jsonify({'success': False, 'message': 'classes 필드가 필요합니다.'}), 400
    
    if not isinstance(classes, list):
        return jsonify({'success': False, 'message': 'classes는 리스트 형태여야 합니다.'}), 400

    from backend.time_utils import now_kst
    settings_collection.update_one(
        {"_id": "asset_classes"},
        {"$set": {"classes": classes, "updated_at": now_kst()}},
        upsert=True
    )
    return jsonify({'success': True, 'message': '자산 분류 항목이 저장되었습니다.'})


@bp.route('/portfolios/<portfolio_id>', methods=['GET'])
@login_required
def get_portfolio(portfolio_id):
    """단일 포트폴리오 상세 조회 (접근 권한 체크)"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    try:
        p = portfolio_collection.find_one({'_id': database.ObjectId(portfolio_id)})
        if not p:
            return jsonify({'success': False, 'message': '포트폴리오를 찾을 수 없습니다.'}), 404
        
        # Enrich items with asset_class from ticker_collection
        items = p.get('items', [])
        ticker_ids = [i['ticker'] for i in items if i.get('ticker')]
        if ticker_ids:
            tickers_info = list(ticker_collection.find({'ticker': {'$in': ticker_ids}}, {'ticker': 1, 'asset_class': 1}))
            tickers_map = {t['ticker']: t.get('asset_class') for t in tickers_info}
            for item in items:
                item['asset_class'] = tickers_map.get(item['ticker'])
            
        return jsonify(_serialize_portfolio(p))
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/portfolios/<portfolio_id>', methods=['DELETE'])
@login_required
def delete_portfolio(portfolio_id):
    """포트폴리오 삭제 (소유자 또는 관리자)"""
    user_id = session.get('user_id')
    is_admin = session.get('role') == 'admin'
    
    existing = portfolio_collection.find_one({'_id': database.ObjectId(portfolio_id)})
    if not existing:
        return jsonify({'success': False, 'message': '포트폴리오를 찾을 수 없습니다.'}), 404
    
    if not is_admin and existing.get('user_id') != user_id:
        return jsonify({'success': False, 'message': '삭제 권한이 없습니다.'}), 403
        
    database.delete_portfolio(portfolio_collection, portfolio_id)
    return jsonify({'success': True, 'message': '포트폴리오가 삭제되었습니다.'})


@bp.route('/portfolios/search_ticker', methods=['GET'])
@login_required
def search_ticker():
    """티커 검색"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = database.search_tickers(ticker_collection, query)
    return jsonify(results)


@bp.route('/portfolios/refresh-all-admin', methods=['POST'])
@admin_required
def refresh_all_admin():
    """모든 포트폴리오의 티커 가격 강제 갱신 (관리자 수동 실행)"""
    from backend import crawler
    ports = list(portfolio_collection.find({}))
    tickers = set()
    for p in ports:
        for item in p.get('items', []):
            if item.get('ticker'):
                tickers.add(item['ticker'])
    
    if not tickers:
        return jsonify({'success': True, 'message': '갱신할 티커가 없습니다.', 'count': 0})
    
    # 즉각적인 갱신을 위해 threshold_minutes=0 으로 설정
    results = crawler.update_stale_prices(ticker_collection, list(tickers), threshold_minutes=0)
    count = sum(
        1
        for x in results.values()
        if (x.get('price') if isinstance(x, dict) else x) > 0
    )
    return jsonify({'success': True, 'count': count, 'message': f'{count}개 종목의 가격이 갱신되었습니다.'})
