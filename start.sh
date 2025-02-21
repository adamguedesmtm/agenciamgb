#!/bin/bash

# Script de inicialização do CS2 Discord Bot
# Author: adamguedesmtm
# Created: 2025-02-21 14:02:49

# Configurar ambiente
export CS2BOT_ENV="production"
export CS2BOT_CONFIG="/opt/cs2server/config/config.json"
export PYTHONPATH="/opt/cs2server/src:$PYTHONPATH"

# Diretório do bot
BOT_DIR="/opt/cs2server"
LOG_DIR="/var/log/cs2server"
PID_FILE="/var/run/cs2bot.pid"

# Criar diretórios necessários
mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$PID_FILE")"

# Função para iniciar o bot
start_bot() {
    echo "Iniciando CS2 Discord Bot..."
    cd "$BOT_DIR" || exit 1
    
    # Ativar ambiente virtual
    source venv/bin/activate

    # Iniciar bot com nohup
    nohup python -m src.bot.bot > "$LOG_DIR/bot.log" 2>&1 &
    
    # Salvar PID
    echo $! > "$PID_FILE"
    echo "Bot iniciado com PID $(cat "$PID_FILE")"
}

# Função para parar o bot
stop_bot() {
    if [ -f "$PID_FILE" ]; then
        echo "Parando CS2 Discord Bot..."
        kill $(cat "$PID_FILE")
        rm "$PID_FILE"
        echo "Bot parado"
    else
        echo "PID file não encontrado"
    fi
}

# Função para reiniciar o bot
restart_bot() {
    stop_bot
    sleep 2
    start_bot
}

# Função para verificar status
status_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo "Bot está rodando (PID: $PID)"
        else
            echo "Bot não está rodando (PID file existe mas processo não encontrado)"
            rm "$PID_FILE"
        fi
    else
        echo "Bot não está rodando"
    fi
}

# Processar argumentos
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0