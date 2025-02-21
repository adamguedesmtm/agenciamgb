#!/bin/bash

# Script de instalação do CS2 Discord Bot
# Author: adamguedesmtm
# Created: 2025-02-21 14:02:49

# Configurações
INSTALL_DIR="/opt/cs2server"
CONFIG_DIR="$INSTALL_DIR/config"
LOG_DIR="/var/log/cs2server"
DEMOS_DIR="$INSTALL_DIR/demos"
ASSETS_DIR="$INSTALL_DIR/assets"
USER="cs2bot"
GROUP="cs2bot"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    error "Por favor, execute como root"
fi

# Criar usuário e grupo
log "Criando usuário e grupo $USER..."
if ! getent group "$GROUP" >/dev/null; then
    groupadd "$GROUP"
fi
if ! getent passwd "$USER" >/dev/null; then
    useradd -r -g "$GROUP" -d "$INSTALL_DIR" -s /bin/bash "$USER"
fi

# Criar diretórios
log "Criando diretórios..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DEMOS_DIR"
mkdir -p "$ASSETS_DIR"/{fonts,ranks,templates}

# Instalar dependências do sistema
log "Instalando dependências do sistema..."
apt-get update
apt-get install -y python3 python3-venv python3-pip \
    postgresql postgresql-contrib \
    imagemagick ffmpeg

# Clonar repositório
log "Clonando repositório..."
cd "$INSTALL_DIR"
git clone https://github.com/adamguedesmtm/agenciamgb.git .

# Configurar ambiente virtual
log "Configurando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar banco de dados
log "Configurando banco de dados..."
sudo -u postgres psql -c "CREATE USER cs2bot WITH PASSWORD 'cs2bot';"
sudo -u postgres psql -c "CREATE DATABASE cs2bot OWNER cs2bot;"

# Configurar permissões
log "Configurando permissões..."
chown -R "$USER:$GROUP" "$INSTALL_DIR"
chown -R "$USER:$GROUP" "$LOG_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod -R 644 "$CONFIG_DIR"/*
chmod +x start.sh

# Criar serviço systemd
log "Criando serviço systemd..."
cat > /etc/systemd/system/cs2bot.service << EOF
[Unit]
Description=CS2 Discord Bot
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh start
ExecStop=$INSTALL_DIR/start.sh stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd
systemctl daemon-reload
systemctl enable cs2bot.service

# Criar arquivo de configuração inicial
log "Criando arquivo de configuração inicial..."
cat > "$CONFIG_DIR/config.json" << EOF
{
    "discord": {
        "token": "YOUR_BOT_TOKEN_HERE",
        "prefix": "!",
        "admin_role": "Admin"
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "cs2bot",
        "user": "cs2bot",
        "password": "cs2bot"
    },
    "servers": {
        "competitive": {
            "host": "localhost",
            "port": 27015,
            "rcon_password": "CHANGE_THIS"
        },
        "wingman": {
            "host": "localhost",
            "port": 27016,
            "rcon_password": "CHANGE_THIS"
        },
        "retake": {
            "host": "localhost",
            "port": 27017,
            "rcon_password": "CHANGE_THIS"
        }
    }
}
EOF

# Finalizar instalação
log "Instalação concluída!"
log "Por favor, configure seu token do Discord e senhas RCON em $CONFIG_DIR/config.json"
log "Use 'systemctl start cs2bot' para iniciar o bot"