import hashlib
import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from functools import wraps
from backend.services import user_collection, user_preferences_collection

bp = Blueprint('auth', __name__)

# 간단한 인메모리 Rate Limiting (저사양 환경용, Redis 없이 동작)
# { "ip:endpoint": [timestamp1, timestamp2, ...] }
_RATE_LIMITS = {}

def is_rate_limited(key, limit=10, window=60):
    """특정 키(IP+엔드포인트)에 대해 요청 빈도 제한 체크."""
    now = datetime.now(timezone.utc).timestamp()
    if key not in _RATE_LIMITS:
        _RATE_LIMITS[key] = [now]
        return False
    
    # 윈도우 밖의 타임스탬프 제거
    _RATE_LIMITS[key] = [t for t in _RATE_LIMITS[key] if now - t < window]
    
    if len(_RATE_LIMITS[key]) >= limit:
        return True
    
    _RATE_LIMITS[key].append(now)
    return False


def _build_public_user_payload(user_doc):
    return {
        'id': str(user_doc['_id']),
        'username': user_doc['username'],
        'email': user_doc.get('email', ''),
        'role': user_doc.get('role', 'member'),
    }


def _build_api_key_login_url(raw_api_key: str):
    base = request.host_url.rstrip('/')
    return f"{base}/api/login-with-key?api_key={raw_api_key}"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin permission required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Rate Limit: 가입 시도는 분당 5회로 제한 (봇 방지)
    if is_rate_limited(f"{request.remote_addr}:register", limit=5, window=60):
        return jsonify({'error': 'Too many registration attempts. Please wait.'}), 429

    if user_collection.find_one({'username': username}):
        return jsonify({'error': 'Username already exists'}), 400

    # First user is admin, others are members
    role = 'admin' if user_collection.count_documents({}) == 0 else 'member'

    user_data = {
        'username': username,
        'password': generate_password_hash(password),
        'email': email,
        'role': role
    }
    user_id = user_collection.insert_one(user_data).inserted_id
    
    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': {
            'id': str(user_id),
            'username': username,
            'role': role
        }
    })

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Rate Limit: 로그인 시도는 분당 10회로 제한 (무작위 대입 방지)
    if is_rate_limited(f"{request.remote_addr}:login", limit=10, window=60):
        return jsonify({'error': 'Too many login attempts. Please wait.'}), 429

    user = user_collection.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        session['role'] = user.get('role', 'member')
        return jsonify({
            'success': True,
            'user': _build_public_user_payload(user),
        })

    return jsonify({'error': 'Invalid username or password'}), 401


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})

@bp.route('/me', methods=['GET'])
def me():
    if 'user_id' in session:
        user = user_collection.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            return jsonify({
                'logged_in': True,
                'user': _build_public_user_payload(user),
            })
    return jsonify({'logged_in': False})


@bp.route('/login-with-key', methods=['GET'])
def login_with_api_key():
    """API Key 기반 자동 로그인 후 세션 생성 + 지정 경로로 리다이렉트."""
    raw_api_key = (request.args.get('api_key') or '').strip()
    next_path = (request.args.get('next') or '/').strip()
    if not raw_api_key:
        return jsonify({'error': 'api_key가 필요합니다.'}), 400

    # open redirect 방지: 내부 경로만 허용
    parsed = urlparse(next_path)
    if parsed.scheme or parsed.netloc or not next_path.startswith('/'):
        next_path = '/'

    api_key_hash = hashlib.sha256(raw_api_key.encode('utf-8')).hexdigest()
    user = user_collection.find_one({'api_key_hash': api_key_hash})
    if not user:
        return jsonify({'error': '유효하지 않은 API Key 입니다.'}), 401

    session['user_id'] = str(user['_id'])
    session['username'] = user['username']
    session['role'] = user.get('role', 'member')
    logging.info("API key login success user_id=%s username=%s", str(user['_id']), user.get('username'))
    return redirect(next_path)

@bp.route('/user/update-profile', methods=['POST'])
@login_required
def update_profile():
    """로그인한 사용자의 프로필(이메일 등)을 업데이트합니다."""
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()

    update_data = {
        'email': email
    }

    result = user_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )

    if result.matched_count == 0:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    logging.info("User updated profile user_id=%s email=%s", user_id, email)
    return jsonify({'success': True, 'message': '프로필이 업데이트되었습니다.'})

@bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = list(user_collection.find({}, {'password': 0, 'api_key_hash': 0}))
    for user in users:
        user['id'] = str(user.pop('_id'))
    return jsonify(users)


@bp.route('/users/reset-password', methods=['POST'])
@admin_required
def admin_reset_user_password():
    """관리자가 다른 사용자(또는 본인)의 비밀번호를 강제로 설정합니다."""
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    if not user_id or not new_password:
        return jsonify({'error': 'user_id와 new_password가 필요합니다.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': '비밀번호는 6자 이상이어야 합니다.'}), 400

    try:
        oid = ObjectId(user_id)
    except Exception:
        return jsonify({'error': '잘못된 user_id입니다.'}), 400

    result = user_collection.update_one(
        {'_id': oid},
        {'$set': {'password': generate_password_hash(new_password)}},
    )
    if result.matched_count == 0:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    logging.info("Admin reset password for user_id=%s", user_id)
    return jsonify({'success': True, 'message': '비밀번호가 변경되었습니다.'})


@bp.route('/user/change-password', methods=['POST'])
@login_required
def change_my_password():
    """로그인한 사용자가 본인 비밀번호를 변경합니다."""
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'current_password와 new_password가 필요합니다.'}), 400

    if len(new_password) < 6:
        return jsonify({'error': '새 비밀번호는 6자 이상이어야 합니다.'}), 400

    user = user_collection.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    if not check_password_hash(user.get('password', ''), current_password):
        return jsonify({'error': '현재 비밀번호가 올바르지 않습니다.'}), 400

    user_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'password': generate_password_hash(new_password)}},
    )
    logging.info("User changed own password user_id=%s", user_id)
    return jsonify({'success': True, 'message': '비밀번호가 변경되었습니다.'})


# ─── User Dashboard Preferences ───────────────────────────────────────────────

@bp.route('/user/preferences', methods=['GET'])
@login_required
def get_user_preferences():
    """로그인한 사용자의 대시보드 설정을 조회합니다."""
    user_id = session['user_id']
    doc = user_preferences_collection.find_one({'user_id': user_id})
    if not doc:
        return jsonify({'preferences': {}})
    # Remove MongoDB internal fields
    doc.pop('_id', None)
    doc.pop('user_id', None)
    return jsonify({'preferences': doc})


@bp.route('/user/preferences', methods=['PUT'])
@login_required
def save_user_preferences():
    """로그인한 사용자의 대시보드 설정을 저장합니다 (upsert)."""
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}

    # Only allow known preference keys to avoid arbitrary data injection
    allowed_keys = {
        'view_mode',
        'categories',
        'account_category_map',
        'show_shared',
        'hidden_account_ids',
    }
    prefs = {k: v for k, v in data.items() if k in allowed_keys}

    user_preferences_collection.update_one(
        {'user_id': user_id},
        {'$set': prefs},
        upsert=True,
    )
    logging.debug("Saved dashboard prefs for user_id=%s keys=%s", user_id, list(prefs.keys()))
    return jsonify({'success': True})


@bp.route('/user/api-key', methods=['GET'])
@login_required
def get_user_api_key_info():
    """현재 로그인 사용자의 API Key 발급 상태 조회."""
    user_id = session['user_id']
    user = user_collection.find_one({'_id': ObjectId(user_id)}, {'api_key_created_at': 1})
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    return jsonify({
        'has_api_key': bool(user.get('api_key_created_at')),
        'api_key_created_at': user.get('api_key_created_at'),
    })


@bp.route('/user/api-key', methods=['POST'])
@login_required
def issue_user_api_key():
    """현재 로그인 사용자용 API Key 신규 발급(기존 키는 무효화)."""
    user_id = session['user_id']
    raw_api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(raw_api_key.encode('utf-8')).hexdigest()
    created_at = datetime.now(timezone.utc).isoformat()

    result = user_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'api_key_hash': api_key_hash, 'api_key_created_at': created_at}},
    )
    if result.matched_count == 0:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'api_key': raw_api_key,
        'api_key_created_at': created_at,
        'login_url': _build_api_key_login_url(raw_api_key),
        'message': '새 API Key가 발급되었습니다. 이전 키는 즉시 만료됩니다.',
    })

