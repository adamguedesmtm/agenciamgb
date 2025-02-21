#!/bin/bash
# CS2 Server Update Script
# Author: adamguedesmtm
# Created: 2025-02-21 03:19:37

source /opt/cs2server/config/.env

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configurações
LOG_FILE="/opt/cs2server/logs/update.log"
STEAMCMD_PATH="/opt/cs2server/steamcmd/steamcmd.sh"
CS2_PATH="/opt/cs2server/cs2"
BACKUP_PATH="/opt/cs2server/backups/cs2"

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> $LOG_FILE
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Backup das configurações atuais
log_message "Fazendo backup das configurações..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_PATH
tar -czf $BACKUP_PATH/cs2_config_$BACKUP_DATE.tar.gz $CS2_PATH/game/csgo/cfg/

# Parar o servidor
log_message "Parando o servidor CS2..."
systemctl stop cs2server

# Atualizar servidor
log_message "Iniciando atualização do servidor..."
$STEAMCMD_PATH +force_install_dir $CS2_PATH +login anonymous +app_update 730 validate +quit

if [ $? -eq 0 ]; then
    log_message "Atualização concluída com sucesso"
    
    # Restaurar configurações
    log_message "Restaurando configurações..."
    tar -xzf $BACKUP_PATH/cs2_config_$BACKUP_DATE.tar.gz -C /
    
    # Iniciar servidor
    log_message "Iniciando servidor..."
    systemctl start cs2server
    
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"✅ Servidor CS2 atualizado com sucesso!\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
else
    log_error "Falha na atualização"
    
    # Restaurar backup em caso de falha
    log_message "Restaurando backup..."
    tar -xzf $BACKUP_PATH/cs2_config_$BACKUP_DATE.tar.gz -C /
    
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"❌ Falha na atualização do servidor CS2\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
fi

# Limpar backups antigos (manter últimos 5)
find $BACKUP_PATH -type f -name "cs2_config_*.tar.gz" | sort -r | tail -n +6 | xargs rm -f

log_message "Processo de atualização finalizado"