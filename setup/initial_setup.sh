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
    apache2 \
    libapache2-mod-php \
    php \
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
    sqlite3 \
    certbot \
    python3-certbot-apache

# Verificar se o PHP foi instalado corretamente
if ! command -v php &> /dev/null; then
    echo "PHP não foi instalado corretamente. Tentando instalar novamente..."
    apt-get install -y php
fi

# Verificar se o Composer foi instalado corretamente
if ! command -v composer &> /dev/null; then
    echo "Composer não foi instalado corretamente. Tentando instalar novamente..."
    curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
fi

# Instalar dependências do PHP
composer require discord-php/discord-php || { echo "Falha ao instalar discord-php/discord-php"; exit 1; }
composer require doctrine/dbal || { echo "Falha ao instalar doctrine/dbal"; exit 1; }

# Verificar se o Node.js foi instalado corretamente
if ! command -v node &> /dev/null; then
    echo "Node.js não foi instalado corretamente. Tentando instalar novamente..."
    apt-get install -y nodejs
fi

# Verificar se o npm foi instalado corretamente
if ! command -v npm &> /dev/null; then
    echo "npm não foi instalado corretamente. Tentando instalar novamente..."
    apt-get install -y npm
fi

# Instalar CS Demo Manager
npm install -g cs-demo-manager || { 
    echo "Falha ao instalar CS Demo Manager. Tentando instalar a partir do GitHub...";
    git clone https://github.com/saulouis/cs-demo-manager.git /tmp/cs-demo-manager
    cd /tmp/cs-demo-manager
    npm install
    npm link -g
    cd -
    rm -rf /tmp/cs-demo-manager
}

# Verificar se o SQLite foi instalado corretamente
if ! command -v sqlite3 &> /dev/null; then
    echo "SQLite3 não foi instalado corretamente. Tentando instalar novamente..."
    apt-get install -y sqlite3
fi

# Criar banco de dados e tabelas
/usr/bin/php /var/www/agenciamgb/config/db.php || { echo "Falha ao criar banco de dados e tabelas"; exit 1; }

# Configurar o cron job
/bin/bash /var/www/agenciamgb/setup/setup_cron_job.sh || { echo "Falha ao configurar o cron job"; exit 1; }

# Verificar se o Docker foi instalado corretamente
if ! command -v docker &> /dev/null; then
    echo "Docker não foi instalado corretamente. Instalando Docker..."
    # Instalar Docker
    apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io
    systemctl start docker
    systemctl enable docker
fi

# Verificar se o Docker Compose foi instalado corretamente
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não foi instalado corretamente. Instalando Docker Compose..."
    # Instalar Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Iniciar os serviços
docker-compose up -d || { echo "Falha ao iniciar os serviços"; exit 1; }