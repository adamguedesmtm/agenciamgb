#!/bin/bash
# Backup Script for CS2 Server
# Author: adamguedesmtm
# Created: 2025-02-21 03:12:49

# Carregar variáveis de ambiente
source /opt/cs2server/config/.env

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configurações
BACKUP_DIR="/opt/cs2server/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7
LOG_FILE="/opt/cs2server/logs/backup.log"

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> $LOG_FILE
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Criar diretórios
mkdir -p $BACKUP_DIR/{database,configs,demos}

# Backup da base de dados
log_message "Iniciando backup do banco de dados..."
if pg_dump -U $DB_USER cs2_matchmaking > $BACKUP_DIR/database/cs2_db_$TIMESTAMP.sql; then
    log_message "Backup do banco de dados concluído"
else
    log_error "Falha no backup do banco de dados"
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"❌ Falha no backup do banco de dados\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
fi

# Backup das configurações
log_message "Iniciando backup das configurações..."
if tar -czf $BACKUP_DIR/configs/configs_$TIMESTAMP.tar.gz /opt/cs2server/*/config/; then
    log_message "Backup das configurações concluído"
else
    log_error "Falha no backup das configurações"
fi

# Backup dos demos importantes
log_message "Iniciando backup dos demos..."
if tar -czf $BACKUP_DIR/demos/demos_$TIMESTAMP.tar.gz /opt/cs2server/demos/; then
    log_message "Backup dos demos concluído"
else
    log_error "Falha no backup dos demos"
fi

# Limpar backups antigos
log_message "Limpando backups antigos..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Calcular tamanho total dos backups
TOTAL_SIZE=$(du -sh $BACKUP_DIR | cut -f1)

# Enviar notificação para o Discord
curl -H "Content-Type: application/json" \
     -d "{\"content\": \"📦 Backup diário concluído\\n📊 Tamanho total: $TOTAL_SIZE\\n⏰ Data: $(date '+%Y-%m-%d %H:%M:%S')\"}" \
     https://discord.com/api/webhooks/$CHANNEL_ADMIN

log_message "Backup concluído! Tamanho total: $TOTAL_SIZE"