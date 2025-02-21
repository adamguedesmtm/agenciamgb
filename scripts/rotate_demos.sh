#!/bin/bash
# Demo Rotation Script
# Author: adamguedesmtm
# Created: 2025-02-21 03:24:21

source /opt/cs2server/config/.env

# Configurações
DEMO_DIR="/opt/cs2server/demos"
NEW_DEMOS="$DEMO_DIR/new"
PROCESSED_DEMOS="$DEMO_DIR/processed"
MAX_AGE_DAYS=30
MIN_PLAYERS=6

# Função de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEMO_DIR/rotation.log"
}

# Criar diretórios se não existirem
mkdir -p "$NEW_DEMOS" "$PROCESSED_DEMOS"

# Processar demos novos
for demo in "$NEW_DEMOS"/*.dem; do
    if [ -f "$demo" ]; then
        # Verificar número de players na demo
        player_count=$(grep -c "connected" "$demo")
        
        if [ $player_count -ge $MIN_PLAYERS ]; then
            # Mover para processados
            mv "$demo" "$PROCESSED_DEMOS/"
            log_message "Demo movido para processados: $(basename "$demo") - $player_count players"
        else
            # Remover demos com poucos players
            rm "$demo"
            log_message "Demo removido (poucos players): $(basename "$demo") - $player_count players"
        fi
    fi
done

# Remover demos antigos
find "$PROCESSED_DEMOS" -type f -name "*.dem" -mtime +$MAX_AGE_DAYS -delete
log_message "Demos mais antigos que $MAX_AGE_DAYS dias foram removidos"

# Verificar espaço em disco
TOTAL_SIZE=$(du -sh "$DEMO_DIR" | cut -f1)
log_message "Tamanho total dos demos: $TOTAL_SIZE"

# Notificar Discord se necessário
if [ $(df -h / | awk 'NR==2{print $5}' | tr -d '%') -gt 90 ]; then
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"⚠️ Espaço em disco crítico para demos: $TOTAL_SIZE utilizados\"}" \
         https://discord.com/api/webhooks/$CHANNEL_ADMIN
fi