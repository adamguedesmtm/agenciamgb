#!/bin/bash
# DNS Update Script
# Author: adamguedesmtm
# Created: 2025-02-21 03:19:37

source /opt/cs2server/config/.env

# Configurações
LOG_FILE="/opt/cs2server/logs/dns_update.log"
CURRENT_IP_FILE="/opt/cs2server/config/current_ip"

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Obter IP atual
CURRENT_IP=$(curl -s ifconfig.me)

# Verificar se o IP mudou
if [ -f $CURRENT_IP_FILE ] && [ "$(cat $CURRENT_IP_FILE)" == "$CURRENT_IP" ]; then
    log_message "IP não mudou: $CURRENT_IP"
    exit 0
fi

# Atualizar FreeDNS
UPDATE_URL="https://sync.afraid.org/u/$FREEDNS_KEY/"
UPDATE_RESULT=$(curl -s $UPDATE_URL)

if [[ $UPDATE_RESULT == *"Updated"* ]]; then
    log_message "DNS atualizado com sucesso para IP: $CURRENT_IP"
    echo $CURRENT_IP > $CURRENT_IP_FILE
    
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"✅ DNS atualizado para IP: $CURRENT_IP\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
else
    log_message "Falha ao atualizar DNS"
    
    # Notificar Discord
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"❌ Falha ao atualizar DNS\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
fi