#!/bin/bash

# scripts/check_server_status.sh
# Script para verificar se há servidores ativos e processar demos pendentes se não houver

LOGFILE="/var/www/agenciamgb/storage/logs/server_status.log"

function log_message {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOGFILE
}

# Conectar ao banco de dados SQLite
DB_PATH="/var/www/agenciamgb/storage/logs/stats.db"

# Verificar se há servidores ativos
COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM active_servers WHERE status = 'running';")

if [ "$COUNT" -eq 0 ]; then
    log_message "Nenhum servidor ativo. Processando demos pendentes."
    /usr/bin/php /var/www/agenciamgb/scripts/process_demos.php
else
    log_message "Servidores ativos encontrados. Não processando demos."
fi