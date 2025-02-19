#!/bin/bash
# Script completo para configurar um servidor Debian 12 com CS2, Web Stats, Bot do Discord, FreeDNS, Gerenciador de Plugins e Backup Automático

set -euo pipefail
IFS=$'\n\t'

# --- Variáveis ---
HOSTNAME="cs2-server"
TIMEZONE="Europe/Lisbon" # Altere para sua timezone
SSH_PORT=2222            # Porta personalizada para SSH
PUBLIC_IP=$(curl -s ifconfig.me)
NETWORK_INTERFACE=$(ip route | grep default | awk '{print $5}')
DOMAIN="stats.agenciamgb.strangled.net" # Domínio FreeDNS
FREEDNS_UPDATE_URL="https://freedns.strangled.net/nic/update?hostname=$DOMAIN&myip=$PUBLIC_IP"
LOG_FILE="/var/log/debian_cs2_setup.log"

# --- Configurações ---
WEB_USER="cs2stats"
WEB_DIR="/var/www/stats"
API_PORT="8080"
CS_PORT="27015"
STEAMCMD_DIR="/opt/steamcmd"
CS2_DIR="/opt/cs2"
PLUGIN_BASE_DIR="/opt/plugins"
WEB_PLUGIN_DIR="$PLUGIN_BASE_DIR/web-plugins"
DISCORD_PLUGIN_DIR="$PLUGIN_BASE_DIR/discord-plugins"
CS2_PLUGIN_DIR="$PLUGIN_BASE_DIR/cs2-plugins"
BOT_REPO="https://github.com/seu-usuario/discord-bot.git" # Substitua pelo URL do seu repositório
BOT_DIR="/opt/bot-discord"
LOG_FILE_CS2="/var/log/cs2_setup.log"
UPLOAD_DIR="/var/www/stats/uploads"
DEMO_MANAGER_DIR="/opt/cs-demo-manager"
SERVICE_USER="cs2server"
CONFIG_FILE="/etc/cs2_config.enc"
BACKUP_DIR="/backups"
MASTER_KEY="/path/to/master.key"

# --- Funções ---

log() {
    echo "$(date '+%Y-%m-%d %T') - $1" | tee -a "$LOG_FILE"
}

error_log() {
    echo "$(date '+%Y-%m-%d %T') - [ERRO] $1" >> "$LOG_FILE"
}

progress_bar() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    PERCENTAGE=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    BAR_LENGTH=50
    FILLED=$((PERCENTAGE * BAR_LENGTH / 100))
    EMPTY=$((BAR_LENGTH - FILLED))
    printf "\r[%-${BAR_LENGTH}s] %d%% - %s" "$(printf '#%.0s' $(seq 1 $FILLED))$(printf ' %.0s' $(seq 1 $EMPTY))" $PERCENTAGE "${STEPS[$((CURRENT_STEP - 1))]}"
    echo ""
}

decrypt_credentials() {
    log "🔑 Descriptografando credenciais..."
    if [ ! -f "$CONFIG_FILE" ]; then
        error_log "Arquivo de credenciais não encontrado: $CONFIG_FILE"
        return 1
    fi
    if [ ! -f "$MASTER_KEY" ]; then
        error_log "Arquivo de chave mestra não encontrado: $MASTER_KEY"
        return 1
    fi
    openssl enc -aes-256-cbc -d -in "$CONFIG_FILE" -out /tmp/cs2_key.bin -kfile "$MASTER_KEY" || { error_log "Falha ao descriptografar credenciais."; return 1; }
    source /tmp/cs2_key.bin
    shred -u /tmp/cs2_key.bin
    log "✅ Credenciais carregadas com sucesso."
}

install_dependencies() {
    log "📦 Instalando dependências..."
    apt update && apt install -y \
        curl git nginx fail2ban unzip wget software-properties-common python3-pip docker.io lib32gcc-s1 lib32stdc++6 lib32z1 \
        nodejs npm php-fpm php-mysql php-curl php-cli php-gd php-json php-mbstring php-xml php-zip \
        xorg openbox lxterminal xterm fluxbox chromium || { error_log "Falha ao instalar dependências."; return 1; }
    usermod -aG docker root
    systemctl enable --now docker
    log "✅ Dependências instaladas com sucesso."
}

install_steamcmd() {
    log "⬇️ Instalando SteamCMD..."
    mkdir -p "$STEAMCMD_DIR" || { error_log "Falha ao criar diretório do SteamCMD."; return 1; }
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - -C "$STEAMCMD_DIR" || { error_log "Falha ao baixar SteamCMD."; return 1; }
    chmod +x "$STEAMCMD_DIR/linux32/steamcmd" || { error_log "Falha ao definir permissões de execução para steamcmd."; return 1; }
    log "✅ SteamCMD instalado com sucesso."
}

install_cs2_server() {
    log "🎮 Instalando servidor CS2..."
    cd "$STEAMCMD_DIR"
    ./steamcmd.sh +force_install_dir "$CS2_DIR" +login anonymous +app_update 740 validate +quit || { error_log "Falha ao instalar CS2."; return 1; }
    log "✅ Servidor CS2 instalado com sucesso."
}

configure_firewall() {
    log "🔥 Configurando firewall..."
    apt update && apt install -y ufw || { error_log "Falha ao instalar UFW."; return 1; }
    ufw allow "$SSH_PORT/tcp"
    ufw allow 27015:27020/tcp
    ufw allow 27015:27020/udp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable || { error_log "Falha ao configurar firewall."; return 1; }
    log "✅ Firewall configurado com sucesso."
}

configure_ssh() {
    log "🔒 Configurando SSH na porta $SSH_PORT..."
    sed -i "s/#Port 22/Port $SSH_PORT/" /etc/ssh/sshd_config || { error_log "Falha ao alterar porta SSH."; return 1; }
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config || { error_log "Falha ao desativar login root."; return 1; }
    systemctl restart sshd || { error_log "Falha ao reiniciar serviço SSH."; return 1; }
    log "✅ SSH configurado com sucesso."
}

configure_hostname() {
    log "💻 Configurando hostname para $HOSTNAME..."
    echo "$HOSTNAME" > /etc/hostname || { error_log "Falha ao configurar o hostname."; return 1; }
    sed -i "s/127.0.1.1.*/127.0.1.1\t$HOSTNAME/g" /etc/hosts || { error_log "Falha ao configurar /etc/hosts."; return 1; }
    hostnamectl set-hostname "$HOSTNAME" || { error_log "Falha ao aplicar o hostname."; return 1; }
    log "✅ Hostname configurado com sucesso."
}

configure_timezone() {
    log "⏰ Configurando timezone para $TIMEZONE..."
    timedatectl set-timezone "$TIMEZONE" || { error_log "Falha ao configurar o timezone."; return 1; }
    log "✅ Timezone configurado com sucesso."
}

configure_network() {
    log "🌐 Configurando interface de rede $NETWORK_INTERFACE..."

    NETPLAN_CONFIG="/etc/netplan/01-netcfg.yaml"

    cat > "$NETPLAN_CONFIG" <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    $NETWORK_INTERFACE:
      dhcp4: true
EOF

    netplan apply || { error_log "Falha ao aplicar a configuração de rede."; return 1; }
    log "✅ Rede configurada com sucesso."
}

setup_fail2ban() {
    log "🛡️ Configurando Fail2Ban..."
    apt update && apt install -y fail2ban || { error_log "Falha ao instalar Fail2Ban."; return 1; }

    # Configurar jail.local para proteger SSH
    cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

    systemctl restart fail2ban || { error_log "Falha ao reiniciar Fail2Ban."; return 1; }
    log "✅ Fail2Ban configurado com sucesso."
}

update_freedns() {
    log "🔄 Atualizando registro DNS no FreeDNS..."

    if [ -z "$FREEDNS_USERNAME" ] || [ -z "$FREEDNS_PASSWORD" ]; then
        error_log "Credenciais da FreeDNS não foram configuradas corretamente."
        return 1
    fi

    RESPONSE=$(curl -s -u "$FREEDNS_USERNAME:$FREEDNS_PASSWORD" "$FREEDNS_UPDATE_URL")
    if [[ "$RESPONSE" == *"good"* || "$RESPONSE" == *"nochg"* ]]; then
        log "✅ Registro DNS atualizado com sucesso para $DOMAIN ($PUBLIC_IP)."
    elif [[ "$RESPONSE" == *"nohost"* ]]; then
        error_log "Falha ao atualizar o registro DNS. O hostname $DOMAIN não existe na conta da FreeDNS."
    elif [[ "$RESPONSE" == *"badauth"* ]]; then
        error_log "Falha ao atualizar o registro DNS. Credenciais da FreeDNS inválidas."
    elif [[ "$RESPONSE" == *"notfqdn"* ]]; then
        error_log "Falha ao atualizar o registro DNS. O hostname $DOMAIN não é um FQDN válido."
    elif [[ "$RESPONSE" == *"badagent"* ]]; then
        error_log "Falha ao atualizar o registro DNS. O cliente de atualização não é suportado pela FreeDNS."
    elif [[ "$RESPONSE" == *"abuse"* ]]; then
        error_log "Falha ao atualizar o registro DNS. Sua conta foi bloqueada por abuso."
    else
        error_log "Falha ao atualizar o registro DNS. Resposta inesperada: $RESPONSE"
    fi
    progress_bar
}

configure_swap() {
    log "😴 Configurando arquivo de swap..."

    if [ ! -f /swapfile ]; then
        log "Criando arquivo de swap de 2GB..."
        sudo fallocate -l 2G /swapfile || { error_log "Falha ao criar arquivo de swap."; return 1; }
        sudo chmod 600 /swapfile || { error_log "Falha ao definir permissões do arquivo de swap."; return 1; }
        sudo mkswap /swapfile || { error_log "Falha ao formatar arquivo de swap."; return 1; }
        sudo swapon /swapfile || { error_log "Falha ao ativar arquivo de swap."; return 1; }

        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        log "✅ Arquivo de swap configurado com sucesso."
    else
        log "⚠️ O arquivo de swap já existe. Ignorando a criação."
    fi
    progress_bar
}

setup_directories() {
    log "📁 Configurando diretórios..."

    mkdir -p "$PLUGIN_BASE_DIR" || { error_log "Falha ao criar o diretório base para plugins."; return 1; }
    mkdir -p "$WEB_PLUGIN_DIR" || { error_log "Falha ao criar o diretório web-plugins."; return 1; }
    mkdir -p "$DISCORD_PLUGIN_DIR" || { error_log "Falha ao criar o diretório discord-plugins."; return 1; }
    mkdir -p "$CS2_PLUGIN_DIR" || { error_log "Falha ao criar o diretório cs2-plugins."; return 1; }
    mkdir -p "$BOT_DIR" || { error_log "Falha ao criar o diretório do bot-discord."; return 1; }
    mkdir -p "$UPLOAD_DIR" || { error_log "Falha ao criar o diretório de uploads."; return 1; }
    mkdir -p "$DEMO_MANAGER_DIR" || { error_log "Falha ao criar o diretório do gerenciador de demos."; return 1; }
    mkdir -p "$BACKUP_DIR" || { error_log "Falha ao criar o diretório de backups."; return 1; }
    return 0
}

clone_or_update_repo() {
    local repo_url="$1"
    local target_dir="$2"
    local repo_name=$(basename "$repo_url" .git)

    if [ ! -d "$target_dir" ]; then
        log "📥 Clonando $repo_name para $target_dir..."
        git clone "$repo_url" "$target_dir" || { error_log "Falha ao clonar $repo_name."; return 1; }
    else
        log "🔄 Atualizando $repo_name em $target_dir..."
        cd "$target_dir" && git pull || { error_log "Falha ao atualizar $repo_name."; return 1; }
    fi
    return 0
}

update_all_plugins_and_bot() {
    log "🔄 Atualizando todos os plugins e o bot do Discord..."

    local success=true
    clone_or_update_repo "https://github.com/adamguedesmtm/web-plugins.git" "$WEB_PLUGIN_DIR" || success=false
    clone_or_update_repo "https://github.com/adamguedesmtm/discord-plugins.git" "$DISCORD_PLUGIN_DIR" || success=false
    clone_or_update_repo "https://github.com/adamguedesmtm/cs2-plugins.git" "$CS2_PLUGIN_DIR" || success=false
    clone_or_update_repo "$BOT_REPO" "$BOT_DIR" || success=false

    if [ "$success" = true ]; then
        log "✅ Todos os plugins e o bot foram atualizados com sucesso!"
    else
        error_log "Alguns plugins ou o bot não foram atualizados corretamente."
    fi
    progress_bar
}

configure_credentials() {
    log "🔑 Configurando credenciais sensíveis..."

    RCON_PASSWORD='agenciapicks'
    DISCORD_BOT_TOKEN='MTM0MTA3MTk2NjU0Mjc1ODAwOQ.Ge_cK1.aGpzLjrRFVfBaQEivyjQrTqVqkI-7zDOFIQIPA'
    STEAM_API_KEY='1F1623402CA92202C0FF3B65B79E6DD3'
    FREEDNS_USERNAME='agenciadns'
    FREEDNS_PASSWORD='fbMTnCaK'

    cat > /tmp/cs2_key.bin <<EOF
RCON_PASSWORD=$RCON_PASSWORD
DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN
STEAM_API_KEY=$STEAM_API_KEY
FREEDNS_USERNAME=$FREEDNS_USERNAME
FREEDNS_PASSWORD=$FREEDNS_PASSWORD
EOF

    openssl enc -aes-256-cbc -salt -in /tmp/cs2_key.bin -out "$CONFIG_FILE" -kfile "$MASTER_KEY" || { error_log "Falha ao criptografar credenciais."; exit 1; }
    shred -u /tmp/cs2_key.bin
    log "✅ Credenciais configuradas e criptografadas com sucesso."
    progress_bar
}

configure_backups() {
    log "💾 Configurando backups automáticos..."

    mkdir -p "$BACKUP_DIR" || { error_log "Falha ao criar diretório de backups."; return 1; }

    cat > /etc/cron.daily/cs2_backup <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d)

# Verificar espaço em disco
if [ \$(df "$BACKUP_DIR" | awk 'NR==2 {print \$4}') -lt 5242880 ]; then
    echo "Espaço insuficiente para backups" >> "$LOG_FILE"
    exit 1
fi

# Backup do servidor CS2
tar -czf "\$BACKUP_DIR/cs2_backup_\$DATE.tar.gz" "$CS2_DIR" 2>/dev/null

# Backup do bot do Discord
tar -czf "\$BACKUP_DIR/discord_bot_backup_\$DATE.tar.gz" "$BOT_DIR" 2>/dev/null

# Backup dos plugins
tar -czf "\$BACKUP_DIR/plugins_backup_\$DATE.tar.gz" "$PLUGIN_BASE_DIR" 2>/dev/null

# Limpar backups antigos (manter apenas os últimos 7 dias)
find "$BACKUP_DIR" -type f -name "*.tar.gz" -mtime +7 -delete
EOF

    chmod +x /etc/cron.daily/cs2_backup
    log "✅ Backups automáticos configurados."
    progress_bar
}

configure_logrotate() {
    log "📝 Configurando logrotate..."

    # Configurar logrotate para logs do sistema
    cat > /etc/logrotate.d/system <<EOF
/var/log/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root adm
}
EOF

    # Configurar logrotate para logs do Nginx
    cat > /etc/logrotate.d/nginx <<EOF
$WEB_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
}
EOF

    log "✅ Logrotate configurado com sucesso."
    progress_bar
}

configure_ssl() {
    log "🔐 Configurando SSL..."

    apt update && apt install -y certbot python3-certbot-nginx || { error_log "Falha ao instalar Certbot."; return 1; }

    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email contato@seuemail.com || { error_log "Falha ao configurar SSL."; return 1; }
    log "✅ SSL configurado com sucesso."
    progress_bar
}

setup_web() {
    log "🌐 Configurando web server..."

    apt update && apt install -y nginx || { error_log "Falha ao instalar Nginx."; return 1; }

    cat > /etc/nginx/sites-available/cs2stats <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    root $WEB_DIR;
    index index.php index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php-fpm.sock;
    }

    location ~ /\.ht {
        deny all;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/cs2stats /etc/nginx/sites-enabled/
    systemctl restart nginx || { error_log "Falha ao reiniciar Nginx."; return 1; }
    log "✅ Web server configurado com sucesso."
    progress_bar
}

setup_demo_upload() {
    log "📊 Configurando upload de demos..."

    cat > "$WEB_DIR/upload.php" <<EOF
<?php
header("Content-Type: application/json");

if (\$_SERVER['REQUEST_METHOD'] === 'POST' && isset(\$_FILES['demo'])) {
    \$allowedTypes = ['application/octet-stream'];
    if (!in_array(\$_FILES['demo']['type'], \$allowedTypes)) {
        http_response_code(400);
        echo json_encode(['status' => 'error', 'message' => 'Arquivo inválido. Apenas arquivos .dem são permitidos.']);
        exit;
    }

    \$target = "$UPLOAD_DIR/" . hash_file('sha256', \$_FILES['demo']['tmp_name']) . '.dem';

    if (move_uploaded_file(\$_FILES['demo']['tmp_name'], \$target)) {
        shell_exec("$DEMO_MANAGER_DIR/cs-demo-manager analyze --json \"\$target\"");
        echo json_encode(['status' => 'success', 'file' => \$target]);
    } else {
        http_response_code(500);
        echo json_encode(['status' => 'error', 'message' => 'Falha no upload.']);
    }
} else {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Solicitação inválida.']);
}
?>
EOF

    chown -R www-data:www-data "$WEB_DIR"
    chmod -R 755 "$WEB_DIR"
    log "✅ Upload de demos configurado com sucesso."
    progress_bar
}

configure_services() {
    log "⚙️ Configurando serviços systemd..."

    # Configurar serviço CS2
    cat > /etc/systemd/system/cs2.service <<EOF
[Unit]
Description=Counter-Strike 2 Server
After=network.target

[Service]
ExecStart=$CS2_DIR/srcds_run -game csgo -console -usercon +game_type 0 +game_mode 1 +mapgroup mg_active +map de_dust2 +sv_setsteamaccount \$STEAM_API_KEY
Restart=always
User=root
EnvironmentFile=/etc/cs2_config.env

[Install]
WantedBy=multi-user.target
EOF

    # Configurar serviço do bot do Discord
    cat > /etc/systemd/system/discord-bot.service <<EOF
[Unit]
Description=Discord Bot
After=network.target

[Service]
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/node index.js
Restart=always
User=root
EnvironmentFile=/etc/cs2_config.env

[Install]
WantedBy=multi-user.target
EOF

    # Configurar serviço CS Demo Manager
    cat > /etc/systemd/system/cs-demo-manager.service <<EOF
[Unit]
Description=CS Demo Manager
After=network.target

[Service]
ExecStart=$DEMO_MANAGER_DIR/index.js
Restart=always
User=root
EnvironmentFile=/etc/cs2_config.env

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable cs2.service
    systemctl start cs2.service || { error_log "Falha ao iniciar o serviço CS2."; return 1; }
    systemctl enable discord-bot.service
    systemctl start discord-bot.service || { error_log "Falha ao iniciar o serviço do bot."; return 1; }
    systemctl enable cs-demo-manager.service
    systemctl start cs-demo-manager.service || { error_log "Falha ao iniciar o serviço CS Demo Manager."; return 1; }
    log "✅ Serviços configurados e iniciados."
    progress_bar
}

update_system() {
    log "🔄 Atualizando sistema..."

    apt update && apt upgrade -y || { error_log "Falha ao atualizar o sistema."; return 1; }
    log "✅ Sistema atualizado com sucesso."
    progress_bar
}

install_cs_demo_manager() {
    log "🛠️ Instalando gerenciador de demos..."

    mkdir -p "$DEMO_MANAGER_DIR" || { error_log "Falha ao criar diretório do gerenciador de demos."; return 1; }
    cd "$DEMO_MANAGER_DIR"
    git clone https://github.com/adamguedesmtm/cs-demo-manager.git . || { error_log "Falha ao clonar gerenciador de demos."; return 1; }
    npm install || { error_log "Falha ao instalar dependências do gerenciador de demos."; return 1; }

    # Criar arquivo de configuração para CS Demo Manager
    cat > "$DEMO_MANAGER_DIR/config.json" <<EOF
{
    "uploadDir": "$UPLOAD_DIR",
    "analyzeCommand": "node index.js analyze --json"
}
EOF

    log "✅ Gerenciador de demos instalado e configurado com sucesso."
    progress_bar
}

configure_automatic_updates() {
    log "📅 Configurando atualizações automáticas..."

    apt update && apt install -y unattended-upgrades || { error_log "Falha ao instalar unattended-upgrades."; return 1; }

    # Configurar atualizações automáticas
    dpkg-reconfigure -f noninteractive unattended-upgrades || { error_log "Falha ao configurar atualizações automáticas."; return 1; }
    log "✅ Atualizações automáticas configuradas."
    progress_bar
}

show_final_info() {
    log "🎉 Configuração concluída!"

    log "⚠️ Verifique o arquivo de log para detalhes sobre possíveis erros: $LOG_FILE"
}

show_error_summary() {
    log "⚠️ Resumo de erros:"
    grep "\[ERRO\]" "$LOG_FILE" || log "✅ Nenhum erro crítico encontrado."
}

# --- Configuração de Credenciais no Início ---
configure_credentials

# --- Execução ---
[ "$EUID" -ne 0 ] && { log "❌ Execute como root"; exit 1; }
trap 'log "⚠️ Script interrompido!"; exit 130' INT TERM

TOTAL_STEPS=22
CURRENT_STEP=0
STEPS=("Atualizando sistema" "Configurando hostname" "Configurando timezone" "Configurando rede" "Configurando firewall" "Configurando SSH" "Instalando pacotes básicos" "Configurando Fail2Ban" "Atualizando DNS" "Instalando SteamCMD" "Instalando servidor CS2" "Instalando gerenciador de demos" "Configurando serviços" "Configurando SSL" "Configurando web" "Configurando upload de demos" "Configurando diretórios" "Atualizando plugins e bot" "Configurando credenciais" "Configurando backups" "Configurando logrotate" "Configurando atualizações automáticas")

(
    update_system || true
    configure_hostname || true
    configure_timezone || true
    configure_network || true
    configure_firewall || true
    configure_ssh || true
    install_dependencies || true
    setup_fail2ban || true
    update_freedns || true
    install_steamcmd || true
    install_cs2_server || true
    install_cs_demo_manager || true
    configure_services || true
    configure_ssl || true
    setup_web || true
    setup_demo_upload || true
    setup_directories || true
    update_all_plugins_and_bot || true
    configure_credentials || true
    configure_backups || true
    configure_logrotate || true
    configure_automatic_updates || true
    show_final_info
) 2>&1 | tee -a "$LOG_FILE"

show_error_summary


<?php
// db.php
// Conexão com o banco de dados SQLite

$dbPath = '/var/www/stats/stats.db';

try {
    $conn = new PDO("sqlite:$dbPath");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    echo "Erro na conexão: " . $e->getMessage();
    exit;
}

// Cria tabelas se não existirem
$conn->exec("
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    steam_id TEXT UNIQUE,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    headshots INTEGER DEFAULT 0,
    kd_ratio REAL GENERATED ALWAYS AS (kills / NULLIF(deaths, 0)) STORED
);

CREATE TABLE IF NOT EXISTS demos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS map_pool (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS active_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    score TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
");
?>

<?php
// upload.php
// Endpoint para upload de demos

include 'db.php';

$uploadDir = '/var/www/stats/demos/';
$logFile = '/var/www/stats/logs/upload.log';

if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}
if (!is_dir('/var/www/stats/logs')) {
    mkdir('/var/www/stats/logs', 0777, true);
}

function log_message($message, $logFile = '/var/www/stats/logs/upload.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['demo'])) {
    $demoFile = $uploadDir . basename($_FILES['demo']['name']);
    if (move_uploaded_file($_FILES['demo']['tmp_name'], $demoFile)) {
        // Salva o caminho do arquivo no banco de dados para processamento posterior
        $query = "INSERT INTO demos (file_path, status) VALUES (:file_path, 'pending')";
        $stmt = $conn->prepare($query);
        $stmt->bindParam(':file_path', $demoFile);
        $stmt->execute();

        log_message("Demo enviada com sucesso: {$demoFile}");
        echo json_encode(["mensagem" => "Demo enviada com sucesso.", "arquivo" => $demoFile]);
    } else {
        log_message("Falha ao enviar demo: {$_FILES['demo']['name']}");
        http_response_code(500);
        echo json_encode(["erro" => "Falha ao enviar demo."]);
    }
}
?>

<?php
// process_demos.php
// Script para processar demos em segundo plano usando o CS Demo Manager

include 'db.php';
$logFile = '/var/www/stats/logs/process.log';

function log_message($message, $logFile = '/var/www/stats/logs/process.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

$query = "SELECT * FROM demos WHERE status = 'pending' LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->execute();
$demo = $stmt->fetch(PDO::FETCH_ASSOC);

if ($demo) {
    $filePath = $demo['file_path'];
    $outputFile = str_replace('.dem', '.json', $filePath);

    // Processa o arquivo usando CS Demo Manager
    $command = "/caminho/para/cs-demo-manager --input {$filePath} --output {$outputFile}";
    exec($command, $output, $returnVar);

    if ($returnVar === 0) {
        // Lê o JSON gerado e salva no banco de dados
        $jsonData = file_get_contents($outputFile);
        $stats = json_decode($jsonData, true);

        foreach ($stats['players'] as $player) {
            $name = $conn->quote($player['name']);
            $kills = $player['kills'];
            $deaths = $player['deaths'];
            $headshots = $player['headshots'];

            $query = "INSERT INTO players (name, kills, deaths, headshots) 
                      VALUES ($name, $kills, $deaths, $headshots)
                      ON DUPLICATE KEY UPDATE 
                      kills = kills + VALUES(kills), 
                      deaths = deaths + VALUES(deaths), 
                      headshots = headshots + VALUES(headshots)";
            $conn->exec($query);
        }

        // Atualiza o status do arquivo
        $updateQuery = "UPDATE demos SET status = 'processed' WHERE id = :id";
        $updateStmt = $conn->prepare($updateQuery);
        $updateStmt->bindParam(':id', $demo['id']);
        $updateStmt->execute();

        log_message("Demo processada com sucesso: {$filePath}");
    } else {
        // Marca o arquivo como falha
        $updateQuery = "UPDATE demos SET status = 'failed' WHERE id = :id";
        $updateStmt = $conn->prepare($updateQuery);
        $updateStmt->bindParam(':id', $demo['id']);
        $updateStmt->execute();

        log_message("Falha ao processar demo: {$filePath}");
    }
}
?>

<?php
// api.php
// API para retornar estatísticas e outros dados

include 'db.php';

$action = $_GET['acao'];

function log_message($message, $logFile='/var/www/stats/logs/api.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

if ($action === 'get_player_stats') {
    $nome = $_GET['nome'];
    $query = "SELECT * FROM players WHERE nome = :nome";
    $stmt = $conn->prepare($query);
    $stmt->bindParam(':nome', $nome);
    $stmt->execute();
    $jogador = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($jogador) {
        log_message("Estatísticas solicitadas para jogador: {$jogador['nome']}");
        echo json_encode($jogador);
    } else {
        log_message("Jogador não encontrado: $nome");
        http_response_code(404);
        echo json_encode(["erro" => "Jogador não encontrado"]);
    }
} elseif ($action === 'get_rankings') {
    $query = "SELECT nome, kills, mortes, kd_ratio FROM players ORDER BY kd_ratio DESC LIMIT 10";
    $stmt = $conn->prepare($query);
    $stmt->execute();
    $jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);

    log_message("Ranking solicitado");
    echo json_encode(["jogadores" => $jogadores]);
} elseif ($action === 'get_last_match') {
    $query = "SELECT * FROM demos WHERE status = 'processed' ORDER BY id DESC LIMIT 1";
    $stmt = $conn->prepare($query);
    $stmt->execute();
    $demo = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($demo) {
        log_message("Última partida solicitada");
        echo json_encode($demo);
    } else {
        log_message("Nenhuma partida processada ainda");
        http_response_code(404);
        echo json_encode(["erro" => "Nenhuma partida processada ainda"]);
    }
} elseif ($action === 'get_active_server') {
    $query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1";
    $stmt = $conn->prepare($query);
    $stmt->execute();
    $servidorAtivo = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($servidorAtivo) {
        log_message("Informações do servidor ativo solicitadas");
        echo json_encode($servidorAtivo);
    } else {
        log_message("Nenhum servidor ativo");
        http_response_code(404);
        echo json_encode(["erro" => "Nenhum servidor ativo"]);
    }
}
?>

<?php
// player.php
// Página individual do jogador com estatísticas e gráficos

include 'db.php';

$nome = $_GET['nome'];
$query = "SELECT * FROM players WHERE nome = :nome";
$stmt = $conn->prepare($query);
$stmt->bindParam(':nome', $nome);
$stmt->execute();
$jogador = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$jogador) {
    die("Jogador não encontrado.");
}
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil do Jogador</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Perfil do Jogador: <?= htmlspecialchars($jogador['nome']) ?></h1>
        <p><strong>Kills:</strong> <?= $jogador['kills'] ?></p>
        <p><strong>Mortes:</strong> <?= $jogador['mortes'] ?></p>
        <p><strong>K/D Ratio:</strong> <?= number_format($jogador['kd_ratio'], 2) ?></p>
        <p><strong>Headshots:</strong> <?= $jogador['headshots'] ?></p>

        <h2>Estatísticas ao Longo do Tempo</h2>
        <canvas id="statsChart" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('statsChart').getContext('2d');
            const statsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Kills', 'Mortes', 'Headshots'],
                    datasets: [{
                        label: 'Estatísticas',
                        data: [<?= $jogador['kills'] ?>, <?= $jogador['mortes'] ?>, <?= $jogador['headshots'] ?>],
                        backgroundColor: ['#007BFF', '#FF5733', '#28A745'],
                        borderColor: ['#007BFF', '#FF5733', '#28A745'],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
    </div>
</body>
</html>
?>

<?php
// rankings.php
// Página de ranking global

include 'db.php';

$query = "SELECT nome, kills, mortes, kd_ratio FROM players ORDER BY kd_ratio DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ranking Global</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Ranking Global</h1>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Jogador</th>
                    <th>Kills</th>
                    <th>Mortes</th>
                    <th>K/D Ratio</th>
                    <th>Headshots</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($jogadores as $indice => $jogador): ?>
                <tr>
                    <td><?= $indice + 1 ?></td>
                    <td><?= htmlspecialchars($jogador['nome']) ?></td>
                    <td><?= $jogador['kills'] ?></td>
                    <td><?= $jogador['mortes'] ?></td>
                    <td><?= number_format($jogador['kd_ratio'], 2) ?></td>
                    <td><?= $jogador['headshots'] ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
?>

<?php
// dashboard.php
// Painel administrativo com estatísticas

include 'db.php';

$query = "SELECT nome, kills, mortes, kd_ratio FROM players ORDER BY kd_ratio DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$jogadores = $stmt->fetchAll(PDO::FETCH_ASSOC);

$query = "SELECT * FROM demos ORDER BY id DESC LIMIT 10";
$stmt = $conn->prepare($query);
$stmt->execute();
$demos = $stmt->fetchAll(PDO::FETCH_ASSOC);

$query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1";
$stmt = $conn->prepare($query);
$stmt->execute();
$servidorAtivo = $stmt->fetch(PDO::FETCH_ASSOC);
?>

<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Dashboard de Estatísticas</h1>

        <h2>Top 10 Jogadores</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Jogador</th>
                    <th>Kills</th>
                    <th>Mortes</th>
                    <th>K/D Ratio</th>
                    <th>Headshots</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($jogadores as $indice => $jogador): ?>
                <tr>
                    <td><?= $indice + 1 ?></td>
                    <td><?= htmlspecialchars($jogador['nome']) ?></td>
                    <td><?= $jogador['kills'] ?></td>
                    <td><?= $jogador['mortes'] ?></td>
                    <td><?= number_format($jogador['kd_ratio'], 2) ?></td>
                    <td><?= $jogador['headshots'] ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>

        <h2>Demos Recentes</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Arquivo</th>
                    <th>Status</th>
                    <th>Data de Processamento</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($demos as $demo): ?>
                <tr>
                    <td><?= $demo['id'] ?></td>
                    <td><?= htmlspecialchars($demo['file_path']) ?></td>
                    <td><?= htmlspecialchars($demo['status']) ?></td>
                    <td><?= htmlspecialchars($demo['processed_at']) ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>

        <h2>Servidor Ativo</h2>
        <?php if ($servidorAtivo): ?>
            <p>Categoria: <?= htmlspecialchars($servidorAtivo['categoria']) ?></p>
            <p>Status: <?= htmlspecialchars($servidorAtivo['status']) ?></p>
            <p>Placar: <?= htmlspecialchars($servidorAtivo['score']) ?></p>
            <p>Iniciado em: <?= htmlspecialchars($servidorAtivo['started_at']) ?></p>
        <?php else: ?>
            <p>Nenhum servidor ativo.</p>
        <?php endif; ?>

        <h2>Estatísticas Gerais</h2>
        <canvas id="generalChart" width="400" height="200"></canvas>
        <script>
            const ctx = document.getElementById('generalChart').getContext('2d');
            const generalChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Kills', 'Mortes', 'Headshots'],
                    datasets: [
                        {
                            label: 'Média',
                            data: [<?= array_sum(array_column($jogadores, 'kills')) / count($jogadores) ?>, <?= array_sum(array_column($jogadores, 'mortes')) / count($jogadores) ?>, <?= array_sum(array_column($jogadores, 'headshots')) / count($jogadores) ?>],
                            backgroundColor: ['#007BFF', '#FF5733', '#28A745'],
                            borderColor: ['#007BFF', '#FF5733', '#28A745'],
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        </script>
    </div>
</body>
</html>
?>

/* style.css */
/* Estilo CSS */

body {
    font-family: 'Roboto', sans-serif;
    background-color: #f9f9f9;
    color: #333333;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1, h2, h3 {
    color: #007BFF;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
}

table th {
    background-color: #007BFF;
    color: white;
}

button {
    background-color: #007BFF;
    color: white;
    border: none;
    padding: 10px 20px;
    cursor: pointer;
    border-radius: 5px;
}

button:hover {
    background-color: #0056b3;
}
?>

// scripts.js
// JavaScript para interatividade (gráficos, heatmaps, etc.)

// Exemplo de script para gráficos
// Este arquivo pode ser usado no futuro para adicionar mais interatividade

// Exemplo de script para gráficos
document.addEventListener('DOMContentLoaded', function() {
    // Adicione scripts JavaScript aqui
});
?>

// bot.py
// Script do bot do Discord

import discord
from discord.ext import commands, tasks
import requests
import os
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import subprocess

# Configuração do bot
TOKEN = 'SEU_TOKEN_AQUI'
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
TEXT_CHANNEL_ID = 123456789012345678  # ID do canal de texto para mensagens do bot

# IDs dos canais de voz
VOICE_CHANNELS = {
    "5v5": 123456789012345678,  # ID do canal de voz "5v5"
    "2v2": 234567890123456789,  # ID do canal de voz "2v2"
    "Retakes": 345678901234567890  # ID do canal de voz "Retakes"
}

# Variáveis globais
signup_messages = {categoria: None for categoria in VOICE_CHANNELS.keys()}
signed_up_players = {categoria: [] for categoria in VOICE_CHANNELS.keys()}
matches = {}
MAPS = ["de_dust2", "de_mirage", "de_inferno", "de_nuke", "de_overpass", "de_ancient", "de_vertigo"]
ADMIN_IDS = [123456789012345678]  # IDs dos administradores
MAX_PLAYERS = 10

# Conexão com o banco de dados SQLite
DB_PATH = '/var/www/stats/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    log_message("Bot conectado com sucesso.")

@bot.command()
async def signup(ctx, categoria: str):
    global signup_messages, signed_up_players

    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if ctx.author.name not in signed_up_players[categoria]:
        signed_up_players[categoria].append(ctx.author.name)
        await ctx.send(f"{ctx.author.name} foi adicionado à lista de jogadores para {categoria}!")
    else:
        await ctx.send(f"{ctx.author.name}, você já está na lista para {categoria}!")

@bot.command()
async def list_players(ctx, categoria: str):
    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if signed_up_players[categoria]:
        player_list = "\n".join(signed_up_players[categoria])
        await ctx.send(f"Jogadores inscritos para {categoria}:\n{player_list}")
    else:
        await ctx.send(f"Nenhum jogador inscrito ainda para {categoria}.")

@bot.command()
async def create_teams(ctx, categoria: str):
    global signed_up_players

    if categoria not in signed_up_players:
        await ctx.send("Categoria inválida. Use '5v5', '2v2' ou 'Retakes'.")
        return

    if len(signed_up_players[categoria]) < MAX_PLAYERS:
        await ctx.send(f"Não há jogadores suficientes para criar equipes em {categoria}.")
        return

    stats = {jogador: {"kd_ratio": random.uniform(0.5, 3.0)} for jogador in signed_up_players[categoria]}
    sorted_players = sorted(signed_up_players[categoria], key=lambda x: stats[x]['kd_ratio'], reverse=True)
    team1 = sorted_players[:5]
    team2 = sorted_players[5:]

    team1_list = "\n".join(team1)
    team2_list = "\n".join(team2)
    await ctx.send(f"Equipes criadas para {categoria}:\n\n**Time 1:**\n{team1_list}\n\n**Time 2:**\n{team2_list}")

    # Limpa a lista de jogadores inscritos
    signed_up_players[categoria].clear()

@bot.command()
async def ban_map(ctx, categoria: str, map_name: str):
    if categoria not in matches:
        matches[categoria] = {"banned_maps": []}
    elif "banned_maps" not in matches[categoria]:
        matches[categoria]["banned_maps"] = []

    if map_name.lower() in MAPS:
        if map_name.lower() not in matches[categoria]["banned_maps"]:
            matches[categoria]["banned_maps"].append(map_name.lower())
            await ctx.send(f"Mapa {map_name} foi banido para {categoria}.")
        else:
            await ctx.send(f"{map_name} já foi banido.")
    else:
        await ctx.send(f"{map_name} não está na lista de mapas disponíveis.")

@bot.command()
async def select_final_map(ctx, categoria: str):
    if categoria not in matches or "banned_maps" not in matches[categoria]:
        await ctx.send(f"Nenhum mapa foi banido ainda para {categoria}.")
        return

    available_maps = [mapa for mapa in MAPS if mapa not in matches[categoria]["banned_maps"]]
    if available_maps:
        final_map = random.choice(available_maps)
        await ctx.send(f"O mapa final para {categoria} é: {final_map}")
        # Salva o mapa final no banco de dados
        conn = get_db_connection()
        query = "UPDATE active_servers SET map = ? WHERE categoria = ? AND status = 'running'"
        conn.execute(query, (final_map, categoria))
        conn.commit()
        conn.close()
    else:
        await ctx.send(f"Todos os mapas foram banidos para {categoria}!")

@bot.command()
async def stats(ctx, jogador_nome: str):
    conn = get_db_connection()
    query = "SELECT * FROM players WHERE nome = ?"
    jogador = conn.execute(query, (jogador_nome,)).fetchone()
    conn.close()

    if jogador:
        stats = {
            "nome": jogador['nome'],
            "kills": jogador['kills'],
            "mortes": jogador['mortes'],
            "kd_ratio": round(jogador['kd_ratio'], 2),
            "headshots": jogador['headshots'],
            "avatar_url": "https://example.com/avatar.png"  # Substitua pelo URL real do avatar
        }
        card_path = generate_player_card(jogador_nome, stats)

        with open(card_path, 'rb') as f:
            await ctx.send(file=discord.File(f, filename=f"{jogador_nome}_card.png"))
    else:
        await ctx.send("Jogador não encontrado ou erro ao buscar estatísticas.")

@bot.command()
async def lastmatch(ctx):
    conn = get_db_connection()
    query = "SELECT * FROM demos WHERE status = 'processed' ORDER BY id DESC LIMIT 1"
    demo = conn.execute(query).fetchone()
    conn.close()

    if demo:
        embed = discord.Embed(title="Última Partida", color=discord.Color.green())
        embed.add_field(name="Arquivo", value=demo['file_path'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Nenhuma partida processada ainda.")

@bot.command()
async def top10(ctx):
    conn = get_db_connection()
    query = "SELECT * FROM players ORDER BY kd_ratio DESC LIMIT 10"
    jogadores = conn.execute(query).fetchall()
    conn.close()

    if jogadores:
        leaderboard = "\n".join([f"{i+1}. {jogador['nome']}: {jogador['kd_ratio']}" for i, jogador in enumerate(jogadores)])
        await ctx.send(f"Top 10 Jogadores:\n{leaderboard}")
    else:
        await ctx.send("Nenhum jogador registrado ainda.")

@bot.command()
async def upload_demo(ctx, attachment: discord.Attachment):
    if not attachment.filename.endswith('.dem'):
        await ctx.send("Por favor, envie um arquivo .dem válido.")
        return

    # Salva o arquivo no servidor
    demo_path = f"/var/www/stats/demos/{attachment.filename}"
    await attachment.save(demo_path)

    # Adiciona à fila de processamento
    conn = get_db_connection()
    query = "INSERT INTO demos (file_path, status) VALUES (?, 'pending')"
    conn.execute(query, (demo_path,))
    conn.commit()
    conn.close()

    await ctx.send(f"Arquivo {attachment.filename} enviado com sucesso! Aguardando processamento.")

@bot.command()
async def update_map_pool(ctx, categoria: str, *mapas: str):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("Você não tem permissão para atualizar a map pool.")
        return

    conn = get_db_connection()
    query = "DELETE FROM map_pool WHERE categoria = ?"
    conn.execute(query, (categoria,))
    conn.commit()

    for mapa in mapas:
        insert_query = "INSERT INTO map_pool (map_name, categoria) VALUES (?, ?)"
        conn.execute(insert_query, (mapa, categoria))
    conn.commit()
    conn.close()

    await ctx.send(f"Map pool para {categoria} atualizada com sucesso.")

@bot.event
async def on_voice_state_update(member, before, after):
    for categoria, voice_channel_id in VOICE_CHANNELS.items():
        voice_channel = bot.get_channel(voice_channel_id)
        text_channel = bot.get_channel(TEXT_CHANNEL_ID)

        if voice_channel is None or text_channel is None:
            log_message(f"Canal não encontrado para a categoria {categoria}!")
            continue

        membros_no_canal = len(voice_channel.members)
        try:
            await voice_channel.edit(name=f"{categoria} ({membros_no_canal}/{MAX_PLAYERS})")
            log_message(f"Nome do canal atualizado para: {categoria} ({membros_no_canal}/{MAX_PLAYERS})")
        except Exception as e:
            log_message(f"Erro ao atualizar o nome do canal: {e}")

        if membros_no_canal == MAX_PLAYERS:
            await check_active_server(text_channel, categoria)

async def check_active_server(text_channel, categoria):
    conn = get_db_connection()
    query = "SELECT * FROM active_servers WHERE status = 'running' LIMIT 1"
    servidor_ativo = conn.execute(query).fetchone()
    conn.close()

    if servidor_ativo:
        await text_channel.send(f"Um servidor já está ativo para a categoria {servidor_ativo['categoria']}.\nPlacar: {servidor_ativo['score']}")
    else:
        await start_server(text_channel, categoria)

async def start_server(text_channel, categoria):
    conn = get_db_connection()
    query = "INSERT INTO active_servers (categoria, status, score) VALUES (?, 'running', '0-0')"
    conn.execute(query, (categoria,))
    conn.commit()
    conn.close()

    await text_channel.send(f"Servidor para {categoria} iniciado! Placar inicial: 0-0")

    # Inicia o servidor de CS2 usando RCON ou outro método
    start_cs2_server(categoria)

def start_cs2_server(categoria):
    # Exemplo de comando para iniciar o servidor de CS2
    # Substitua pelo comando real para iniciar o servidor
    if categoria == "5v5":
        command = "/caminho/para/start_cs2_5v5.sh"
    elif categoria == "2v2":
        command = "/caminho/para/start_cs2_2v2.sh"
    elif categoria == "Retakes":
        command = "/caminho/para/start_cs2_retakes.sh"
    
    subprocess.Popen(command, shell=True)

def generate_player_card(jogador_nome, stats):
    # Carrega o avatar do jogador
    avatar_url = stats.get("avatar_url")
    response = requests.get(avatar_url)
    avatar = Image.open(io.BytesIO(response.content)).resize((100, 100))

    # Cria a imagem
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Adiciona o avatar
    img.paste(avatar, (20, 20))

    # Adiciona texto
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    draw.text((140, 20), f"Nome: {jogador_nome}", fill=(0, 0, 0), font=font)
    draw.text((140, 50), f"Kills: {stats['kills']}", fill=(0, 0, 0), font=font)
    draw.text((140, 80), f"Mortes: {stats['mortes']}", fill=(0, 0, 0), font=font)
    draw.text((140, 110), f"K/D: {stats['kd_ratio']}", fill=(0, 0, 0), font=font)
    draw.text((140, 140), f"Headshots: {stats['headshots']}", fill=(0, 0, 0), font=font)

    # Salva a imagem
    card_path = f"/var/www/stats/player_cards/{jogador_nome}_card.png"
    img.save(card_path)
    return card_path

def log_message(mensagem, logFile='/var/www/stats/logs/general.log'):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(logFile, 'a') as file:
        file.write(f"[{timestamp}] {mensagem}\n")

# Executa o bot
bot.run(TOKEN)
?>

// gs_server.py
// Servidor Flask para processar dados do GSI

from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = '/var/www/stats/stats.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/gsi', methods=['POST'])
def gsi():
    data = request.json
    conn = get_db_connection()
    # Processa os dados recebidos e salva no banco de dados
    # Exemplo: Salvar informações de kills, mortes, headshots, etc.
    conn.close()
    return jsonify({"status": "sucesso"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
?>

// Dockerfile
// Dockerfile para o servidor web

# Dockerfile
FROM php:8.1-apache

# Instalar dependências
RUN apt-get update && apt-get install -y \
    libapache2-mod-php \
    php-sqlite3 \
    git \
    curl \
    unzip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Configurar Apache
COPY . /var/www/html
RUN chown -R www-data:www-data /var/www/html

# Habilitar mod_rewrite
RUN a2enmod rewrite

# Reiniciar Apache
CMD ["apache2-foreground"]
?>

// docker-compose.yml
// Orquestração de serviços

version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:80"
    volumes:
      - ./logs:/var/www/stats/logs
      - ./demos:/var/www/stats/demos
      - ./player_cards:/var/www/stats/player_cards
    environment:
      - DB_PATH=/var/www/stats/stats.db

  bot:
    image: python:3.10-slim
    command: python /app/bot.py
    volumes:
      - ./logs:/var/www/stats/logs
      - ./demos:/var/www/stats/demos
      - ./player_cards:/var/www/stats/player_cards
    environment:
      - TOKEN=SEU_TOKEN_AQUI
      - DB_PATH=/var/www/stats/stats.db
    depends_on:
      - web

  gs_server:
    image: python:3.10-slim
    command: python /app/gs_server.py
    ports:
      - "5000:5000"
    volumes:
      - ./logs:/var/www/stats/logs
      - ./demos:/var/www/stats/demos
      - ./player_cards:/var/www/stats/player_cards
    environment:
      - DB_PATH=/var/www/stats/stats.db
    depends_on:
      - web
?>

-- db.sql
-- Script SQL para criar o banco de dados

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    steam_id TEXT UNIQUE,
    kills INTEGER DEFAULT 0,
    mortes INTEGER DEFAULT 0,
    headshots INTEGER DEFAULT 0,
    kd_ratio REAL GENERATED ALWAYS AS (kills / NULLIF(mortes, 0)) STORED
);

CREATE TABLE IF NOT EXISTS demos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS map_pool (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_name TEXT NOT NULL,
    categoria TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS active_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    score TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
?>
