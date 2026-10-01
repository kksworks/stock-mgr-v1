# Skill: Release & Deployment (stock-manage-flask)

## 목적
이 프로젝트(Flask 백엔드 + Vue 3 프론트엔드 + MongoDB, Docker Compose 운영)를 로컬/VPS/CI에서 안전하게 실행·재기동·배포·롤백한다.

---

## 언제 사용하는가
- 로컬 PC에서 개발 서버를 띄우거나, Docker로 운영 환경을 재현할 때
- 코드 변경을 VPS(운영 서버)에 반영할 때
- 배포 전후로 데이터베이스를 백업/점검할 때
- GitHub Actions 배포가 실패했을 때 원인을 진단할 때
- 특정 시점(커밋/브랜치/태그)으로 롤백해야 할 때

---

## 실행 경로는 두 가지뿐이다 — 섞지 않는다

### A. 로컬 개발 (venv + npm dev server)
- `make dev` / `make start` / `./scripts/start.sh` — 백엔드(:5000/:8080)와 프론트(:5173 또는 :8080)를 동시에 기동
- `./scripts/start.sh install` — venv 생성 + `pip install -r requirements.txt` + `npm install`
- `./scripts/start.sh update` — 의존성 업데이트
- 이 경로는 **Docker를 쓰지 않는다.** venv가 없으면 반드시 먼저 `install`을 실행한다.

### B. Docker (로컬 재현 / VPS 운영 / CI 배포) — `./scripts/start-docker.sh`
모든 Docker 관련 작업은 이 스크립트 하나로 통일되어 있다. 직접 `docker compose` 명령을 새로 조합하지 말고 이 스크립트의 서브커맨드를 사용한다.

| 명령 | 용도 |
|---|---|
| `install` | 최초 설치: `config.ini` 확인 + 외부 네트워크 생성 + 빌드 + 백그라운드 기동 |
| `up` | 백그라운드 실행 (항상 `--build` 포함 — 이미지 재빌드 누락 방지) |
| `start` | 포그라운드 실행 (로그 보면서 디버깅할 때) |
| `stop` | `docker compose down` |
| `restart` | `stop` 후 `up` |
| `build` | 이미지만 빌드 |
| `update` | 현재 브랜치 `git pull --ff-only` + 재빌드/재기동 (로컬/VPS 수동 갱신용) |
| `deploy` | **CI/CD 전용.** `backend`/`frontend` 컨테이너를 강제 recreate. 사전에 이미지 `pull` 시도 후 실패하면 빌드로 폴백 |
| `logs` [`--no-follow`] | 로그 확인 |
| `ps` | 컨테이너 상태 확인 |

옵션:
- `--debug` → `FLASK_DEBUG=1`, `LOG_LEVEL=DEBUG`
- `--no-git-pull` → `update`/`deploy`에서 git 동기화 단계 생략 (CI가 이미 별도 checkout을 했을 때)
- `--ref <branch|tag|sha>` → 특정 ref로 체크아웃 후 배포

사전 조건:
- `config.ini`가 없으면 `config.ini.example`을 복사만 하고 즉시 종료한다(값 채우라는 안내). MongoDB `access_url`이 비어 있는 채로 기동을 시도하지 않는다.
- `docker-compose.yml`은 **외부 네트워크** `mydocker-base-net`(기본값)을 사용한다. 없으면 스크립트가 자동 생성하지만, 이름을 바꾸려면 `DOCKER_EXTERNAL_NETWORK` 환경변수를 배포 전에 export한다.
- `APP_VERSION`(git short sha)과 `APP_BUILD_DATE`는 스크립트가 자동으로 계산해 컨테이너 환경변수로 주입한다 — 수동으로 하드코딩하지 않는다.

---

## CI/CD — 두 워크플로우의 차이를 정확히 구분한다
- **`.github/workflows/deploy.yml` (권장, 빌드 최적화 방식)**: `main` push 시 GitHub Actions가 backend/frontend 이미지를 빌드해 GHCR에 push한 뒤, VPS에 `scripts/*`, `docker-compose.yml`, `config.ini.example`을 SCP로 복사하고 `./scripts/start-docker.sh deploy`만 실행한다. VPS는 이미지를 빌드하지 않고 pull만 하므로 VPS 부하가 적다.
- **`.github/workflows/deploy-docker.yml` (서버 빌드 방식)**: `main` push 또는 (같은 저장소 기준) PR 업데이트 시, VPS에서 `git fetch` + `git checkout -B <branch> origin/<branch>` 후 `./scripts/start-docker.sh --no-git-pull deploy`를 실행해 서버에서 직접 빌드한다. 동시 배포는 `concurrency` 그룹으로 이전 실행을 취소한다.
- 운영 서버에 두 워크플로우를 동시에 활성화하면 같은 배포가 이중으로 트리거될 수 있다 — 하나만 쓰는 것이 원칙이며, 어떤 것을 쓰는지 확인 없이 다른 워크플로우 파일을 새로 추가하지 않는다.
- 필요한 GitHub Repository Secrets: `DEPLOY_HOST`(필수), `DEPLOY_USER`(필수), `SSH_PRIVATE_KEY`(필수), `DEPLOY_PORT`(선택, 기본 22), `DEPLOY_PATH`(선택, 기본 `~/stock-manage`).

---

## 배포 전 필수 체크리스트
- [ ] `git status`가 깨끗한가 (배포는 커밋된 상태 기준으로 진행)
- [ ] **스키마/데이터에 영향을 주는 변경이면 배포 전 반드시 DB 백업**: `./scripts/backup-db.sh [백업경로]` (Mongo 클라이언트 없이도 임시 `mongo:latest` 컨테이너로 `mongodump` 수행, `config.ini`의 `access_url`/`database`를 자동으로 읽음)
- [ ] `config.ini`, SSH 프라이빗 키 등 민감정보가 커밋에 포함되지 않았는가
- [ ] 로컬에서 `./scripts/start-docker.sh up` 또는 `start`로 최소 1회 정상 기동을 확인했는가
- [ ] 운영 배포 후에는 `./scripts/start-docker.sh ps`와 `logs`로 즉시 상태 확인

## 롤백
- 특정 커밋/태그로 되돌리려면: `./scripts/start-docker.sh --ref <이전-sha-또는-태그> deploy`
- GHCR 기반(`deploy.yml`) 운영이면, 이전 태그 이미지를 가리키도록 조정 후 재배포하는 방법도 가능 — 태그 전략을 바꾸기 전에 사용자와 상의한다.
- 데이터까지 되돌려야 하면 `backup-db.sh`로 만든 백업을 `mongorestore`로 복원한다 (이 저장소에는 restore 스크립트가 없으므로, 수동 `docker run mongo:latest mongorestore ...`로 수행하고 실행 전 반드시 사용자에게 확인받는다 — 데이터 손실 위험이 있는 작업).

---

## 금지 사항
- `config.ini`, SSH 키, `.env` 등 민감정보 커밋 금지
- 백업 없이 스키마/마이그레이션 변경을 운영 서버에 배포 금지
- `docker compose`를 스크립트 밖에서 직접 조합해 운영 서버 상태를 스크립트와 어긋나게 만들지 말 것
- `deploy` 대상 서버가 어떤 CI 워크플로우(`deploy.yml` vs `deploy-docker.yml`)를 쓰는지 모른 채 워크플로우 파일을 수정/추가 금지
- 사용자 승인 없이 운영(VPS) 서버에 대해 `restart`/`deploy`/`stop`/데이터 복원 등 실제 영향이 있는 명령을 실행 금지 — 로컬 `docker compose` 조작과 달리 운영 서버 작업은 되돌리기 어렵다
