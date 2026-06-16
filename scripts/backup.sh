#!/bin/bash
# QuoteFlow 数据库自动备份脚本
# 用法: 放在 crontab 中每天凌晨执行
# crontab: 0 2 * * * /home/admin/product-tool/scripts/backup.sh >> /home/admin/product-tool/backups/backup.log 2>&1

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[$(date)] Starting backup..."

# 1. Backup SQLite databases
for DB in "$PROJECT_DIR/backend/app.db" "$HOME/.product_tool/products.db"; do
    if [ -f "$DB" ]; then
        BASENAME=$(basename "$DB" .db)
        BACKUP_FILE="$BACKUP_DIR/${BASENAME}-${DATE}.db"
        cp "$DB" "$BACKUP_FILE"
        echo "  Backed up: $DB -> $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
    else
        echo "  Skipped (not found): $DB"
    fi
done

# 2. Backup environment config (if exists)
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    cp "$PROJECT_DIR/backend/.env" "$BACKUP_DIR/env-${DATE}.env"
    echo "  Backed up: .env"
fi

# 3. Clean old backups (keep last 7 days)
DELETED=$(find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "  Cleaned $DELETED old backups (>${RETENTION_DAYS}d)"

echo "[$(date)] Backup complete. Backups in: $BACKUP_DIR"
