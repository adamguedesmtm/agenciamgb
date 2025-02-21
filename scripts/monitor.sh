#!/bin/bash
# System Monitoring Script
# Author: adamguedesmtm
# Created: 2025-02-21 03:12:49

source /opt/cs2server/config/.env

# Configurações
LOG_FILE="/opt/cs2server/logs/monitor.log"
ALERT_THRESHOLD_CPU=90
ALERT_THRESHOLD_MEM=90
ALERT_THRESHOLD_DISK=90
ALERT_THRESHOLD_TEMP=80

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Verificar serviços
check_service() {
    if ! systemctl is-active --quiet $1; then
        systemctl restart $1
        log_message "Serviço $1 reiniciado"
        
        curl -H "Content-Type: application/json" \
             -d "{\"content\": \"⚠️ Serviço $1 reiniciado automaticamente\"}" \
             https://discord.com/api/webhooks/$CHANNEL_ADMIN
    fi
}

# Verificar recursos
check_resources() {
    # CPU
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    # Memória
    MEM=$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2 }')
    # Disco
    DISK=$(df -h / | awk 'NR==2{print $5}' | tr -d '%')
    # Temperatura
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp | awk '{printf "%.1f", $1/1000}')

    ALERT_MESSAGE=""

    # Verificar CPU
    if [ $(echo "$CPU > $ALERT_THRESHOLD_CPU" | bc -l) -eq 1 ]; then
        ALERT_MESSAGE="$ALERT_MESSAGE\\n🔥 CPU em uso crítico: ${CPU}%"
    fi

    # Verificar Memória
    if [ $(echo "$MEM > $ALERT_THRESHOLD_MEM" | bc -l) -eq 1 ]; then
        ALERT_MESSAGE="$ALERT_MESSAGE\\n🔥 Memória em uso crítico: ${MEM}%"
    fi

    # Verificar Disco
    if [ $(echo "$DISK > $ALERT_THRESHOLD_DISK" | bc -l) -eq 1 ]; then
        ALERT_MESSAGE="$ALERT_MESSAGE\\n🔥 Disco quase cheio: ${DISK}%"
    fi

    # Verificar Temperatura
    if [ $(echo "$TEMP > $ALERT_THRESHOLD_TEMP" | bc -l) -eq 1 ]; then
        ALERT_MESSAGE="$ALERT_MESSAGE\\n🔥 Temperatura crítica: ${TEMP}°C"
    fi

    # Enviar alerta se necessário
    if [ ! -z "$ALERT_MESSAGE" ]; then
        log_message "Alertas detectados: $ALERT_MESSAGE"
        curl -H "Content-Type: application/json" \
             -d "{\"content\": \"⚠️ ALERTAS:$ALERT_MESSAGE\"}" \
             https://discord.com/api/webhooks/$CHANNEL_ADMIN
    fi
}

# Verificar todos os serviços
check_service cs2server
check_service cs2bot
check_service matchzy
check_service postgresql

# Verificar recursos
check_resources

# Log de execução bem-sucedida
log_message "Verificação de sistema concluída"