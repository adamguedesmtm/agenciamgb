#!/bin/bash

# scripts/check_server_status.sh
# Script para verificar se há servidores ativos e processar demos pendentes se não houver

LOGFILE="/var/www/agenciamgb/storage/logs/server_status.log"

function log_message {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOGFILE
}

# Função para descriptografar uma string
function decrypt_string {
    local encrypted_string="$1"
    local encryption_key="$2"
    echo -n "$encrypted_string" | openssl enc -aes-256-cbc -a -d -salt -pass pass:"$encryption_key"
}

# Carregar as credenciais do .env
if [ -f "/var/www/agenciamgb/.env" ]; then
    while IFS='=' read -r key value; do
        dotenv["$key"]="$value"
    done < "/var/www/agenciamgb/.env"
fi

# Descriptografar as credenciais
encryption_key="${dotenv['ENCRYPTION_KEY']}"
db_host=$(decrypt_string "${dotenv['DB_HOST']}" "$encryption_key")
db_name=$(decrypt_string "${dotenv['DB_NAME']}" "$encryption_key")
db_user=$(decrypt_string "${dotenv['DB_USER']}" "$encryption_key")
db_pass=$(decrypt_string "${dotenv['DB_PASS']}" "$encryption_key")
discord_bot_token=$(decrypt_string "${dotenv['DISCORD_BOT_TOKEN']}" "$encryption_key")
steam_api_key=$(decrypt_string "${dotenv['STEAM_API_KEY']}" "$encryption_key")

# Verificar se há servidores ativos
COUNT=$(sqlite3 "/var/www/agenciamgb/storage/logs/stats.db" "SELECT COUNT(*) FROM active_servers WHERE status = 'running';")

if [ "$COUNT" -eq 0 ]; then
    log_message "Nenhum servidor ativo. Processando demos pendentes."
    /usr/bin/php /var/www/agenciamgb/scripts/process_demos.php
else
    log_message "Servidores ativos encontrados. Não processando demos."
fi

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