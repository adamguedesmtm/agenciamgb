#!/bin/bash
# Log Cleanup Script
# Author: adamguedesmtm
# Created: 2025-02-21 03:19:37

source /opt/cs2server/config/.env

# Configurações
LOG_DIR="/opt/cs2server/logs"
RETENTION_DAYS=7
MAX_SIZE_MB=1000  # 1GB

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_DIR/cleanup.log
}

# Limpar logs antigos
find $LOG_DIR -type f -name "*.log" -mtime +$RETENTION_DAYS -delete
log_message "Logs mais antigos que $RETENTION_DAYS dias foram removidos"

# Verificar tamanho total dos logs
TOTAL_SIZE=$(du -sm $LOG_DIR | cut -f1)

if [ $TOTAL_SIZE -gt $MAX_SIZE_MB ]; then
    log_message "Diretório de logs excedeu ${MAX_SIZE_MB}MB. Limpando logs mais antigos..."
    
    # Remover logs mais antigos até atingir o limite
    while [ $TOTAL_SIZE -gt $MAX_SIZE_MB ]; do
        OLDEST_LOG=$(find $LOG_DIR -type f -name "*.log" -printf '%T+ %p\n' | sort | head -n 1 | cut -d' ' -f2-)
        if [ -z "$OLDEST_LOG" ]; then
            break
        fi
        rm "$OLDEST_LOG"
        TOTAL_SIZE=$(du -sm $LOG_DIR | cut -f1)
    done
    
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"⚠️ Limpeza automática de logs realizada\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
fi

log_message "Limpeza de logs concluída. Tamanho atual: ${TOTAL_SIZE}MB"