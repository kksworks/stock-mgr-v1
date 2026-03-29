#!/bin/sh

# config.ini가 없으면 예시 파일로 초기화
if [ ! -f /app/config.ini ]; then
  rm -rf /app/config.ini
  cp /app/config.ini.example /app/config.ini
fi

# 서버 스펙에 맞춘 리소스 제어를 위해 config.ini의 [server] 값을 우선 사용
GUNICORN_WORKERS=$(python3 - <<'PY'
import configparser
cfg = configparser.ConfigParser()
cfg.read("/app/config.ini")
print(cfg.get("server", "gunicorn_workers", fallback="1"))
PY
)

GUNICORN_THREADS=$(python3 - <<'PY'
import configparser
cfg = configparser.ConfigParser()
cfg.read("/app/config.ini")
print(cfg.get("server", "gunicorn_threads", fallback="2"))
PY
)

GUNICORN_TIMEOUT=$(python3 - <<'PY'
import configparser
cfg = configparser.ConfigParser()
cfg.read("/app/config.ini")
print(cfg.get("server", "gunicorn_timeout_sec", fallback="120"))
PY
)

exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers "${GUNICORN_WORKERS}" \
  --threads "${GUNICORN_THREADS}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --log-level "${LOG_LEVEL:-info}" \
  backend.app:app
