#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Docker lifecycle helper for local + VPS + CI/CD environments
# -----------------------------------------------------------------------------
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

BACKEND_URL="${BACKEND_URL:-http://localhost:5000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8080}"
DOCKER_EXTERNAL_NETWORK="${DOCKER_EXTERNAL_NETWORK:-mydocker-base-net}"
APP_SERVICES=(backend frontend)

COMMAND=""
DEPLOY_REF=""
SKIP_GIT_PULL=0
FOLLOW_LOGS=1

export FLASK_DEBUG=0
export LOG_LEVEL=INFO
export TZ="${TZ:-Asia/Seoul}"

COMPOSE_CMD=()

log() {
  printf ">>> %s\n" "$*"
}

warn() {
  printf "!!! %s\n" "$*" >&2
}

die() {
  warn "$*"
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || die "Required command not found: ${cmd}"
}

setup_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    die "Docker Compose not found. Install docker compose plugin or docker-compose."
  fi
}

run_compose() {
  "${COMPOSE_CMD[@]}" "$@"
}

show_help() {
  cat <<'EOF'
Usage:
  ./scripts/start-docker.sh [options] [command]

Purpose:
  Docker 기반 실행/배포를 로컬과 VPS에서 동일한 방식으로 운영합니다.

Commands:
  start        포그라운드 실행 (Ctrl+C로 종료)
  up           백그라운드 실행
  stop         컨테이너 중지/정리 (down)
  restart      stop 후 up
  build        이미지 빌드
  install      최초 설치: config.ini 확인 + 네트워크 확인 + 빌드/실행
  update       현재 브랜치 git pull(ff-only) + 재빌드/재기동
  deploy       CI/CD 배포용(backend/frontend 강제 recreate)
  logs         로그 확인 (기본 follow, --no-follow로 1회 출력)
  ps           컨테이너 상태
  help         도움말

Options:
  --debug          FLASK_DEBUG=1, LOG_LEVEL=DEBUG 로 실행
  --no-git-pull    update/deploy 시 git pull 단계 건너뜀
  --ref <ref>      deploy 시 특정 git ref/branch 체크아웃 후 배포
  --no-follow      logs 명령에서 follow 비활성화
  -h, --help       도움말

Examples:
  ./scripts/start-docker.sh install
  ./scripts/start-docker.sh up
  ./scripts/start-docker.sh deploy
  ./scripts/start-docker.sh --ref main deploy
  ./scripts/start-docker.sh --no-git-pull deploy
EOF
}

ensure_config_ini() {
  if [[ -f "${PROJECT_ROOT}/config.ini" ]]; then
    return
  fi

  if [[ -f "${PROJECT_ROOT}/config.ini.example" ]]; then
    cp -n "${PROJECT_ROOT}/config.ini.example" "${PROJECT_ROOT}/config.ini"
    warn "config.ini was missing, copied from config.ini.example."
    die "Please update config.ini values and run again."
  fi

  die "config.ini not found (and config.ini.example missing too)."
}

ensure_external_network() {
  # docker-compose.yml uses an external network. Create it automatically if absent.
  if [[ -z "${DOCKER_EXTERNAL_NETWORK}" ]]; then
    return
  fi

  if docker network inspect "${DOCKER_EXTERNAL_NETWORK}" >/dev/null 2>&1; then
    return
  fi

  log "Creating external docker network: ${DOCKER_EXTERNAL_NETWORK}"
  docker network create "${DOCKER_EXTERNAL_NETWORK}" >/dev/null
}

ensure_app_services_defined() {
  local services_raw services_joined svc
  services_raw="$(run_compose config --services)"
  services_joined="${services_raw//$'\n'/ }"

  for svc in "${APP_SERVICES[@]}"; do
    if [[ " ${services_joined} " != *" ${svc} "* ]]; then
      die "Service '${svc}' is missing in docker-compose.yml."
    fi
  done
}

sync_git_for_deploy() {
  [[ "${SKIP_GIT_PULL}" -eq 1 ]] && return

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    warn "Not a git repository, skipping git sync."
    return
  fi

  if [[ -n "${DEPLOY_REF}" ]]; then
    log "Syncing git ref: ${DEPLOY_REF}"
    git fetch --prune origin
    git checkout "${DEPLOY_REF}"
    if git show-ref --verify --quiet "refs/remotes/origin/${DEPLOY_REF}"; then
      git pull --ff-only origin "${DEPLOY_REF}"
    fi
    return
  fi

  local current_branch
  current_branch="$(git symbolic-ref --short -q HEAD || true)"

  if [[ -z "${current_branch}" ]]; then
    warn "Detached HEAD state detected; skipping git pull (use --ref <branch> if needed)."
    return
  fi

  log "Pulling latest code for branch: ${current_branch}"
  git pull --ff-only origin "${current_branch}"
}

cmd_start() {
  ensure_config_ini
  ensure_external_network
  log "Starting services in foreground..."
  log "Backend: ${BACKEND_URL} | Frontend: ${FRONTEND_URL}"
  run_compose up
}

cmd_up() {
  ensure_config_ini
  ensure_external_network
  log "Starting services in background..."
  run_compose up -d
  log "Backend: ${BACKEND_URL} | Frontend: ${FRONTEND_URL}"
}

cmd_stop() {
  log "Stopping and removing containers..."
  run_compose down
}

cmd_restart() {
  cmd_stop
  cmd_up
}

cmd_build() {
  ensure_config_ini
  ensure_external_network
  log "Building docker images..."
  run_compose build
}

cmd_install() {
  ensure_config_ini
  ensure_external_network
  log "Installing and starting containers..."
  run_compose up -d --build --remove-orphans
  log "Backend: ${BACKEND_URL} | Frontend: ${FRONTEND_URL}"
}

cmd_update() {
  ensure_config_ini
  ensure_external_network
  sync_git_for_deploy
  log "Rebuilding and restarting containers..."
  run_compose up -d --build --remove-orphans
}

cmd_deploy() {
  ensure_config_ini
  ensure_external_network
  sync_git_for_deploy
  # CI/CD: Pulling pre-built images first is faster & more reliable for production servers.
  log "Pulling latest images before recreation..."
  run_compose pull "${APP_SERVICES[@]}" || warn "Failed to pull some images; falling back to build."
  
  # Deploy must always restart app containers even if Docker thinks nothing changed.
  log "Force recreating ${APP_SERVICES[*]} containers for deployment..."
  run_compose up -d --build --force-recreate --remove-orphans "${APP_SERVICES[@]}"
}

cmd_logs() {
  if [[ "${FOLLOW_LOGS}" -eq 1 ]]; then
    run_compose logs -f
  else
    run_compose logs
  fi
}

cmd_ps() {
  run_compose ps
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --debug)
        export FLASK_DEBUG=1
        export LOG_LEVEL=DEBUG
        ;;
      --no-git-pull)
        SKIP_GIT_PULL=1
        ;;
      --ref)
        shift
        [[ $# -gt 0 ]] || die "--ref requires a value."
        DEPLOY_REF="$1"
        ;;
      --no-follow)
        FOLLOW_LOGS=0
        ;;
      -h|--help|help)
        COMMAND="help"
        ;;
      *)
        if [[ -z "${COMMAND}" ]]; then
          COMMAND="$1"
        else
          die "Unknown extra argument: $1"
        fi
        ;;
    esac
    shift
  done

  if [[ -z "${COMMAND}" ]]; then
    COMMAND="start"
  fi
}

main() {
  require_cmd docker
  setup_compose_cmd
  parse_args "$@"
  if [[ "${COMMAND}" != "help" ]]; then
    ensure_app_services_defined
  fi

  if [[ "${LOG_LEVEL}" == "DEBUG" ]]; then
    log "[DEBUG MODE] FLASK_DEBUG=1, LOG_LEVEL=DEBUG"
  fi

  case "${COMMAND}" in
    start)   cmd_start ;;
    up)      cmd_up ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    build)   cmd_build ;;
    install) cmd_install ;;
    update)  cmd_update ;;
    deploy)  cmd_deploy ;;
    logs)    cmd_logs ;;
    ps)      cmd_ps ;;
    help)    show_help ;;
    *)       die "Unknown command: ${COMMAND}. Use --help." ;;
  esac
}

main "$@"
