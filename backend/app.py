"""
Flask API 진입점.
프론트엔드(Vue)는 별도 서버에서 실행되며, 이 API를 호출합니다.
"""
import logging
from datetime import timedelta
from flask import Flask, g
from flask_cors import CORS

from backend.routes import stock_api, account_api, portfolio_api, system_api, auth_api, board_api
from backend.services import log_collection
from backend.custom_logger import MongoDBHandler
from backend import scheduler, database, runtime_state
from backend.services import log_collection, app_config
from backend import config_loader

app = Flask(__name__)
# 보안: 세션 시크릿 키 (config.ini에 없으면 기본값 사용)
app.config['SECRET_KEY'] = config_loader.get_str(app_config, 'flask', 'secret_key', 'dev_secret_key_change_me')

# 세션 만료 시간 설정: 기본 10년 (유효기간 없음과 동일한 효과)
session_lifetime_days = config_loader.get_int(app_config, 'flask', 'session_lifetime_days', 3650)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=session_lifetime_days)
# 보안 강화: 세션 쿠키 설정
# HttpOnly=True: JS에서 쿠키 접근 방지 (XSS 보호)
app.config['SESSION_COOKIE_HTTPONLY'] = True
# SameSite='Lax': CSRF 공격 방지
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# HTTPS 환경인 경우만 Secure 쿠키 사용 (개발 환경 호환성 고려)
app.config['SESSION_COOKIE_SECURE'] = config_loader.get_bool(app_config, 'flask', 'secure_cookie', False)

# CORS: Vue 개발 서버(localhost:5173, 5174)에서 API 호출 허용
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:5174', 'http://127.0.0.1:5174'], supports_credentials=True)

import os
log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
# 유효한 로그 레벨인지 확인, 아니면 INFO 기본값
_log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(level=_log_level, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')

# 백그라운드 라이브러리 로그 노이즈 감소 (CPU 및 로그 저장 오버헤드 방지)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('mongodb').setLevel(logging.WARNING)

mongo_handler = MongoDBHandler(log_collection)
mongo_handler.setFormatter(logging.Formatter('%(message)s'))

# DB 저장은 기본 WARNING 이상만 (CPU/네트워크 절약), 하지만 전체 레벨이 DEBUG면 DEBUG로 설정
_db_log_level = logging.DEBUG if log_level_str == 'DEBUG' else logging.WARNING
mongo_handler.setLevel(_db_log_level)
logging.getLogger().addHandler(mongo_handler)

# API Blueprint 등록 (prefix /api)
app.register_blueprint(stock_api.bp, url_prefix='/api')
app.register_blueprint(account_api.bp, url_prefix='/api')
app.register_blueprint(portfolio_api.bp, url_prefix='/api')
app.register_blueprint(system_api.bp, url_prefix='/api')
app.register_blueprint(auth_api.bp, url_prefix='/api')
app.register_blueprint(board_api.bp, url_prefix='/api')


@app.before_request
def _before_request_track_load():
    g._active_request_tracked = True
    runtime_state.increment_active_requests()



@app.after_request
def _after_request_track_load(response):
    if getattr(g, '_active_request_tracked', False):
        runtime_state.decrement_active_requests()
        g._active_request_tracked = False
    return response


@app.teardown_request
def _teardown_request_track_load(_exc):
    # 예외 상황에서 after_request가 생략돼도 카운터 누수를 막는다.
    if getattr(g, '_active_request_tracked', False):
        runtime_state.decrement_active_requests()
        g._active_request_tracked = False

# 주기적 계좌 현재가 크롤링 스케줄러 (설정은 DB에서 로드)
# Flask 리로더(debug=True) 사용 시 자식 프로세스에서만 기동하도록 제어
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    # 필수 데이터/설정 초기화 (기동 시 1회)
    database.ensure_indexes(app_config)
    database.ensure_default_settings(app_config)
    # 스케줄러 시작
    scheduler.init_scheduler(app)


if __name__ == '__main__':
    import os
    _port = int(os.environ.get('PORT', '5000'))
    _debug = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    _reload = os.environ.get('FLASK_USE_RELOADER', '0').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=_port, debug=_debug, use_reloader=_reload and _debug)
