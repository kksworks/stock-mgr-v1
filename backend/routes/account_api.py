import logging
import uuid
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from bson.objectid import ObjectId
from bson.decimal128 import Decimal128
from flask import Blueprint, request, jsonify, session, current_app
from backend.services import (
    ticker_collection, account_collection, transaction_collection,
    portfolio_collection, balance_collection, balance_history_collection,
    account_monthly_trend_collection, user_collection,
)
from backend.account_monthly_trend import (
    account_ids_needing_trend_backfill,
    backfill_monthly_trends_from_history,
    load_monthly_trend_series,
    monthly_cutoff_key,
    upsert_monthly_trend_row,
)
from backend import crawler
from backend import config_loader
from backend.cache_utils import query_cache
from backend.time_utils import now_kst, ensure_kst_from_utc_naive
from backend.routes.auth_api import login_required, admin_required
import pandas as pd

bp = Blueprint('account', __name__)

_config = config_loader.load_config()
# 계좌 재계산 병렬 워커 수 (CPU 사용량 제어)
_RECALC_ACCOUNT_WORKERS = max(1, config_loader.get_int(_config, 'performance', 'recalc_account_workers', 1))
# 백그라운드 refresh 동시 실행/대기 개수 제한 (메모리 급증 방지)
_BACKGROUND_REFRESH_WORKERS = max(1, config_loader.get_int(_config, 'performance', 'background_refresh_workers', 1))
_BACKGROUND_REFRESH_QUEUE = max(0, config_loader.get_int(_config, 'performance', 'background_refresh_queue', 4))
_BACKGROUND_REFRESH_SLOTS = _BACKGROUND_REFRESH_WORKERS + _BACKGROUND_REFRESH_QUEUE
_BACKGROUND_REFRESH_SEMAPHORE = threading.BoundedSemaphore(value=_BACKGROUND_REFRESH_SLOTS)
_BACKGROUND_REFRESH_EXECUTOR = ThreadPoolExecutor(max_workers=_BACKGROUND_REFRESH_WORKERS, thread_name_prefix='bg-refresh')
_QUERY_CACHE_TTL_SEC = max(1, config_loader.get_int(_config, 'performance', 'query_cache_ttl_sec', 5))
_QUERY_CACHE_WAIT_SEC = max(1, config_loader.get_int(_config, 'performance', 'query_cache_wait_timeout_sec', 3))
_BACKGROUND_REFRESH_COOLDOWN_SEC = max(5, config_loader.get_int(_config, 'performance', 'background_refresh_cooldown_sec', 30))
_FORCE_REFRESH_COOLDOWN_DEFAULT_SEC = max(5, config_loader.get_int(_config, 'performance', 'force_refresh_cooldown_sec', 60))
_NEXT_ALLOWED_REFRESH = {}
_NEXT_ALLOWED_FORCE_REFRESH = {}
_NEXT_ALLOWED_REFRESH_LOCK = threading.Lock()


def _session_is_admin():
    return session.get('role') == 'admin'


def _normalize_shared_user_ids(raw):
    """공유 사용자 ID 목록 (문자열 ObjectId 리스트)."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [x.strip() for x in raw.split(',') if x.strip()]
    if not isinstance(raw, (list, tuple)):
        return []
    out, seen = [], set()
    for x in raw:
        s = str(x).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _normalize_tags(raw):
    """태그 목록 문자열 정규화(중복 제거, 공백 제거)."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [x.strip() for x in raw.split(',') if x.strip()]
    if not isinstance(raw, (list, tuple)):
        return []
    out, seen = [], set()
    for x in raw:
        s = str(x).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _str_user_id(val):
    if val is None:
        return None
    return str(val)


def _user_can_access_account(account_doc, session_user_id):
    if not account_doc:
        return False
    if account_doc.get('is_public'):
        return True
    if not session_user_id:
        return False
    if _str_user_id(account_doc.get('user_id')) == _str_user_id(session_user_id):
        return True
    shared = account_doc.get('shared_user_ids') or []
    su = {_str_user_id(s) for s in shared}
    return _str_user_id(session_user_id) in su


def _find_account_for_session(account_uuid):
    """관리자/소유자/공유 사용자 또는 공개 계좌인 경우 문서 반환."""
    acc = account_collection.find_one({'uuid': account_uuid})
    if not acc:
        return None
    uid = session.get('user_id')
    if _session_is_admin():
        return acc
    if _user_can_access_account(acc, uid):
        return acc
    return None


def _accounts_cursor_for_session():
    """현재 세션 사용자가 볼 수 있는 계좌 커서 (비로그인은 공개 계좌)."""
    uid_str = session.get('user_id')
    if not uid_str:
        return account_collection.find({'is_public': True})
        
    if _session_is_admin():
        return account_collection.find({})
        
    # 문자열과 ObjectId 양쪽 모두 대응 가능하도록 쿼리 (레거시 지원)
    ids_to_match = [uid_str]
    try:
        ids_to_match.append(ObjectId(uid_str))
    except Exception:
        pass
        
    return account_collection.find({
        '$or': [
            {'is_public': True},
            {'user_id': {'$in': ids_to_match}},
            {'shared_user_ids': {'$in': ids_to_match}}
        ]
    })


def _serialize_account(a):
    """MongoDB 문서를 JSON으로 직렬화 (uuid -> id)"""
    d = dict(a)
    d['id'] = a.get('uuid') or str(a['_id'])
    d.pop('_id', None)
    if d.get('user_id') is not None:
        d['user_id'] = str(d['user_id'])
    if 'shared_user_ids' not in d or d['shared_user_ids'] is None:
        d['shared_user_ids'] = []
    else:
        d['shared_user_ids'] = [str(x) for x in d['shared_user_ids']]
    if 'tags' not in d or d['tags'] is None:
        d['tags'] = []
    else:
        d['tags'] = _normalize_tags(d['tags'])
    d['is_public'] = bool(d.get('is_public', False))
    return d


def _bulk_get_user_display_names(user_ids_list):
    """여러 user_id에 대해 username 맵을 한 번에 조회."""
    unique_ids = set()
    for uid in user_ids_list:
        if uid:
            try:
                unique_ids.add(ObjectId(uid))
            except Exception:
                pass
    if not unique_ids:
        return {}
    
    users = user_collection.find({'_id': {'$in': list(unique_ids)}}, {'username': 1})
    return {str(u['_id']): u.get('username') for u in users}


def _serialize_account_with_owner_labels(a, user_name_map=None):
    """관리자 목록용: 소유자·공유 사용자 로그인명 표시. user_name_map이 있으면 N+1 쿼리 방지."""
    d = _serialize_account(a)
    uid = d.get('user_id')
    
    if user_name_map is not None:
        d['owner_username'] = user_name_map.get(str(uid)) if uid else None
        names = []
        for sid in d.get('shared_user_ids') or []:
            names.append({'id': sid, 'username': user_name_map.get(str(sid))})
        d['shared_users_display'] = names
    else:
        # 레거시/단일 조회용 (가급적 지양)
        if uid:
            try:
                ou = user_collection.find_one({'_id': ObjectId(uid)}, {'username': 1})
                d['owner_username'] = ou.get('username') if ou else None
            except Exception:
                d['owner_username'] = None
        else:
            d['owner_username'] = None
        names = []
        for sid in d.get('shared_user_ids') or []:
            try:
                su = user_collection.find_one({'_id': ObjectId(sid)}, {'username': 1})
                if su:
                    names.append({'id': sid, 'username': su.get('username')})
            except Exception:
                names.append({'id': sid, 'username': None})
        d['shared_users_display'] = names
    return d


def _serialize_transaction(t):
    d = dict(t)
    d['id'] = str(t['_id'])
    d.pop('_id', None)
    if hasattr(d.get('date'), 'isoformat'):
        d['date'] = ensure_kst_from_utc_naive(d['date']).isoformat() if d.get('date') else None
    return d


def _serialize_portfolio(p):
    """MongoDB 문서를 JSON으로 직렬화 (ObjectId -> str)"""
    d = dict(p)
    d['id'] = str(p['_id'])
    d['is_public'] = bool(p.get('is_public', False))
    d['level'] = p.get('level', 1)
    d.pop('_id', None)
    return d


@bp.route('/accounts', methods=['GET'])
@login_required
def list_accounts():
    """계좌 목록: 일반 사용자는 본인 소유·공유받은 계좌, 관리자는 전체."""
    accounts = list(_accounts_cursor_for_session())
    if _session_is_admin():
        # 모든 계좌의 소유자/공유자 ID 수집하여 한 번에 이름 조회 (N+1 방지)
        all_user_ids = []
        for a in accounts:
            if a.get('user_id'): all_user_ids.append(str(a['user_id']))
            shared = a.get('shared_user_ids') or []
            all_user_ids.extend([str(x) for x in shared])
        
        user_name_map = _bulk_get_user_display_names(all_user_ids)
        return jsonify([_serialize_account_with_owner_labels(a, user_name_map) for a in accounts])
    
    return jsonify([_serialize_account(a) for a in accounts])


@bp.route('/accounts', methods=['POST'])
@login_required
def update_account():
    """계좌 추가/수정. ID가 있으면 수정, 없으면 추가. 관리자는 소유자·공유 사용자 지정 가능."""
    data = request.get_json(silent=True) or {}
    account_id = data.get('id')
    session_uid = session.get('user_id')
    is_adm = _session_is_admin()

    if not data.get('account_number') or not data.get('account_name'):
        return jsonify({'success': False, 'message': '계좌명과 계좌번호는 필수 항목입니다.'}), 400

    try:
        recalc_account_id = None
        recalc_owner_uid = None

        if account_id:
            existing = account_collection.find_one({'uuid': account_id})
            if not existing:
                return jsonify({'success': False, 'message': '수정할 계좌를 찾을 수 없습니다.'}), 404
            if not is_adm and _str_user_id(existing.get('user_id')) != _str_user_id(session_uid):
                return jsonify({'success': False, 'message': '계좌 수정 권한이 없습니다. 소유자 또는 관리자만 수정 가능합니다.'}), 403

            set_doc = {
                'account_name': data.get('account_name'),
                'account_number': data.get('account_number'),
                'owner': data.get('owner'),
                'description': data.get('description', ''),
            }
            if 'tags' in data:
                set_doc['tags'] = _normalize_tags(data.get('tags'))
            if is_adm:
                if data.get('user_id') is not None and str(data.get('user_id')).strip():
                    set_doc['user_id'] = str(data.get('user_id')).strip()
                if 'shared_user_ids' in data:
                    owner_uid = set_doc.get('user_id', existing.get('user_id'))
                    shared = _normalize_shared_user_ids(data.get('shared_user_ids'))
                    if owner_uid and str(owner_uid) in shared:
                        shared = [x for x in shared if x != str(owner_uid)]
                    set_doc['shared_user_ids'] = shared
                if 'is_public' in data:
                    set_doc['is_public'] = bool(data.get('is_public'))

            result = account_collection.update_one({'uuid': account_id}, {'$set': set_doc})
            if result.matched_count == 0:
                return jsonify({'success': False, 'message': '수정할 계좌를 찾을 수 없습니다.'}), 404
            message = f"계좌({set_doc['account_name']}) 정보가 수정되었습니다."
            recalc_account_id = account_id
            recalc_owner_uid = set_doc.get('user_id', existing.get('user_id'))
        else:
            owner_uid = str(data.get('user_id')).strip() if is_adm and data.get('user_id') else session_uid
            shared = _normalize_shared_user_ids(data.get('shared_user_ids')) if is_adm else []
            if owner_uid and str(owner_uid) in shared:
                shared = [x for x in shared if x != str(owner_uid)]
            account_data = {
                'account_name': data.get('account_name'),
                'account_number': data.get('account_number'),
                'owner': data.get('owner'),
                'description': data.get('description', ''),
                'tags': _normalize_tags(data.get('tags')),
                'user_id': owner_uid,
                'shared_user_ids': shared,
                'is_public': bool(data.get('is_public')) if is_adm else False,
                'uuid': str(uuid.uuid4()),
            }
            account_collection.insert_one(account_data)
            message = f"계좌({account_data['account_name']}) 정보가 추가되었습니다."
            recalc_account_id = account_data.get('uuid')
            recalc_owner_uid = account_data.get('user_id')

        # 계좌 저장 직후 balance latest/history도 즉시 동기화.
        try:
            if recalc_account_id:
                # 계좌 저장 자체를 리밸런싱으로 보지 않는다.
                _recalc_and_save_balance(recalc_account_id, recalc_owner_uid, is_rebalanced=False)
        except Exception as e:
            logging.error(f"계좌 저장 후 잔고 재계산 실패: {e}", exc_info=True)
            return jsonify({'success': False, 'message': '계좌 저장은 완료되었지만, 잔고 재계산 중 오류가 발생했습니다.'}), 500

        return jsonify({'success': True, 'message': message})
    except Exception as e:
        logging.error(f"계좌 저장 중 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/accounts/<account_id>', methods=['GET'])
@login_required
def get_account(account_id):
    """계좌 상세 정보: 소유자 또는 관리자만 조회 가능."""
    acc = account_collection.find_one({'uuid': account_id})
    if not acc:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    uid = session.get('user_id')
    is_adm = _session_is_admin()

    # 소유자 본인 또는 관리자만 접근 허용 (공유 사용자는 제외)
    if not is_adm and _str_user_id(acc.get('user_id')) != _str_user_id(uid):
        return jsonify({'error': '계좌 소유자 또는 관리자만 접근 가능합니다.'}), 403

    return jsonify(_serialize_account_with_owner_labels(acc))


@bp.route('/accounts/<account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    """계좌 삭제 (연관된 트랜잭션 및 잔고 포함). 소유자 또는 관리자만."""
    session_uid = session.get('user_id')
    is_adm = _session_is_admin()
    account = account_collection.find_one({'uuid': account_id})
    if not account:
        return jsonify({'success': False, 'message': '계좌를 찾을 수 없습니다.'}), 404
    if not is_adm and account.get('user_id') != session_uid:
        return jsonify({'success': False, 'message': '삭제는 계좌 소유자 또는 관리자만 할 수 있습니다.'}), 403

    try:
        # 1. 계좌 삭제
        account_collection.delete_one({'uuid': account_id})
        # 2. 연관된 트랜잭션 삭제
        transaction_collection.delete_many({'account_id': account_id})
        # 3. 연관된 잔고 정보 삭제
        balance_collection.delete_many({'account_id': account_id})
        
        return jsonify({'success': True, 'message': f"계좌({account.get('account_name')}) 및 모든 연관 데이터가 삭제되었습니다."})
    except Exception as e:
        logging.error(f"계좌 삭제 중 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/transactions', methods=['GET'])
@login_required
def list_transactions():
    """계좌별 입출금 내역 (사용자 확인 포함)"""
    account_id = request.args.get('account_id')
    if not account_id:
        return jsonify([])

    account = _find_account_for_session(account_id)
    if not account:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    is_adm = _session_is_admin()
    uid = session.get('user_id')
    if not is_adm and _str_user_id(account.get('user_id')) != _str_user_id(uid):
        return jsonify({'error': '거래 내역 조회 권한이 없습니다. 소유자 또는 관리자만 조회 가능합니다.'}), 403

    limit = int(request.args.get('limit', 0))
    offset = int(request.args.get('offset', 0))

    query = {'account_id': account_id}
    cursor = transaction_collection.find(query).sort([('date', -1), ('_id', -1)])
    
    if offset > 0:
        cursor = cursor.skip(offset)
    if limit > 0:
        cursor = cursor.limit(limit)

    return jsonify([_serialize_transaction(t) for t in cursor])


@bp.route('/transactions', methods=['POST'])
@login_required
def save_transaction():
    """입출금 내역 저장 (사용자 확인 포함)"""
    data = request.get_json(silent=True) or {}
    account_id = data.get('account_id')

    account = _find_account_for_session(account_id)
    if not account:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    is_adm = _session_is_admin()
    uid = session.get('user_id')
    if not is_adm and _str_user_id(account.get('user_id')) != _str_user_id(uid):
        return jsonify({'error': '거래 내역 저장 권한이 없습니다. 소유자 또는 관리자만 저장 가능합니다.'}), 403

    transaction_id = data.get('transaction_id') or data.get('id') or request.form.get('transaction_id')
    payload = {
        'account_id': account_id,
        'date': data.get('date') or request.form.get('date'),
        'type': data.get('type') or request.form.get('type'),
        'amount': int(data.get('amount') or request.form.get('amount') or 0),
        'description': data.get('description') or request.form.get('description') or '',
        'source': data.get('source') or request.form.get('source') or 'principal',
    }
    try:
        if transaction_id:
            transaction_collection.update_one({'_id': ObjectId(transaction_id)}, {'$set': payload})
            try:
                _recalc_and_save_balance(account_id, account.get('user_id'))
            except Exception as e:
                logging.error(f"거래 수정 후 잔고 재계산 실패: {e}", exc_info=True)
                return jsonify({'success': False, 'message': '거래 저장은 완료되었지만, 잔고 재계산 중 오류가 발생했습니다.'}), 500
            return jsonify({'success': True, 'message': '거래 내역이 수정되었습니다.'})
        transaction_collection.insert_one(payload)
        try:
            _recalc_and_save_balance(account_id, account.get('user_id'))
        except Exception as e:
            logging.error(f"거래 추가 후 잔고 재계산 실패: {e}", exc_info=True)
            return jsonify({'success': False, 'message': '거래 저장은 완료되었지만, 잔고 재계산 중 오류가 발생했습니다.'}), 500
        return jsonify({'success': True, 'message': '거래 내역이 추가되었습니다.'})
    except Exception as e:
        logging.error(f"트랜잭션 저장 중 오류: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/transactions/<transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """거래 내역 삭제 (사용자 확인 포함)"""
    transaction = transaction_collection.find_one({'_id': ObjectId(transaction_id)})
    if not transaction:
        return jsonify({'error': '거래 내역을 찾을 수 없습니다.'}), 404

    account = _find_account_for_session(transaction['account_id'])
    if not account:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    is_adm = _session_is_admin()
    uid = session.get('user_id')
    if not is_adm and _str_user_id(account.get('user_id')) != _str_user_id(uid):
        return jsonify({'error': '거래 내역 삭제 권한이 없습니다. 소유자 또는 관리자만 삭제 가능합니다.'}), 403

    transaction_collection.delete_one({'_id': ObjectId(transaction_id)})
    try:
        _recalc_and_save_balance(transaction['account_id'], account.get('user_id'))
    except Exception as e:
        logging.error(f"거래 삭제 후 잔고 재계산 실패: {e}", exc_info=True)
        return jsonify({'success': False, 'message': '거래 삭제는 완료되었지만, 잔고 재계산 중 오류가 발생했습니다.'}), 500
    return jsonify({'success': True, 'message': '거래 내역이 삭제되었습니다.'})


@bp.route('/balances', methods=['GET'])
def list_balances():
    """계좌 잔고 목록 (소유·공유·관리자 전체)"""
    accounts = list(_accounts_cursor_for_session())
    return jsonify([_serialize_account(a) for a in accounts])


def _get_price_threshold():
    """DB에서 현재가 갱신 주기(분) 조회."""
    from backend.services import settings_collection
    default_threshold = max(1, config_loader.get_int(_config, 'performance', 'price_refresh_threshold_minutes', 10))

    def _load():
        doc = settings_collection.find_one({'_id': 'price_settings'})
        return int(doc.get('refresh_threshold_minutes', default_threshold)) if doc else default_threshold

    return query_cache.get_or_load(
        key=('settings', 'price_threshold'),
        ttl_seconds=_QUERY_CACHE_TTL_SEC,
        loader=_load,
        wait_timeout=_QUERY_CACHE_WAIT_SEC,
    )


def _get_force_refresh_cooldown_sec():
    """사용자 강제 갱신(버튼) 최소 간격(초). DB 설정 우선, 없으면 config.ini."""
    from backend.services import settings_collection

    def _load():
        doc = settings_collection.find_one({'_id': 'price_settings'})
        if doc and doc.get('force_refresh_cooldown_sec') is not None:
            return max(5, int(doc['force_refresh_cooldown_sec']))
        return _FORCE_REFRESH_COOLDOWN_DEFAULT_SEC

    return query_cache.get_or_load(
        key=('settings', 'force_refresh_cooldown_sec'),
        ttl_seconds=_QUERY_CACHE_TTL_SEC,
        loader=_load,
        wait_timeout=_QUERY_CACHE_WAIT_SEC,
    )


def _get_ticker_name_map_cached(tickers):
    tickers = sorted(set(tickers))
    if not tickers:
        return {}

    def _load():
        t_docs = ticker_collection.find({'ticker': {'$in': list(tickers)}}, {'ticker': 1, 'name': 1})
        return {t['ticker']: t.get('name', t['ticker']) for t in t_docs}

    return query_cache.get_or_load(
        key=('ticker_name_map', tuple(tickers)),
        ttl_seconds=_QUERY_CACHE_TTL_SEC,
        loader=_load,
        wait_timeout=_QUERY_CACHE_WAIT_SEC,
    )


def _get_ticker_price_doc_map_cached(tickers):
    tickers = sorted(set(tickers))
    if not tickers:
        return {}

    def _load():
        t_docs = ticker_collection.find(
            {'ticker': {'$in': list(tickers)}},
            {
                '_id': 0,
                'ticker': 1,
                'name': 1,
                'current_price': 1,
                'price_updated_at': 1,
                'prev_day_change': 1,
                'prev_day_change_pct': 1,
            },
        )
        return {t['ticker']: t for t in t_docs}

    return query_cache.get_or_load(
        key=('ticker_price_doc_map', 'v3', tuple(tickers)),
        ttl_seconds=_QUERY_CACHE_TTL_SEC,
        loader=_load,
        wait_timeout=_QUERY_CACHE_WAIT_SEC,
    )


def _get_ticker_asset_class_map_live(tickers):
    """자산분류는 캐시하지 않음 — 수정 직후 대시보드에 반영되도록."""
    tickers = sorted({t for t in (tickers or []) if t and t != 'CASH'})
    if not tickers:
        return {}
    docs = ticker_collection.find(
        {'ticker': {'$in': tickers}},
        {'_id': 0, 'ticker': 1, 'asset_class': 1},
    )
    out = {}
    for d in docs:
        t = d.get('ticker')
        if t is None:
            continue
        ac = d.get('asset_class')
        if isinstance(ac, Decimal128):
            try:
                ac = str(ac.to_decimal()).strip() or None
            except Exception:
                ac = None
        elif ac is not None and not isinstance(ac, str):
            ac = str(ac).strip() or None
        elif isinstance(ac, str):
            ac = ac.strip() or None
        out[t] = ac
        out[str(t).strip()] = ac
    return out


def _lookup_asset_class(asset_class_map, raw_ticker):
    if raw_ticker is None or raw_ticker == 'CASH':
        return None
    for key in (raw_ticker, str(raw_ticker).strip()):
        if key in asset_class_map:
            return asset_class_map[key]
    return None


def _final_price_entry_from_quote(ticker, q, name):
    """crawler.update_stale_prices 반환 dict와 종목명으로 재계산용 가격 엔트리 생성."""
    if isinstance(q, dict):
        return {
            'price': int(q.get('price') or 0),
            'name': name,
            'prev_day_change': q.get('prev_day_change'),
            'prev_day_change_pct': q.get('prev_day_change_pct'),
        }
    return {
        'price': int(q or 0),
        'name': name,
        'prev_day_change': None,
        'prev_day_change_pct': None,
    }


def _bulk_get_portfolio_names(portfolio_ids_list):
    """여러 portfolio_id에 대해 name 맵을 한 번에 조회."""
    unique_ids = set()
    for pid in portfolio_ids_list:
        if pid:
            try:
                unique_ids.add(ObjectId(pid))
            except Exception:
                pass
    if not unique_ids:
        return {}
    
    ports = portfolio_collection.find({'_id': {'$in': list(unique_ids)}}, {'name': 1})
    return {str(p['_id']): p.get('name') for p in ports}


def _collect_unique_tickers_from_balances(balances):
    tickers = set()
    portfolio_ids = set()
    for b in balances:
        for h in b.get('holdings', []):
            t = h.get('ticker')
            if t:
                tickers.add(t)
        lp_id = b.get('linked_portfolio')
        if lp_id:
            portfolio_ids.add(str(lp_id))

    if portfolio_ids:
        oid_map = {}
        for pid in portfolio_ids:
            try:
                oid_map[pid] = ObjectId(pid)
            except Exception:
                continue
        if oid_map:
            ports = portfolio_collection.find(
                {'_id': {'$in': list(oid_map.values())}},
                {'items.ticker': 1}
            )
            for port in ports:
                for item in port.get('items', []):
                    t = item.get('ticker')
                    if t:
                        tickers.add(t)

    tickers.discard('CASH')
    return tickers


def _accounts_allowed_for_refresh(account_ids, force=False):
    """
    이번에 백그라운드 갱신을 허용할 계좌 ID만 반환하고, 해당 계좌의 다음 허용 시각을 갱신합니다.
    - 자동 갱신(force=False): background_refresh_cooldown_sec
    - 강제 갱신(force=True): force_refresh_cooldown_sec (DB 또는 config)
    """
    account_ids = [a for a in account_ids if a]
    if not account_ids:
        return []

    now_ts = time.time()
    with _NEXT_ALLOWED_REFRESH_LOCK:
        if force:
            cooldown = float(_get_force_refresh_cooldown_sec())
            allowed_ids = []
            for aid in account_ids:
                next_ts = _NEXT_ALLOWED_FORCE_REFRESH.get(aid, 0)
                if now_ts >= next_ts:
                    allowed_ids.append(aid)
            if not allowed_ids:
                return []
            new_next_ts = now_ts + cooldown
            for aid in allowed_ids:
                _NEXT_ALLOWED_FORCE_REFRESH[aid] = new_next_ts
            return allowed_ids

        allowed_ids = []
        for aid in account_ids:
            next_ts = _NEXT_ALLOWED_REFRESH.get(aid, 0)
            if now_ts >= next_ts:
                allowed_ids.append(aid)
        if not allowed_ids:
            return []
        new_next_ts = now_ts + _BACKGROUND_REFRESH_COOLDOWN_SEC
        for aid in allowed_ids:
            _NEXT_ALLOWED_REFRESH[aid] = new_next_ts
        return allowed_ids


def _trigger_background_refresh(app, accounts, force=False):
    """
    지정된 계좌들의 현재가를 백그라운드에서 갱신하고 balance를 재계산합니다.
    None 이면 백그라운드 작업이 큐에 들어갔고, 그 외는 문자열 이유(cooldown, busy, noop).
    """
    raw_ids = [a.get('uuid') for a in accounts if a.get('uuid')]
    if not raw_ids:
        return 'noop'

    if not _BACKGROUND_REFRESH_SEMAPHORE.acquire(blocking=False):
        logging.warning(
            "Skip background refresh: queue is full (workers=%d, queue=%d).",
            _BACKGROUND_REFRESH_WORKERS,
            _BACKGROUND_REFRESH_QUEUE,
        )
        return 'busy'

    allowed_list = _accounts_allowed_for_refresh(raw_ids, force=force)
    if not allowed_list:
        logging.debug("Skip background refresh: cooldown active for requested accounts (force=%s).", force)
        _BACKGROUND_REFRESH_SEMAPHORE.release()
        return 'cooldown'

    allowed_ids = set(allowed_list)
    accounts = [a for a in accounts if a.get('uuid') in allowed_ids]
    account_ids = [a.get('uuid') for a in accounts if a.get('uuid')]
    if not account_ids:
        _BACKGROUND_REFRESH_SEMAPHORE.release()
        return 'noop'

    def _run():
        with app.app_context():
            try:
                logging.info(f"Starting background refresh for {len(accounts)} accounts. Force={force}")
                # 1. 모든 계좌의 모든 티커 수집
                balances = list(balance_collection.find({'account_id': {'$in': account_ids}}))
                logging.debug(f"Found {len(balances)} balance documents for target accounts.")
                all_tickers = _collect_unique_tickers_from_balances(balances)
                if not all_tickers:
                    logging.info("No tickers found for refresh.")
                    return

                logging.info(f"Collected {len(all_tickers)} unique tickers for price update.")

                # 2. stale한 가격들만 갱신 (force=True면 모두 갱신)
                threshold = 0 if force else _get_price_threshold()
                ticker_prices_map = crawler.update_stale_prices(ticker_collection, list(all_tickers), threshold)
                
                # 3. 계좌별 balance 재계산 및 저장
                tasks = [
                    (a['uuid'], a.get('user_id'))
                    for a in accounts
                    if a.get('uuid') and a.get('user_id')
                ]
                
                t_names = _get_ticker_name_map_cached(all_tickers)

                final_prices = {
                    t: _final_price_entry_from_quote(t, q, t_names.get(t, t))
                    for t, q in ticker_prices_map.items()
                }
                
                # _RECALC_ACCOUNT_WORKERS가 1이므로 실질적으로 순차 실행임
                logging.info(f"Triggering sequential recalculation for {len(tasks)} accounts (Worker=1).")
                _refresh_accounts_parallel_tasks(app, tasks, final_prices)
                logging.info(f"Background refresh completed successfully for {len(tasks)} accounts.")
            except Exception as e:
                logging.error(f"Background refresh thread failed: {e}", exc_info=True)

    def _run_with_release():
        try:
            _run()
        finally:
            _BACKGROUND_REFRESH_SEMAPHORE.release()

    try:
        _BACKGROUND_REFRESH_EXECUTOR.submit(_run_with_release)
        logging.debug("Background refresh task submitted.")
        return None
    except RuntimeError as e:
        _BACKGROUND_REFRESH_SEMAPHORE.release()
        logging.warning("Failed to submit background refresh task: %s", e)
        return 'busy'


@bp.route('/balances/overview', methods=['GET'])
def balances_overview():
    """메인 화면용: 각 계좌별 summary (ROI, 자산구성 등) 요약. N+1 쿼리 최적화 및 메모리 효율화."""
    accounts = list(_accounts_cursor_for_session())
    account_ids = [a['uuid'] for a in accounts if a.get('uuid')]
    if not account_ids:
        return jsonify([])

    # 1. 기초 데이터 벌크 조회
    balances = list(balance_collection.find({'account_id': {'$in': account_ids}}))
    balance_map = {b['account_id']: b for b in balances}

    today_str = now_kst().strftime('%Y-%m-%d')
    hist_today = list(
        balance_history_collection.find(
            {'account_id': {'$in': account_ids}, 'date': today_str},
            {'account_id': 1, 'prev_day_asset_change': 1, 'principal': 1}
        )
    )
    hist_change_by_aid = {h['account_id']: h.get('prev_day_asset_change') for h in hist_today}
    hist_principal_by_aid = {h['account_id']: h.get('principal') for h in hist_today}

    min_month = monthly_cutoff_key(12)
    monthly_by_aid = load_monthly_trend_series(account_monthly_trend_collection, account_ids, min_month)

    rebalanced_by_aid = _bulk_latest_rebalanced_dates(account_ids)

    # 2. 메타데이터 (티커, 포트폴리오) 벌크 조회
    all_lp_ids = [str(b['linked_portfolio']) for b in balances if b.get('linked_portfolio')]
    portfolio_name_map = _bulk_get_portfolio_names(all_lp_ids)

    overview_tickers = set()
    for b in balances:
        for h in (b.get('latest', {}) or {}).get('holdings', []):
            t = h.get('ticker')
            if t and t != 'CASH': overview_tickers.add(t)
    
    overview_tickers = sorted(list(overview_tickers))
    ticker_doc_map = _get_ticker_price_doc_map_cached(overview_tickers) if overview_tickers else {}
    ticker_asset_class_map = _get_ticker_asset_class_map_live(overview_tickers)

    # 3. 결과 조립
    results = []
    stale_accounts = []
    now = now_kst()
    threshold = pd.Timedelta(minutes=_get_price_threshold())

    for account in accounts:
        aid = account.get('uuid')
        balance_doc = balance_map.get(aid, {})
        latest = balance_doc.get('latest', {})
        
        # Stale 여부 체크 (백그라운드 갱신 트리거용)
        last_calc = ensure_kst_from_utc_naive(balance_doc.get('last_calculated_at'))
        if not latest or not last_calc or (now - last_calc) > threshold:
            stale_accounts.append(account)

        # 포트폴리오 이름
        lp_id = balance_doc.get('linked_portfolio')
        lp_name = portfolio_name_map.get(str(lp_id)) if lp_id else None

        # 전일대비 수익률 계산 (기존: 모든 트랜잭션 로드 -> 변경: 이력 데이터 활용)
        prev_day_asset_change = hist_change_by_aid.get(aid)
        # snapshot_history 에는 principal이 필수로 포함되지 않으므로 최신(latest) principal을 활용
        p_today = latest.get('principal')
        prev_day_return_vs_principal_pct = None
        if prev_day_asset_change is not None and p_today and p_today > 0:
            prev_day_return_vs_principal_pct = round((prev_day_asset_change / p_today) * 100, 2)

        # 자산분류 매핑
        _holdings_out = []
        for h in latest.get('holdings', []) or []:
            hd = dict(h)
            _t = hd.get('ticker')
            if _t and _t != 'CASH':
                hd['asset_class'] = _lookup_asset_class(ticker_asset_class_map, _t)
            _holdings_out.append(hd)

        _monthly_series = monthly_by_aid.get(aid, [])

        results.append({
            'account': _serialize_account(account),
            'principal': latest.get('principal', 0),
            'investment_return': latest.get('investment_return', 0),
            'total_asset_value': latest.get('total_asset_value', 0),
            'cash_balance': latest.get('cash_balance', 0),
            'current_stock_value': latest.get('current_stock_value', 0),
            'is_stale': (aid in [sa['uuid'] for sa in stale_accounts]),
            'portfolio_id': str(lp_id) if lp_id else None,
            'portfolio_name': lp_name,
            'prev_day_asset_change': prev_day_asset_change,
            'prev_day_return_vs_principal_pct': prev_day_return_vs_principal_pct,
            'history_months': [m for m, _ in _monthly_series],
            'history_points': [v for _, v in _monthly_series],
            'holdings': _holdings_out,
            'last_rebalanced_date': rebalanced_by_aid.get(aid),
        })

    if stale_accounts and session.get('user_id'):
        _trigger_background_refresh(current_app._get_current_object(), stale_accounts)

    return jsonify(results)


def _json_user_force_refresh_result(reason):
    """강제 갱신 API 공통 응답. reason None이면 큐 적재 성공."""
    if reason is None:
        return jsonify({
            'success': True,
            'queued': True,
            'message': '백그라운드에서 현재가를 갱신합니다.',
        })
    if reason == 'cooldown':
        return jsonify({
            'success': True,
            'queued': False,
            'reason': 'cooldown',
            'message': '강제 갱신은 쿨다운 중입니다. 잠시 후 다시 시도해 주세요.',
        })
    if reason == 'busy':
        return jsonify({
            'success': True,
            'queued': False,
            'reason': 'busy',
            'message': '서버가 갱신 작업 중입니다. 잠시 후 다시 시도해 주세요.',
        })
    return jsonify({
        'success': True,
        'queued': False,
        'reason': reason,
        'message': '갱신할 계좌가 없습니다.',
    })


@bp.route('/balances/refresh', methods=['POST'])
@bp.route('/balances/refresh-all', methods=['POST'])
@login_required
def refresh_balances_user_force():
    """
    강제 현재가 갱신(크롤 threshold 무시, threshold=0).
    JSON body 선택: { \"account_id\": \"uuid\" } — 없으면 접근 가능한 전체 계좌.
    하위 호환: /balances/refresh-all 동일 동작.
    """
    data = request.get_json(silent=True) or {}
    account_id = (data.get('account_id') or '').strip() or None
    if account_id:
        account = _find_account_for_session(account_id)
        if not account:
            return jsonify({'success': False, 'message': '계좌를 찾을 수 없습니다.'}), 404
        accounts = [account]
    else:
        accounts = list(_accounts_cursor_for_session())
    app = current_app._get_current_object()
    reason = _trigger_background_refresh(app, accounts, force=True)
    return _json_user_force_refresh_result(reason)


def run_refresh_all_balances_admin():
    """전체 사용자의 모든 계좌에 대해 즉시 갱신 (스케줄러/관리자용). 동기 방식으로 수행."""
    accounts = list(account_collection.find({}))
    app = current_app._get_current_object()

    balances = list(balance_collection.find({}))
    all_tickers = _collect_unique_tickers_from_balances(balances)
    threshold = _get_price_threshold()
    ticker_prices_map = crawler.update_stale_prices(ticker_collection, list(all_tickers), threshold)
    
    t_names = _get_ticker_name_map_cached(all_tickers)
    
    final_prices = {
        t: _final_price_entry_from_quote(t, q, t_names.get(t, t))
        for t, q in ticker_prices_map.items()
    }

    tasks = [
        (a['uuid'], a['user_id'])
        for a in accounts
        if a.get('uuid') and a.get('user_id')
    ]
    return _refresh_accounts_parallel_tasks(app, tasks, final_prices)


@bp.route('/balances/refresh-all-admin', methods=['POST'])
@admin_required
def refresh_all_balances_admin():
    """관리자: 전체 계좌 현재가 크롤링 후 balance_history 저장."""
    updated = run_refresh_all_balances_admin()
    return jsonify({'success': True, 'updated': updated, 'count': len(updated)})


def _recalc_and_save_balance(account_id, owner_user_id=None, ticker_prices=None, is_rebalanced=False):
    """계좌 1개에 대해 현재가 반영 재계산 후 latest·balance_history(오늘) 저장."""
    account = account_collection.find_one({'uuid': account_id})
    if not account:
        raise ValueError('계좌를 찾을 수 없습니다.')
    if owner_user_id is not None and account.get('user_id') != owner_user_id:
        raise ValueError('계좌 소유자 정보가 일치하지 않습니다.')

    balance_data = balance_collection.find_one({'account_id': account_id}, {'_id': 0}) or {}
    current_holdings = balance_data.get('holdings', [])
    linked_portfolio_id = balance_data.get('linked_portfolio')

    transactions = list(transaction_collection.find({'account_id': account_id}))
    principal = sum(
        t['amount'] if t['type'] == 'deposit'
        else (-t['amount'] if (t['type'] == 'withdraw' and t.get('source') != 'profit') else 0)
        for t in transactions
    )

    target_portfolio = None
    relevant_tickers = set(h['ticker'] for h in current_holdings)
    if linked_portfolio_id:
        try:
            target_portfolio = portfolio_collection.find_one({'_id': ObjectId(linked_portfolio_id)})
        except Exception:
            target_portfolio = None
        if target_portfolio:
            for item in target_portfolio['items']:
                relevant_tickers.add(item['ticker'])

    relevant_tickers.discard('CASH')
    
    final_ticker_prices = {}
    if ticker_prices:
        for t in list(relevant_tickers):
            if t in ticker_prices:
                entry = dict(ticker_prices[t])
                if 'prev_day_change' not in entry:
                    entry['prev_day_change'] = None
                if 'prev_day_change_pct' not in entry:
                    entry['prev_day_change_pct'] = None
                final_ticker_prices[t] = entry

    needed_tickers = [t for t in relevant_tickers if t not in final_ticker_prices]
    if needed_tickers:
        db_prices_map = _get_ticker_price_doc_map_cached(needed_tickers)

        threshold = _get_price_threshold()
        # 필요한 티커들에 대해 stale 여부 체크 및 갱신
        updated_map = crawler.update_stale_prices(ticker_collection, needed_tickers, threshold)

        for t in needed_tickers:
            q = updated_map.get(t, {})
            name = db_prices_map.get(t, {}).get('name', t)
            final_ticker_prices[t] = _final_price_entry_from_quote(t, q, name)
    
    ticker_prices = final_ticker_prices

    total_purchase_amount = 0
    current_stock_value = 0
    for h in current_holdings:
        ticker = h['ticker']
        qty = int(h.get('quantity', 0))
        avg_price = int(h.get('avg_purchase_price', 0))
        info = ticker_prices.get(
            ticker,
            {
                'price': 1 if ticker == 'CASH' else 0,
                'name': '현금' if ticker == 'CASH' else ticker,
                'prev_day_change': None,
                'prev_day_change_pct': None,
            },
        )
        current_price = info['price']
        evaluation_value = qty * current_price
        if ticker != 'CASH':
            total_purchase_amount += qty * avg_price
            current_stock_value += evaluation_value

    manual_cash = balance_data.get('cash', 0)
    diff = principal - total_purchase_amount
    calculated_cash_balance = diff if diff > 0 else 0
    cash_balance = manual_cash if 'cash' in balance_data else calculated_cash_balance
    total_asset_value = current_stock_value + cash_balance
    investment_return = total_asset_value - principal

    # 3. Resolve weights and calculate rebalancing
    # Get portfolio ratios if linked
    portfolio_ratios = {}
    if linked_portfolio_id:
        try:
            port = portfolio_collection.find_one({'_id': ObjectId(linked_portfolio_id)})
            if port:
                for item in port.get('items', []):
                    portfolio_ratios[item['ticker']] = float(item['ratio']) / 100.0
        except Exception as e:
            logging.error(f"Error loading portfolio {linked_portfolio_id}: {e}")

    # Combine tickers from holdings (current tracking list)
    # We do NOT automatically add all tickers from portfolio anymore
    # to avoid deleted items reappearing.
    # Keep user-customized order instead of using a set.
    ordered_tickers = []
    seen_tickers = set()
    for holding in current_holdings:
        ticker = holding.get('ticker')
        if not ticker or ticker == 'CASH' or ticker in seen_tickers:
            continue
        seen_tickers.add(ticker)
        ordered_tickers.append(ticker)

    holdings_list = []
    for ticker in ordered_tickers:
        # Find existing holding if any
        h = next((x for x in current_holdings if x['ticker'] == ticker), None)
        
        qty = int(h.get('quantity', 0)) if h else 0
        avg_price = int(h.get('avg_purchase_price', 0)) if h else 0
        
        info = ticker_prices.get(
            ticker,
            {'price': 0, 'name': ticker, 'prev_day_change': None, 'prev_day_change_pct': None},
        )
        current_price = info['price']
        
        evaluation_value = qty * current_price
        purchase_amount = qty * avg_price
        profit_loss = evaluation_value - purchase_amount if purchase_amount > 0 else 0
        return_rate = (profit_loss / purchase_amount * 100) if purchase_amount > 0 else 0.0
        
        # Rebalancing calculations
        target_ratio = portfolio_ratios.get(ticker, 0.0)
        
        # If quantity is 0 AND not in portfolio, skip entirely
        # (This handles the case where user manually deleted a ticker)
        if qty == 0 and target_ratio == 0:
            continue
            
        target_value = total_asset_value * target_ratio
        
        if current_price > 0:
            target_qty = int(target_value / current_price)
            diff_qty = target_qty - qty
            diff_amount = diff_qty * current_price
            
            if diff_qty > 0:
                action = 'buy'
            elif diff_qty < 0:
                action = 'sell'
            else:
                action = 'hold'
        else:
            target_qty = 0
            diff_qty = 0
            diff_amount = 0
            action = 'hold' if target_ratio == 0 else '-'

        holdings_list.append({
            'ticker': ticker,
            'name': info['name'],
            'quantity': qty,
            'price': current_price,
            'prev_day_change': info.get('prev_day_change'),
            'prev_day_change_pct': info.get('prev_day_change_pct'),
            'value': evaluation_value,
            'avg_purchase_price': avg_price,
            'profit_loss': profit_loss,
            'return_rate': return_rate,
            'current_ratio': evaluation_value / total_asset_value if total_asset_value > 0 else 0,
            'target_ratio': target_ratio,
            'target_qty': target_qty,
            'action': action,
            'diff_qty': abs(diff_qty),
            'diff_amount': abs(diff_amount),
        })

    now = now_kst()
    latest_snapshot = {
        'timestamp': now,
        'total_asset_value': total_asset_value,
        'principal': principal,
        'cash_balance': cash_balance,
        'investment_return': investment_return,
        'current_stock_value': current_stock_value,
        'holdings': holdings_list,
        'linked_portfolio': linked_portfolio_id,
        'is_rebalanced': is_rebalanced
    }
    balance_collection.update_one(
        {'account_id': account_id},
        {'$set': {'latest': latest_snapshot, 'last_calculated_at': now}},
        upsert=True
    )
    today_str = now.strftime('%Y-%m-%d')
    snapshot_for_history = {k: v for k, v in latest_snapshot.items() if k != 'principal'}
    
    # 만약 오늘자 문서가 이미 있고, 이미 is_rebalanced=True 라면 이를 유지하도록 함.
    if not is_rebalanced:
        existing_today = balance_history_collection.find_one({'account_id': account_id, 'date': today_str}, {'is_rebalanced': 1})
        if existing_today and existing_today.get('is_rebalanced'):
            snapshot_for_history['is_rebalanced'] = True

    # 전일대비 자산변동금액: 동일 계좌에서 날짜가 오늘 미만인 스냅샷 중 가장 최근 총자산과의 차이
    prev_rows = list(
        balance_history_collection.find(
            {'account_id': account_id, 'date': {'$lt': today_str}},
            {'_id': 0, 'total_asset_value': 1},
        )
        .sort('date', -1)
        .limit(1)
    )
    unset_hist = {'principal': ''}
    if prev_rows:
        try:
            prev_total = int(prev_rows[0].get('total_asset_value') or 0)
        except (TypeError, ValueError):
            prev_total = int(float(prev_rows[0].get('total_asset_value') or 0))
        snapshot_for_history['prev_day_asset_change'] = int(total_asset_value) - prev_total
    else:
        unset_hist['prev_day_asset_change'] = ''

    balance_history_collection.update_one(
        {'account_id': account_id, 'date': today_str},
        {'$set': snapshot_for_history, '$unset': unset_hist},
        upsert=True
    )
    upsert_monthly_trend_row(
        account_monthly_trend_collection,
        account_id,
        today_str,
        investment_return,
    )


def _recalc_with_app_context(app, account_id, user_id, ticker_prices=None, is_rebalanced=False):
    with app.app_context():
        _recalc_and_save_balance(account_id, user_id, ticker_prices, is_rebalanced=is_rebalanced)


def _refresh_accounts_parallel_tasks(app, tasks, ticker_prices=None):
    """tasks: [(account_id, user_id), ...]"""
    if not tasks:
        return []
    
    # 인터프리터 종료 중인지 확인
    if not threading.main_thread().is_alive():
        logging.debug("Main thread is dead, skipping parallel tasks.")
        return []

    updated = []
    n = len(tasks)
    workers = min(_RECALC_ACCOUNT_WORKERS, n)
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_map = {}
            for aid, uid in tasks:
                try:
                    fut = ex.submit(_recalc_with_app_context, app, aid, uid, ticker_prices)
                    future_map[fut] = aid
                except RuntimeError:
                    logging.warning("Cannot schedule recalculation: interpreter is shutting down.")
                    break
            
            for fut in as_completed(future_map):
                aid = future_map[fut]
                try:
                    fut.result()
                    updated.append(aid)
                except Exception as e:
                    logging.error(f"refresh account {aid}: {e}", exc_info=True)
    except RuntimeError:
        logging.warning("ThreadPoolExecutor failed: interpreter is shutting down.")
    
    return updated


@bp.route('/balances/detail', methods=['GET'])
def balance_detail():
    """계좌 상세: 잔고, 포트폴리오, 리밸런싱 정보. 캐시 정보를 먼저 반환."""
    account_id = request.args.get('account_id')
    if not account_id:
        return jsonify({'error': 'account_id required'}), 400

    account = _find_account_for_session(account_id)
    if not account:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    balance_data = balance_collection.find_one({'account_id': account_id}, {'_id': 0}) or {}
    latest = balance_data.get('latest', {})
    
    # 캐시된 정보가 있으면 즉시 반환하고 백그라운드 갱신 트리거
    # ( balances_overview와 동일한 stale 체크 로직 )
    now = now_kst()
    threshold = pd.Timedelta(minutes=_get_price_threshold())
    last_calc = balance_data.get('last_calculated_at')

    normalized_last_calc = ensure_kst_from_utc_naive(last_calc)
    if (not latest or not normalized_last_calc or (now - normalized_last_calc) > threshold) and session.get('user_id'):
        app = current_app._get_current_object()
        _trigger_background_refresh(app, [account])

    transactions = list(transaction_collection.find({'account_id': account_id}).sort('date', 1))

    principal = latest.get('principal', 0)
    if not latest and account_id:
        principal = sum(
            t['amount'] if t['type'] == 'deposit'
            else (-t['amount'] if (t['type'] == 'withdraw' and t.get('source') != 'profit') else 0)
            for t in transactions
        )

    is_admin = _session_is_admin()
    user_id = session.get('user_id')
    user_level = session.get('level', 1)
    
    if is_admin:
        query = {}
    else:
        query = {"$or": [
            {"is_public": True, "level": {"$lte": user_level}},
            {"user_id": user_id}
        ]}
    portfolios = [_serialize_portfolio(p) for p in portfolio_collection.find(query)]

    # 현재 표시되는 보유 종목 기준으로 "가장 오래된 현재가 업데이트 시각" 계산
    holding_tickers = [
        h.get('ticker')
        for h in latest.get('holdings', [])
        if h.get('ticker') and h.get('ticker') != 'CASH'
    ]
    oldest_price_updated_at = None
    oldest_price_age_minutes = None
    if holding_tickers:
        ticker_doc_map = _get_ticker_price_doc_map_cached(holding_tickers)
        for ticker in holding_tickers:
            updated_at = ensure_kst_from_utc_naive((ticker_doc_map.get(ticker) or {}).get('price_updated_at'))
            if not updated_at:
                continue
            if oldest_price_updated_at is None or updated_at < oldest_price_updated_at:
                oldest_price_updated_at = updated_at
        if oldest_price_updated_at is not None:
            delta_seconds = max(0, (now - oldest_price_updated_at).total_seconds())
            oldest_price_age_minutes = int(delta_seconds // 60)

    ticker_asset_class_map = _get_ticker_asset_class_map_live(holding_tickers) if holding_tickers else {}
    holdings_with_asset_class = []
    for h in latest.get('holdings', []) or []:
        hd = dict(h)
        _t = hd.get('ticker')
        if _t and _t != 'CASH':
            hd['asset_class'] = _lookup_asset_class(ticker_asset_class_map, _t)
        holdings_with_asset_class.append(hd)

    today_str = now.strftime('%Y-%m-%d')
    prev_day_asset_change, prev_day_return_vs_principal_pct = _prev_day_metrics_from_history_today(
        account_id, today_str, transactions
    )

    res_dict = {
        'account': _serialize_account(account),
        'principal': principal,
        'cash_balance': latest.get('cash_balance', 0),
        'current_stock_value': latest.get('current_stock_value', 0),
        'total_asset_value': latest.get('total_asset_value', 0),
        'investment_return': latest.get('investment_return', 0),
        'holdings': holdings_with_asset_class,
        'is_rebalanced': latest.get('is_rebalanced', False),
        'last_rebalanced_date': None,
        'linked_portfolio': latest.get('linked_portfolio'),
    }
    
    # balance_history 기준 마지막 리밸런싱 날짜
    res_dict['last_rebalanced_date'] = _latest_rebalanced_history_date(account_id)

    res_dict.update({
        'linked_portfolio': latest.get('linked_portfolio'),
        'portfolios': portfolios,
        'manual_cash_enabled': 'cash' in balance_data,
        'is_stale': bool(not latest or not normalized_last_calc or (now - normalized_last_calc) > threshold),
        'oldest_price_updated_at': oldest_price_updated_at.isoformat() if oldest_price_updated_at else None,
        'oldest_price_age_minutes': oldest_price_age_minutes,
        'prev_day_asset_change': prev_day_asset_change,
        'prev_day_return_vs_principal_pct': prev_day_return_vs_principal_pct,
    })
    return jsonify(res_dict)


def _safe_int_change(raw):
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None


def _prev_day_metrics_from_history_today(account_id, today_str, transactions_sorted):
    """
    오늘자 balance_history 문서의 prev_day_asset_change(그대로)와,
    /balances/history 와 동일하게 해당 일자 원금(_principal_at_date) 대비 변동률(%).
    """
    hist = balance_history_collection.find_one(
        {'account_id': account_id, 'date': today_str},
        {'prev_day_asset_change': 1},
    )
    if not hist:
        return None, None
    change = _safe_int_change(hist.get('prev_day_asset_change'))
    if change is None:
        return None, None
    p = _principal_at_date(transactions_sorted, today_str)
    pct = round((change / p) * 100, 2) if p and p > 0 else None
    return change, pct


def _latest_rebalanced_history_date(account_id):
    """
    balance_history 기준 최신 리밸런싱 일자를 반환.
    - is_rebalanced=True 문서만 대상
    - date 내림차순, 동일 date는 _id 내림차순으로 최신 문서 우선
    """
    doc = balance_history_collection.find_one(
        {
            'account_id': account_id,
            'is_rebalanced': True,
            'date': {'$exists': True, '$ne': None},
        },
        {'date': 1},
        sort=[('date', -1), ('_id', -1)],
    )
    if not doc:
        return None
    d = doc.get('date')
    if d is None:
        return None
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m-%d')
    return str(d)[:10]


def _bulk_latest_rebalanced_dates(account_ids):
    """
    여러 계좌의 최신 리밸런싱(is_rebalanced=True) 일자를 한 번의 집계 쿼리로 조회.
    _latest_rebalanced_history_date와 동일한 정렬 기준(date desc, _id desc)을 계좌별로 적용.
    """
    if not account_ids:
        return {}
    pipeline = [
        {'$match': {
            'account_id': {'$in': account_ids},
            'is_rebalanced': True,
            'date': {'$exists': True, '$ne': None},
        }},
        {'$sort': {'date': -1, '_id': -1}},
        {'$group': {'_id': '$account_id', 'date': {'$first': '$date'}}},
    ]
    out = {}
    for row in balance_history_collection.aggregate(pipeline):
        d = row.get('date')
        if d is None:
            continue
        out[row['_id']] = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)[:10]
    return out


def _principal_at_date(transactions_sorted_by_date, up_to_date_str):
    total = 0
    for t in transactions_sorted_by_date:
        t_date = t.get('date')
        if t_date is None:
            continue
        t_date_str = t_date.strftime('%Y-%m-%d') if hasattr(t_date, 'strftime') else str(t_date)[:10]
        if t_date_str > up_to_date_str:
            break
        if t['type'] == 'deposit':
            total += t.get('amount', 0)
        elif t['type'] == 'withdraw':
            if t.get('source') != 'profit':
                total -= t.get('amount', 0)
    return total


def _balance_history_doc_to_jsonable(obj):
    """balance_history Mongo 문서를 JSON 응답용으로 직렬화."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {k: _balance_history_doc_to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_balance_history_doc_to_jsonable(v) for v in obj]
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal128):
        try:
            return float(obj.to_decimal())
        except Exception:
            return str(obj)
    return str(obj)


@bp.route('/balances/history/raw', methods=['GET'])
@admin_required
def balance_history_raw():
    """특정 일자 balance_history 문서(들) 원시 필드 — JSON."""
    account_id = request.args.get('account_id')
    date_str = request.args.get('date')
    if not account_id or not date_str:
        return jsonify({'error': 'account_id and date (YYYY-MM-DD) are required'}), 400

    account = account_collection.find_one({'uuid': account_id})
    if not account:
        return jsonify({'error': 'Account not found'}), 404

    docs = list(
        balance_history_collection.find({'account_id': account_id, 'date': date_str}).sort('_id', 1)
    )
    if not docs:
        return jsonify({'error': '해당 날짜의 스냅샷이 없습니다.'}), 404

    if len(docs) == 1:
        return jsonify(_balance_history_doc_to_jsonable(docs[0]))

    return jsonify({
        '_multiple_documents': True,
        '_count': len(docs),
        'documents': [_balance_history_doc_to_jsonable(d) for d in docs],
    })


@bp.route('/balances/history', methods=['GET'])
def balance_history():
    account_id = request.args.get('account_id')
    if not account_id:
        return jsonify({'error': 'account_id is required'}), 400

    account = account_collection.find_one({'uuid': account_id})
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    if not _session_is_admin() and not _user_can_access_account(account, session.get('user_id')):
        return jsonify({'error': 'Unauthorized'}), 403

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = {'account_id': account_id}
    if request.args.get('rebalanced_only') == 'true':
        query['is_rebalanced'] = True
        
    if start_date or end_date:
        query['date'] = {}
        if start_date:
            query['date']['$gte'] = start_date
        if end_date:
            query['date']['$lte'] = end_date

    history = list(balance_history_collection.find(query).sort('date', 1))
    transactions = list(transaction_collection.find({'account_id': account_id}).sort('date', 1))

    results = []
    for h in history:
        date_str = h['date']
        principal = _principal_at_date(transactions, date_str)
        investment_return = h.get('investment_return', 0)
        return_rate = (investment_return / principal * 100) if principal > 0 else 0.0
        raw_pday = h.get('prev_day_asset_change')
        pday = _safe_int_change(raw_pday) if raw_pday is not None else None
        prev_day_return_vs_principal_pct = (
            round((pday / principal) * 100, 2) if pday is not None and principal > 0 else None
        )
        results.append({
            'date': date_str,
            'total_asset_value': h.get('total_asset_value', 0),
            'principal': principal,
            'investment_return': investment_return,
            'return_rate': round(return_rate, 2),
            'prev_day_asset_change': h.get('prev_day_asset_change'),
            'prev_day_return_vs_principal_pct': prev_day_return_vs_principal_pct,
            'is_rebalanced': h.get('is_rebalanced', False),
            'holdings': h.get('holdings', [])
        })

    return jsonify(results)


@bp.route('/balances/update', methods=['POST'])
@login_required
def update_balance():
    """잔고/포트폴리오 연결/보유 종목 업데이트."""
    data = request.get_json(silent=True) or {}
    account_id = data.get('account_id')

    account = _find_account_for_session(account_id)
    if not account:
        return jsonify({'error': '계좌를 찾을 수 없습니다.'}), 404

    uid = session.get('user_id')
    is_adm = _session_is_admin()
    if not is_adm and _str_user_id(account.get('user_id')) != _str_user_id(uid):
        return jsonify({'error': '계좌 수정 권한이 없습니다. 소유자 또는 관리자만 수정 가능합니다.'}), 403

    # 기존 데이터 로드 (리밸런싱 플래그 판단용)
    balance_data = balance_collection.find_one({'account_id': account_id})
    
    linked_portfolio = data.get('linked_portfolio') or request.form.get('linked_portfolio') or ''
    if linked_portfolio:
        try:
            p = portfolio_collection.find_one({'_id': ObjectId(linked_portfolio)})
            if not p:
                return jsonify({'error': '포트폴리오를 찾을 수 없습니다.'}), 404
            
            # 권한 체크
            if not is_adm and p.get('user_id') != uid:
                if not p.get('is_public'):
                    return jsonify({'error': '포트폴리오 접근 권한이 없습니다.'}), 403
                user_level = session.get('level', 1)
                if p.get('level', 1) >= user_level:
                    return jsonify({'error': '이 포트폴리오를 사용할 수 있는 권한 레벨이 아닙니다.'}), 403
        except Exception as e:
            return jsonify({'error': '유효하지 않은 포트폴리오 ID입니다.'}), 400
    # ... (생략된 경우를 위해 아래에서 tickers 등 처리)
    
    # 기존 데이터와 비교 로직을 위해 파싱 수행
    tickers = data.get('tickers') or request.form.getlist('tickers[]') or request.form.getlist('tickers')
    quantities = data.get('quantities') or request.form.getlist('quantities[]') or request.form.getlist('quantities')
    avg_purchase_prices = data.get('avg_purchase_prices') or request.form.getlist('avg_purchase_prices[]') or request.form.getlist('avg_purchase_prices')

    holdings = []
    for t, q, p in zip(tickers, quantities, avg_purchase_prices or [0] * len(tickers)):
        if t:
            try:
                qty_val = int(q) if q else 0
                avg_p = int(str(p).replace(',', '')) if p else 0
                holdings.append({
                    'ticker': t,
                    'quantity': qty_val,
                    'avg_purchase_price': avg_p,
                })
            except (ValueError, TypeError):
                continue

    cash = data.get('cash')
    if cash is not None:
        try:
            cash = int(str(cash).replace(',', ''))
        except (ValueError, TypeError):
            cash = 0

    # 리밸런싱 판단:
    # - 이전 보유종목 대비 "수량 또는 평단(avg_purchase_price)"이 바뀐 경우만 True
    # - 단순 저장/포트폴리오 연결 변경/최초 저장은 리밸런싱으로 보지 않음
    def _normalize_holdings_map(src):
        out = {}
        for h in (src or []):
            t = str(h.get('ticker') or '').strip()
            if not t or t == 'CASH':
                continue
            try:
                qty = int(h.get('quantity') or 0)
            except (TypeError, ValueError):
                qty = 0
            try:
                avg = int(h.get('avg_purchase_price') or 0)
            except (TypeError, ValueError):
                avg = 0
            out[t] = {'quantity': qty, 'avg_purchase_price': avg}
        return out

    is_rebalanced = False
    if balance_data:
        old_holdings_map = _normalize_holdings_map(balance_data.get('holdings', []))
        new_holdings_map = _normalize_holdings_map(holdings)
        is_rebalanced = (old_holdings_map != new_holdings_map)

    has_any_stock_holding = any(
        (h.get('ticker') and h.get('ticker') != 'CASH' and int(h.get('quantity', 0)) > 0)
        for h in holdings
    )
    if not has_any_stock_holding:
        txs = list(transaction_collection.find({'account_id': account_id}))
        principal = sum(
            t['amount'] if t['type'] == 'deposit'
            else (-t['amount'] if (t['type'] == 'withdraw' and t.get('source') != 'profit') else 0)
            for t in txs
        )
        cash = principal

    update_payload = {
        'account_id': account_id,
        'linked_portfolio': linked_portfolio or None,
        'holdings': holdings
    }
    if cash is not None:
        update_payload['cash'] = cash

    balance_collection.update_one(
        {'account_id': account_id},
        {'$set': update_payload},
        upsert=True,
    )
    
    try:
        _recalc_and_save_balance(account_id, account.get('user_id'), is_rebalanced=is_rebalanced)
    except Exception as e:
        import traceback
        logging.error(f"Error recalculating balance after update: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': '잔고 설정은 저장했으나, 재계산 중 오류가 발생했습니다.'})

    return jsonify({'success': True, 'message': '잔고 및 포트폴리오 설정이 저장되었습니다.', 'is_rebalanced': is_rebalanced})
