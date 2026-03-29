# 주식 정보 관리 시스템 (Stock Information System)

Python Flask(API)와 Vue 3를 사용하며, MongoDB로 한국 주식 시장(KOSPI, KOSDAQ, KONEX) 및 ETF 데이터를 크롤링하고, 개인의 주식 계좌 및 포트폴리오를 관리하는 웹 애플리케이션입니다.

## 주요 기능

* **주식 데이터 크롤링**: `pykrx`로 전 종목 시세·ETF 정보를 수집해 DB에 저장
* **주식 대시보드**: 수집된 주식 정보 조회 및 사용자 정의 필드 추가
* **계좌 관리**: 증권 계좌 등록·수정
* **입출금 관리**: 계좌별 입금·출금 내역 기록
* **포트폴리오 관리**: 투자 전략(포트폴리오) 구성 및 종목별 비중 설정
* **시스템 로그**: 웹에서 애플리케이션 로그 조회

### 권한 (일반 회원 vs 관리자)

* **로그인한 모든 사용자**: 상단 **설정** 메뉴에서 **포트폴리오(조회)**, **계좌 설정**, **티커 정보** 접근 가능.
* **포트폴리오 템플릿**의 등록·수정·삭제는 **관리자만** 가능. 일반 회원은 목록·차트 조회만 하며, **계좌 상세**에서 목표 포트폴리오를 계좌에 연결하는 것은 가능.
* **계좌 (`account_datas`)**
  * **관리자**: 모든 사용자의 계좌를 조회·수정·삭제할 수 있으며, **소유자(`user_id`)**와 **함께 볼 사용자 목록(`shared_user_ids`)**을 지정할 수 있음. A·B 사용자에게 동일 계좌를 노출하려면 한 명을 소유자로 두고 다른 사용자를 `shared_user_ids`에 추가.
  * **일반 회원**: 본인이 소유한 계좌와, 관리자가 공유로 지정한 계좌를 동일하게 조회·입출금·잔고 수정 가능. **삭제**는 해당 계좌의 **소유자** 또는 **관리자**만 가능(공유만 받은 사용자는 삭제 불가).
* **데이터 관리**(크롤링), **크롤링 스케줄**, **멤버 관리**, **시스템 로그**는 **관리자 전용**.

## 기술 스택

* **Backend**: Python 3.12, Flask (REST API), MongoDB
* **Frontend**: Vue 3, Vite, Vue Router, Axios, Bootstrap 5
* **Crawling**: PyKrx (Naver Finance, KRX Data)

## 폴더 구조

```
stock-manage-flask/
├── backend/                 # Flask API (백엔드)
│   ├── app.py               # Flask 애플리케이션 정의
│   ├── routes/              # API 라우트
│   ├── database.py          # MongoDB 연동 (공통 클라이언트 사용)
│   ├── run_backend.py       # 백엔드 실행
│   ├── Dockerfile           # 백엔드 빌드
│   └── entrypoint.sh        # Docker 진입점
├── frontend/                # Vue 3 SPA (프론트엔드)
├── scripts/                 # 관리 및 유틸리티 스크립트 (신설)
│   ├── start.sh            # 로컬 통합 실행
│   ├── start-docker.sh     # Docker 통합 관리
├── docker-compose.yml      # 서비스 오케스트레이션
├── requirements.txt         # Python 의존성
├── README.md               # 프로젝트 문서
└── config.ini              # 애플리케이션 설정 (git 제외)
```

## 설치 및 실행

### 1. 설정 파일

프로젝트 루트에 `config.ini`를 두고 MongoDB 접속 정보를 넣습니다.

```bash
cp config.ini.example config.ini
# config.ini 수정: mongodb access_url, database 등
```

#### 1.1 서버 리소스 튜닝 설정 (`config.ini`)

백엔드의 CPU/메모리 사용량은 `config.ini`의 `[server]`, `[performance]` 항목으로 조절할 수 있습니다.

- `server.gunicorn_workers`, `server.gunicorn_threads`: Docker 운영 시 동시 처리량/메모리 사용량 조절
- `performance.fetch_price_max_workers`: 현재가 병렬 크롤링 워커 수
- `performance.fetch_price_inflight_ttl_sec`: 병렬 요청 시 동일 티커 중복 크롤링 방지 캐시 TTL
- `performance.fetch_price_max_batch_size`: 대량 티커 갱신 시 배치 분할 크기
- `performance.recalc_account_workers`: 계좌 재계산 병렬 워커 수
- `performance.background_refresh_workers`, `performance.background_refresh_queue`: 백그라운드 갱신 동시 실행/대기 제한
- `performance.background_refresh_cooldown_sec`: 계좌 백그라운드 갱신 재요청 최소 간격
- `performance.scheduler_max_workers`: 스케줄러 내부 작업 병렬도
- `performance.scheduler_max_active_requests`: 실시간 요청이 많으면 스케줄러 작업 자동 연기
- `performance.portfolio_refresh_min_interval_minutes`: 포트폴리오 자동 갱신 최소 주기
- `performance.mongodb_max_pool_size`: MongoDB 연결 풀 상한
- `performance.query_cache_ttl_sec`: 동일 MongoDB 조회 결과의 in-process TTL 캐시 시간

저사양 서버는 값을 낮게, 고사양 서버는 점진적으로 높이면서 모니터링하는 것을 권장합니다.

### 2. Python 가상환경(venv) 설정 (백엔드 실행 전 필수)

백엔드는 **가상환경(venv)** 안에서 실행하는 것을 권장합니다. 프로젝트 루트에서 한 번만 설정하면 됩니다.

#### 2.1 가상환경 생성

```bash
# 프로젝트 루트(stock-manage-flask)에서 실행
python -m venv venv
```

- Python 3.8 이상 필요. `python3 -m venv venv` 로 실행해도 됩니다.
- `venv` 폴더는 저장소 `.gitignore`에 포함되어 커밋되지 않습니다.

#### 2.2 가상환경 활성화

**Linux / macOS (bash, zsh):**
```bash
source venv/bin/activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

활성화되면 프롬프트 앞에 `(venv)` 가 붙습니다.
```text
(venv) user@host:~/stock-manage-flask$
```

#### 2.3 의존성 설치 (가상환경 활성화 상태에서)

```bash
pip install -r requirements.txt
```

#### 2.4 가상환경 비활성화

작업이 끝난 뒤 가상환경을 끄려면:
```bash
deactivate
```

---

**백엔드를 실행할 때는 반드시 위처럼 가상환경을 활성화한 터미널에서** `python run_backend.py` 또는 `./start.sh` / `make dev` 를 실행하세요.

### 3. 백엔드 (Flask API) 실행

가상환경을 **활성화한 상태**에서 프로젝트 루트에서:

```bash
# API 서버 실행 (포트 5000)
python backend/run_backend.py
# 또는
./venv/bin/python3 backend/run_backend.py
```

API는 `http://localhost:5000`에서 동작합니다. (예: `GET /api/tickers`, `POST /api/crawl`)

### 4. 프론트엔드 (Vue)

```bash
cd frontend
npm install
npm run dev
```

가상 스크롤/요청 타임아웃 튜닝이 필요하면:

```bash
cd frontend
cp .env.example .env
# .env에서 VITE_API_TIMEOUT_MS, VITE_VIRTUAL_* 값 조정
```

개발 서버는 **포트 5173**에서 실행되며, `/api` 요청은 Vite 프록시를 통해 `http://localhost:5000`으로 전달됩니다.  
**백엔드를 먼저 실행한 뒤** 브라우저에서 접속하세요.

- 본인 PC: `http://localhost:5173`
- 같은 네트워크 다른 기기: `http://<서버IP>:5173` (예: `http://192.168.16.242:5173`) — 포트는 **5173**입니다.

### 5. 프론트 + 백엔드 한 번에 실행

둘 다 동시에 띄우려면 **가상환경을 활성화한 뒤** 프로젝트 루트에서:

```bash
# 방법 1: 스크립트 실행
./scripts/start.sh

# 방법 2: Make 사용
make dev
# 또는
make start
```

- 백엔드: `http://localhost:5000`
- 프론트: `http://localhost:5173` (브라우저에서 접속)

종료할 때는 프론트 터미널에서 `Ctrl+C` 한 번 하면 백엔드도 함께 종료됩니다.

| Make 타깃 | 설명 |
|-----------|------|
| `make backend` | 백엔드만 실행 |
| `make frontend` | 프론트엔드만 실행 |
| `make dev` / `make start` | 프론트+백엔드 동시 실행 |

### 6. Docker 실행/배포 운영 가이드 (`scripts/start-docker.sh`)

Docker만 설치된 로컬 PC 또는 클라우드 VPS에서 동일하게 사용할 수 있도록, Docker 운영 명령을 `./scripts/start-docker.sh` 하나로 통합했습니다.

#### 6.1 사전 준비

1. **필수 도구**: Docker, Docker Compose
2. **설정 파일 준비**
   ```bash
   cp config.ini.example config.ini
   # config.ini에 MongoDB 접속 정보 입력
   ```
3. **외부 Docker 네트워크**
   - `docker-compose.yml`은 `mydocker-base-net`(external)을 사용합니다.
   - 스크립트가 네트워크를 자동 생성합니다.
   - 네트워크 이름을 바꾸려면 환경변수로 지정합니다.
     ```bash
     export DOCKER_EXTERNAL_NETWORK=my-custom-net
     ```

#### 6.2 주요 명령

```bash
./scripts/start-docker.sh install        # 최초 설치(설정 확인 + 빌드 + 백그라운드 기동)
./scripts/start-docker.sh start          # 포그라운드 실행
./scripts/start-docker.sh up             # 백그라운드 실행
./scripts/start-docker.sh stop           # 중지/정리
./scripts/start-docker.sh restart        # 재시작
./scripts/start-docker.sh build          # 이미지 빌드
./scripts/start-docker.sh logs           # 로그 follow
./scripts/start-docker.sh --no-follow logs
./scripts/start-docker.sh ps             # 상태 확인
./scripts/start-docker.sh help           # 도움말
```

#### 6.3 배포 명령(운영/VPS/CI 공용)

```bash
./scripts/start-docker.sh update         # 현재 브랜치 ff-only pull + 재빌드/재기동
./scripts/start-docker.sh deploy         # backend/frontend 강제 recreate (CI/CD 권장)
./scripts/start-docker.sh --no-git-pull deploy
./scripts/start-docker.sh --ref main deploy
```

- `--no-git-pull`: Git 동기화는 외부(예: GitHub Actions SSH step)에서 이미 처리했을 때 사용
- `--ref <branch|tag|sha>`: 특정 Git ref로 체크아웃 후 배포할 때 사용
- `--debug`: `FLASK_DEBUG=1`, `LOG_LEVEL=DEBUG`로 실행

접속 주소 (기본):
- Backend: `http://localhost:5000`
- Frontend: `http://localhost:8080`

### 7. GitHub Actions 기반 자동 배포 (PR/MR + main push)

워크플로우 파일: `.github/workflows/deploy-docker.yml`

동작 요약:
- `pull_request` (target: `main`) 이벤트 시: PR 브랜치를 서버에 반영 후 Docker 재배포
- `push` to `main` 이벤트 시: `main`을 서버에 반영 후 Docker 재배포
- `workflow_dispatch`: 수동 실행 가능
- 동일 브랜치에서 동시 배포가 발생하면 이전 실행을 취소하고 최신 실행만 유지

#### 7.1 GitHub Repository Secrets 설정

아래 시크릿을 저장소 설정에 등록해야 합니다.

- `DEPLOY_HOST`: VPS 호스트/IP
- `DEPLOY_PORT`: SSH 포트 (예: `22`)
- `DEPLOY_USER`: SSH 사용자
- `DEPLOY_SSH_KEY`: 배포용 private key(PEM 전체)
- `DEPLOY_PATH`: 서버 내 프로젝트 경로 (예: `/home/ubuntu/stock-manage-1/stock-manage-flask`)

#### 7.2 VPS 1회 초기 설정

```bash
# 서버에서 1회만
cd /home/ubuntu
git clone <YOUR_REPOSITORY_URL> stock-manage-1
cd stock-manage-1/stock-manage-flask
cp config.ini.example config.ini
# config.ini 편집
./scripts/start-docker.sh install
```

#### 7.3 워크플로우 배포 방식

GitHub Actions는 서버에 SSH 접속해서 아래 순서로 배포합니다.

1. `git fetch --prune origin`
2. 이벤트에 맞는 브랜치 체크아웃
3. `./scripts/start-docker.sh --no-git-pull deploy`

즉, **코드 동기화 단계와 Docker 재기동 단계를 분리**하여 유지보수성을 높였습니다.

#### 7.4 운영 권장사항

- 운영 서버는 `pull_request` 배포 대신 별도 staging 서버를 두는 것을 권장
- `config.ini`, SSH 키 등 민감정보는 Git 커밋 금지
- 배포 실패 시 서버에서 아래 명령으로 즉시 점검:
  ```bash
  ./scripts/start-docker.sh ps
  ./scripts/start-docker.sh logs
  ```

## 라이선스

This project is licensed under the MIT License.


...

관리자 계정: ID: set2happy / PW: 1234
일반 계정: ID: 1111 / PW: 1111