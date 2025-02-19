#!/bin/bash
STEAMCMD_DIR="/opt/steamcmd"
CS2_DIR="/opt/cs2"

log() {
    echo "$(date '+%Y-%m-%d %T') - $1"
}

log "⬇️ Instalando SteamCMD..."
mkdir -p "$STEAMCMD_DIR" || { log "Falha ao criar diretório do SteamCMD."; exit 1; }
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - -C "$STEAMCMD_DIR" || { log "Falha ao baixar SteamCMD."; exit 1; }
chmod +x "$STEAMCMD_DIR/linux32/steamcmd" || { log "Falha ao definir permissões de execução para steamcmd."; exit 1; }
log "✅ SteamCMD instalado com sucesso."

log "🎮 Instalando servidor CS2..."
cd "$STEAMCMD_DIR"
./steamcmd.sh +force_install_dir "$CS2_DIR" +login anonymous +app_update 740 validate +quit || { log "Falha ao instalar CS2."; exit 1; }
log "✅ Servidor CS2 instalado com sucesso."