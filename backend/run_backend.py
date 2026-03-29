#!/usr/bin/env python3
"""프로젝트 루트에서 백엔드 API 서버 실행 (Flask).

Docker/백그라운드 기동 시 debug=True + 리로더는 자식 프로세스를 포크하고
APScheduler 등이 이중 기동될 수 있으므로 기본은 debug=False, use_reloader=False.
로컬 개발에서만: FLASK_DEBUG=1 (선택) FLASK_USE_RELOADER=1
"""
import os

if __name__ == '__main__':
    import sys
    import os
    from backend import config_loader
    # 프로젝트 루트를 sys.path에 추가 (backend/ 폴더 내부 실행 시 대응)
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root_dir not in sys.path:
        sys.path.insert(0, _root_dir)

    from backend.app import app

    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    # 리로더는 기본 끔 — 켜면 포크 + 스케줄러 중복 초기화 위험
    use_reloader = os.environ.get('FLASK_USE_RELOADER', '0').lower() in ('1', 'true', 'yes')
    cfg = config_loader.load_config()
    threaded = config_loader.get_bool(cfg, 'server', 'flask_threaded', True)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=use_reloader and debug,
        threaded=threaded,
    )
