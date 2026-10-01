import os
from flask import Blueprint, jsonify, request, session
from backend.services import log_collection
from backend.routes.auth_api import admin_required, login_required
from backend.cache_utils import query_cache
from backend import scheduler as sched
from backend.time_utils import ensure_kst_from_utc_naive

bp = Blueprint('system', __name__)

DEFAULT_SITE_GUIDE_MARKDOWN = """# 사이트 안내 👋

본 시스템은 분산된 주식 자산을 효율적으로 관리하고 최적의 포트폴리오를 유지할 수 있도록 돕는 통합 자산 관리 솔루션입니다.

### 📖 주요 메뉴 안내
1. **대시보드**: 전체 자산 현황과 시장 지수를 한눈에 확인하세요.
2. **계좌 잔고**: 각 계좌별 상세 보유 종목과 수익률을 관리합니다.
3. **포트폴리오**: 자산 배분 전략을 세우고 리밸런싱 가이드를 확인하세요.
4. **내 정보**: 비밀번호 변경 및 데이터 연동을 위한 API Key를 관리합니다.

> [!TIP]
> 상단의 **'매뉴얼 보기'** 버튼을 클릭하면 각 기능에 대한 이미지와 함께 더 자세한 사용 가이드를 확인하실 수 있습니다.
"""


def _serialize_log(log):
    ts = log.get('timestamp')
    ts = ensure_kst_from_utc_naive(ts) if hasattr(ts, 'isoformat') else ts
    return {
        'id': str(log.get('_id')),
        'timestamp': ts.isoformat() if hasattr(ts, 'isoformat') else str(ts),
        'level': log.get('level', ''),
        'message': log.get('message', ''),
        'module': log.get('module', ''),
        'lineno': log.get('lineno', 0),
    }


@bp.route('/logs', methods=['GET'])
@admin_required
def list_logs():
    """시스템 로그 목록 (최근 100건)"""
    logs = list(log_collection.find().sort('timestamp', -1).limit(100))
    return jsonify([_serialize_log(log) for log in logs])


@bp.route('/logs/clear', methods=['POST'])
@admin_required
def clear_logs():
    """로그 전체 삭제"""
    try:
        log_collection.delete_many({})
        return jsonify({'success': True, 'message': '시스템 로그가 초기화되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def _serialize_dt(dt):
    if dt is None:
        return None
    if hasattr(dt, 'isoformat'):
        return ensure_kst_from_utc_naive(dt).isoformat()
    return str(dt)


@bp.route('/settings/schedule', methods=['GET'])
@admin_required
def get_schedule():
    """계좌 현재가 크롤링 스케줄 조회 (관리자)"""
    doc = sched.get_schedule_doc()
    next_run = sched.get_next_run_time()
    return jsonify({
        'enabled': doc.get('enabled', False),
        'cron': doc.get('cron', sched.DEFAULT_CRON),
        'last_run': _serialize_dt(doc.get('last_run')),
        'next_run': _serialize_dt(next_run),
    })


@bp.route('/settings/schedule', methods=['PUT'])
@admin_required
def update_schedule():
    """계좌 현재가 크롤링 스케줄 수정 (관리자)"""
    data = request.get_json(silent=True) or {}
    enabled = data.get('enabled', False)
    cron = data.get('cron', '').strip() or sched.DEFAULT_CRON
    try:
        sched.set_schedule_doc(enabled, cron, sched.SETTINGS_BALANCE_REFRESH)
        return jsonify({
            'success': True,
            'message': '스케줄이 저장되었습니다.',
            'enabled': enabled,
            'cron': cron,
            'next_run': _serialize_dt(sched.get_next_run_time(sched.JOB_BALANCE_REFRESH)),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/settings/schedule/portfolio', methods=['GET'])
@admin_required
def get_portfolio_schedule():
    """포트폴리오 티커 자동 갱신 스케줄 조회 (관리자)"""
    doc = sched.get_schedule_doc(sched.SETTINGS_PORTFOLIO_REFRESH)
    next_run = sched.get_next_run_time(sched.JOB_PORTFOLIO_REFRESH)
    return jsonify({
        'enabled': doc.get('enabled', True),
        'interval': doc.get('interval', sched.DEFAULT_PORTFOLIO_INTERVAL),
        'last_run': _serialize_dt(doc.get('last_run')),
        'next_run': _serialize_dt(next_run),
    })


@bp.route('/settings/schedule/portfolio', methods=['PUT'])
@admin_required
def update_portfolio_schedule():
    """포트폴리오 티커 자동 갱신 스케줄 수정 (관리자)"""
    data = request.get_json(silent=True) or {}
    enabled = data.get('enabled', True)
    interval = data.get('interval', sched.DEFAULT_PORTFOLIO_INTERVAL)
    try:
        sched.set_schedule_doc(enabled, int(interval), sched.SETTINGS_PORTFOLIO_REFRESH)
        return jsonify({
            'success': True,
            'message': '포트폴리오 갱신 스케줄이 저장되었습니다.',
            'enabled': enabled,
            'interval': interval,
            'next_run': _serialize_dt(sched.get_next_run_time(sched.JOB_PORTFOLIO_REFRESH)),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/settings/price', methods=['GET'])
@login_required
def get_price_settings():
    """주식 현재가·강제 갱신 정책 조회 (로그인 사용자)."""
    from backend.services import settings_collection
    doc = settings_collection.find_one({'_id': 'price_settings'})
    return jsonify({
        'refresh_threshold_minutes': doc.get('refresh_threshold_minutes', 10) if doc else 10,
        'force_refresh_cooldown_sec': doc.get('force_refresh_cooldown_sec', 60) if doc else 60,
    })


@bp.route('/settings/price', methods=['PUT'])
@admin_required
def update_price_settings():
    """주식 현재가·강제 갱신 정책 수정 (관리자)"""
    from backend.services import settings_collection
    data = request.get_json(silent=True) or {}
    threshold = data.get('refresh_threshold_minutes', 10)
    force_cd = data.get('force_refresh_cooldown_sec', 60)
    try:
        settings_collection.update_one(
            {'_id': 'price_settings'},
            {'$set': {
                'refresh_threshold_minutes': int(threshold),
                'force_refresh_cooldown_sec': max(5, int(force_cd)),
            }},
            upsert=True
        )
        query_cache.invalidate(('settings', 'price_threshold'))
        query_cache.invalidate(('settings', 'force_refresh_cooldown_sec'))
        return jsonify({'success': True, 'message': '현재가 갱신 설정이 저장되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/settings/site-guide', methods=['GET'])
def get_site_guide():
    """사이트 안내 마크다운 조회 (로그인 사용자)."""
    from backend.services import settings_collection
    doc = settings_collection.find_one({'_id': 'site_guide'})
    markdown = (doc or {}).get('markdown') or DEFAULT_SITE_GUIDE_MARKDOWN
    updated_at = (doc or {}).get('updated_at')
    updated_by = (doc or {}).get('updated_by')
    return jsonify({
        'markdown': markdown,
        'updated_at': _serialize_dt(updated_at),
        'updated_by': updated_by,
        'version': os.environ.get('APP_VERSION', 'v1.0.0'),
        'build_date': os.environ.get('APP_BUILD_DATE', '-'),
    })


@bp.route('/settings/site-guide', methods=['PUT'])
@admin_required
def update_site_guide():
    """사이트 안내 마크다운 저장 (관리자)."""
    from backend.services import settings_collection
    from datetime import datetime

    data = request.get_json(silent=True) or {}
    markdown = (data.get('markdown') or '').strip()
    if not markdown:
        return jsonify({'success': False, 'message': 'markdown 내용을 입력해 주세요.'}), 400

    now_utc = datetime.utcnow()
    updated_by = session.get('username', '')
    settings_collection.update_one(
        {'_id': 'site_guide'},
        {'$set': {
            'markdown': markdown,
            'updated_at': now_utc,
            'updated_by': updated_by,
        }},
        upsert=True
    )
    return jsonify({
        'success': True,
        'message': '사이트 안내가 저장되었습니다.',
        'updated_at': _serialize_dt(now_utc),
        'updated_by': updated_by,
    })
