#!/bin/bash

# setup/setup_credentials.sh
# Script para perguntar as credenciais do banco de dados, API keys e outras credenciais, encriptá-las e armazenas em um arquivo .env

# Função para encriptar uma string
encrypt_string() {
    local string="$1"
    local encrypted_string
    encrypted_string=$(echo -n "$string" | openssl enc -aes-256-cbc -a -salt -pass pass:"$ENCRYPTION_KEY")
    echo "$encrypted_string"
}

# Função para descriptografar uma string
decrypt_string() {
    local encrypted_string="$1"
    local decrypted_string
    decrypted_string=$(echo -n "$encrypted_string" | openssl enc -aes-256-cbc -a -d -salt -pass pass:"$ENCRYPTION_KEY")
    echo "$decrypted_string"
}

# Gerar uma chave de encriptação
ENCRYPTION_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32 ; echo '')

# Perguntar as credenciais do banco de dados
read -p "Digite o nome do host do banco de dados (default: 127.0.0.1): " DB_HOST
DB_HOST=${DB_HOST:-127.0.0.1}

read -p "Digite o nome do banco de dados (default: csdm): " DB_NAME
DB_NAME=${DB_NAME:-csdm}

read -p "Digite o nome de usuário do banco de dados (default: postgres): " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "Digite a senha do banco de dados: " DB_PASS
echo

# Perguntar as API keys e outras credenciais
read -sp "Digite a API key do bot do Discord: " DISCORD_BOT_TOKEN
echo

read -sp "Digite a API key do Steam: " STEAM_API_KEY
echo

# Encriptar as credenciais
ENCRYPTED_DB_HOST=$(encrypt_string "$DB_HOST")
ENCRYPTED_DB_NAME=$(encrypt_string "$DB_NAME")
ENCRYPTED_DB_USER=$(encrypt_string "$DB_USER")
ENCRYPTED_DB_PASS=$(encrypt_string "$DB_PASS")
ENCRYPTED_DISCORD_BOT_TOKEN=$(encrypt_string "$DISCORD_BOT_TOKEN")
ENCRYPTED_STEAM_API_KEY=$(encrypt_string "$STEAM_API_KEY")

# Armazenar as credenciais encriptadas em um arquivo .env
cat <<EOF > /var/www/agenciamgb/.env
ENCRYPTION_KEY=$ENCRYPTION_KEY
DB_HOST=$ENCRYPTED_DB_HOST
DB_NAME=$ENCRYPTED_DB_NAME
DB_USER=$ENCRYPTED_DB_USER
DB_PASS=$ENCRYPTED_DB_PASS
DISCORD_BOT_TOKEN=$ENCRYPTED_DISCORD_BOT_TOKEN
STEAM_API_KEY=$ENCRYPTED_STEAM_API_KEY
EOF

echo "Credenciais encriptadas e armazenadas em /var/www/agenciamgb/.env"