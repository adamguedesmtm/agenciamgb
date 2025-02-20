#!/bin/bash
# Script para configurar um servidor Debian 12 com as portas necessárias para CS2, Bot do Discord e Web Server

set -euo pipefail
IFS=$'\n\t'

# --- Variáveis ---
HOSTNAME="cs2-server"
TIMEZONE="Europe/Lisbon" # Altere para sua timezone
SSH_PORT=2222            # Porta personalizada para SSH
PUBLIC_IP=$(curl -s ifconfig.me || echo "UNKNOWN_IP")
NETWORK_INTERFACE=$(ip route | grep default | awk '{print $5}' || echo "eth0")
LOG_FILE="/var/log/initial_setup.log"

# --- Configurações de Portas ---
CS2_PORT_UDP="27015"       # Porta principal do servidor CS2 (UDP)
CS2_PORT_TCP="27015"       # Porta RCON do servidor CS2 (TCP)
CS2_QUERY_PORT="27005"     # Porta de consulta do servidor CS2 (UDP)
GSI_PORT="3000"            # Porta para Game State Integration (TCP)
FLASK_PORT="5000"          # Porta para o servidor Flask (GSI)
WEB_HTTP_PORT="80"         # Porta HTTP para o web server
WEB_HTTPS_PORT="443"       # Porta HTTPS para o web server
API_PORT="8080"            # Porta para APIs adicionais

# --- Funções ---
log() {
    echo "$(date '+%Y-%m-%d %T') - $1" | tee -a "$LOG_FILE"
}

error_log() {
    echo "$(date '+%Y-%m-%d %T') - [ERRO] $1" >> "$LOG_FILE"
}

fatal_error() {
    error_log "$1"
    log "❌ Falha crítica detectada. Executando rollback..."
    rollback
    exit 1
}

rollback() {
    log "🔄 Executando rollback das alterações..."
    # Aqui você pode adicionar comandos específicos para desfazer alterações, se necessário
    log "✅ Rollback concluído."
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        fatal_error "Este script deve ser executado como root. Use 'sudo'."
    fi
}

update_system() {
    log "🔄 Atualizando sistema..."
    if ! apt update && apt upgrade -y; then
        fatal_error "Falha ao atualizar o sistema."
    fi
    log "✅ Sistema atualizado."
}

configure_hostname() {
    log "🌐 Configurando hostname para $HOSTNAME..."
    if ! hostnamectl set-hostname "$HOSTNAME"; then
        fatal_error "Falha ao configurar o hostname."
    fi
    if ! echo "127.0.1.1 $HOSTNAME" >> /etc/hosts; then
        fatal_error "Falha ao configurar /etc/hosts."
    fi
    log "✅ Hostname configurado com sucesso."
}

configure_timezone() {
    log "⏰ Configurando timezone para $TIMEZONE..."
    if ! timedatectl set-timezone "$TIMEZONE"; then
        fatal_error "Falha ao configurar o timezone."
    fi
    log "✅ Timezone configurado com sucesso."
}

configure_network() {
    log "🌐 Configurando interface de rede $NETWORK_INTERFACE..."

    cp /etc/network/interfaces /etc/network/interfaces.bak || fatal_error "Falha ao fazer backup de /etc/network/interfaces."
    cat > /etc/network/interfaces <<EOF
auto lo
iface lo inet loopback

auto $NETWORK_INTERFACE
iface $NETWORK_INTERFACE inet dhcp
EOF

    if ! systemctl restart networking; then
        fatal_error "Falha ao reiniciar o serviço de rede."
    fi
    log "✅ Interface de rede configurada com sucesso."
}

configure_ssh() {
    log "🔑 Configurando SSH na porta $SSH_PORT..."

    if ! sed -i "s/^#Port .*/Port $SSH_PORT/" /etc/ssh/sshd_config; then
        fatal_error "Falha ao alterar a porta SSH."
    fi
    if ! sed -i "s/^PermitRootLogin .*/PermitRootLogin no/" /etc/ssh/sshd_config; then
        fatal_error "Falha ao desativar login root via SSH."
    fi
    if ! systemctl restart ssh; then
        fatal_error "Falha ao reiniciar o serviço SSH."
    fi
    log "✅ SSH configurado com sucesso."
}

configure_firewall() {
    log "🔥 Configurando firewall (UFW)..."

    if ! apt install -y ufw; then
        fatal_error "Falha ao instalar UFW."
    fi

    # Abrir portas necessárias
    ufw allow "$SSH_PORT"/tcp || fatal_error "Falha ao permitir porta SSH no firewall."
    ufw allow "$CS2_PORT_UDP"/udp || fatal_error "Falha ao permitir porta UDP $CS2_PORT_UDP (CS2)."
    ufw allow "$CS2_PORT_TCP"/tcp || fatal_error "Falha ao permitir porta TCP $CS2_PORT_TCP (RCON)."
    ufw allow "$CS2_QUERY_PORT"/udp || fatal_error "Falha ao permitir porta UDP $CS2_QUERY_PORT (CS2 Query)."
    ufw allow "$GSI_PORT"/tcp || fatal_error "Falha ao permitir porta TCP $GSI_PORT (GSI)."
    ufw allow "$FLASK_PORT"/tcp || fatal_error "Falha ao permitir porta TCP $FLASK_PORT (Flask)."
    ufw allow "$WEB_HTTP_PORT"/tcp || fatal_error "Falha ao permitir HTTP no firewall."
    ufw allow "$WEB_HTTPS_PORT"/tcp || fatal_error "Falha ao permitir HTTPS no firewall."
    ufw allow "$API_PORT"/tcp || fatal_error "Falha ao permitir porta TCP $API_PORT (API)."

    if ! ufw enable; then
        fatal_error "Falha ao habilitar UFW."
    fi
    log "✅ Firewall configurado com sucesso."
}

setup_fail2ban() {
    log "🔒 Configurando Fail2Ban..."

    if ! apt install -y fail2ban; then
        fatal_error "Falha ao instalar Fail2Ban."
    fi

    cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local || fatal_error "Falha ao criar jail.local."
    if ! sed -i "s/^bantime = .*/bantime = 3600/" /etc/fail2ban/jail.local; then
        fatal_error "Falha ao configurar bantime."
    fi
    if ! sed -i "s/^maxretry = .*/maxretry = 3/" /etc/fail2ban/jail.local; then
        fatal_error "Falha ao configurar maxretry."
    fi
    if ! systemctl restart fail2ban; then
        fatal_error "Falha ao reiniciar Fail2Ban."
    fi
    log "✅ Fail2Ban configurado com sucesso."
}

install_basic_packages() {
    log "📦 Instalando pacotes básicos..."

    if ! apt install -y curl git nginx python3 python3-pip docker.io; then
        fatal_error "Falha ao instalar pacotes básicos."
    fi
    log "✅ Pacotes básicos instalados com sucesso."
}

# --- Execução ---
check_root

log "🎉 Iniciando configuração inicial..."

(
    update_system
    configure_hostname
    configure_timezone
    configure_network
    configure_ssh
    configure_firewall
    setup_fail2ban
    install_basic_packages
) || fatal_error "Erro durante a execução do script."

log "🎉 Configuração inicial concluída!"