#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# MongoDB Backup Script using Docker
# usage: ./scripts/backup-db.sh
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# backup 디렉토리 설정 (아규먼트가 있으면 해당 경로, 없으면 기본 backups 로 설정)
BACKUP_BASE_DIR="${1:-backups}"
# 절대 경로로 변환 (Docker 마운트를 위함)
mkdir -p "${BACKUP_BASE_DIR}"
ABS_BACKUP_BASE_DIR="$(cd "${BACKUP_BASE_DIR}" && pwd)"

log() {
    printf ">>> %s\n" "$*"
}

die() {
    printf "!!! %s\n" "$*" >&2
    exit 1
}

# config.ini 존재 확인
if [ ! -f "config.ini" ]; then
    die "config.ini file not found."
fi

# config.ini에서 접속 정보 추출 (단순 grep 방식)
ACCESS_URL=$(grep -i "^access_url" config.ini | cut -d'=' -f2- | tr -d ' \r\n')
DB_NAME=$(grep -i "^database" config.ini | cut -d'=' -f2- | tr -d ' \r\n')

if [ -z "$ACCESS_URL" ] || [ -z "$DB_NAME" ]; then
    die "Failed to parse access_url or database from config.ini."
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DB_NAME}_${TIMESTAMP}"
DEST_DIR="/backups/${BACKUP_NAME}"

log "Starting backup for database: ${DB_NAME}"
log "Output will be saved to: ${BACKUP_BASE_DIR}/${BACKUP_NAME}"

# Docker를 이용해 mongodump 실행 (호스트에 몽고 클라이언트가 없어도 됨)
# --user $(id -u):$(id -g) 를 추가하여 권한 문제를 해결합니다.
docker run --rm \
    --user $(id -u):$(id -g) \
    -v "${ABS_BACKUP_BASE_DIR}:/backups" \
    mongo:latest \
    mongodump --uri="${ACCESS_URL}" --db "${DB_NAME}" --out "${DEST_DIR}"

if [ $? -eq 0 ]; then
    log "Backup completed successfully."
    log "Location: ${ABS_BACKUP_BASE_DIR}/${BACKUP_NAME}"
    
    # 압축 (선택 사항, 용량 절약을 위해 권장)
    log "Compressing backup..."
    tar -czf "${BACKUP_BASE_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_BASE_DIR}" "${BACKUP_NAME}"
    rm -rf "${BACKUP_BASE_DIR}/${BACKUP_NAME}"
    log "Compression complete: ${BACKUP_BASE_DIR}/${BACKUP_NAME}.tar.gz"
else
    die "Backup failed."
fi
