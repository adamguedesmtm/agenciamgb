#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d)

# Backup do servidor CS2
tar -czf "${BACKUP_DIR}/cs2_backup_${DATE}.tar.gz" /opt/cs2 2>/dev/null

# Backup do bot do Discord
tar -czf "${BACKUP_DIR}/discord_bot_backup_${DATE}.tar.gz" /opt/bot-discord 2>/dev/null

# Backup dos plugins
tar -czf "${BACKUP_DIR}/plugins_backup_${DATE}.tar.gz" /opt/plugins 2>/dev/null

# Limpar backups antigos (manter apenas os últimos 7 dias)
find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +7 -delete
``` ▋