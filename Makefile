# 주식 정보 시스템 - Front/Back 동시 실행용

.PHONY: backend frontend dev start stop

# 백엔드만 실행 (Flask API, port 5000)
backend:
	./venv/bin/python3 backend/run_backend.py

# 프론트엔드만 실행 (Vue dev server, port 5173)
frontend:
	cd frontend && npm run dev

# 프론트 + 백엔드 동시 실행 (한 번에 둘 다 띄움)
dev: start
start:
	@chmod +x scripts/start.sh 2>/dev/null || true
	./scripts/start.sh
