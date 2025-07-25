#!/bin/bash

# Database backup script for IU Alumni Backend
# This script creates compressed PostgreSQL backups with timestamps

# Load environment variables
if [ -f /root/iu-alumni-backend/.env ]; then
    export $(grep -v '^#' /root/iu-alumni-backend/.env | xargs)
fi

# Set default values if environment variables are not set
POSTGRES_DB=${POSTGRES_DB:-iu_alumni_db}
POSTGRES_USER=${POSTGRES_USER:-alumni_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-alumni_password}

# Backup configuration
BACKUP_DIR="/root/iu-alumni-backend/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/iu_alumni_db_backup_${DATE}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "Starting database backup..."

# Navigate to project directory
cd /root/iu-alumni-backend

# Check if postgres container is running
CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep postgres | head -1)
if [ -z "$CONTAINER_NAME" ]; then
    log_message "ERROR: PostgreSQL container not found!"
    exit 1
fi

# Create backup using Docker exec (more reliable than host connection)
if docker exec "$CONTAINER_NAME" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
   --clean --if-exists --create --verbose 2>>"$LOG_FILE" | gzip > "$BACKUP_FILE"; then

    # Check if backup file was created and has reasonable size
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        BACKUP_BYTES=$(stat -c%s "$BACKUP_FILE")

        if [ "$BACKUP_BYTES" -lt 100 ]; then
            log_message "ERROR: Backup file is too small ($BACKUP_BYTES bytes)"
            exit 1
        fi

        log_message "Backup completed successfully: $BACKUP_FILE (Size: $BACKUP_SIZE)"

        # Clean up old backups (keep last 7 days)
        find "$BACKUP_DIR" -name "iu_alumni_db_backup_*.sql.gz" -mtime +7 -delete
        log_message "Old backups cleaned up (kept last 7 days)"
    else
        log_message "ERROR: Backup file was not created or is empty!"
        exit 1
    fi
else
    log_message "ERROR: Backup failed!"
    exit 1
fi

log_message "Backup process completed."
