#!/bin/bash

# setup/initial_setup.sh
# Script de configuração inicial

# Criar diretórios necessários
mkdir -p /var/www/agenciamgb/storage/uploads
mkdir -p /var/www/agenciamgb/storage/logs
mkdir -p /var/www/agenciamgb/storage/demos
mkdir -p /var/www/agenciamgb/storage/player_cards

# Instalar dependências do sistema
apt-get update && apt-get install -y \
    php \
    php-pgsql \
    php-gd \
    php-curl \
    php-json \
    php-mbstring \
    php-xml \
    php-zip \
    curl \
    git \
    nodejs \
    npm \
    cron \
    sqlite3

# Instalar Composer
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Instalar dependências do PHP
composer require discord-php/discord-php
composer require doctrine/dbal

# Instalar CS Demo Manager
npm install -g cs-demo-manager

# Criar banco de dados e tabelas
/usr/bin/php /var/www/agenciamgb/config/db.php

# Configurar o cron job
/bin/bash /var/www/agenciamgb/setup/setup_cron_job.sh

# Iniciar os serviços
docker-compose up -d