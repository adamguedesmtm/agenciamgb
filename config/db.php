<?php
// config/db.php
// Conexão com o banco de dados SQLite
// Função para descriptografar uma string

function decrypt_string($encrypted_string, $encryption_key) {
    $data = base64_decode($encrypted_string);
    $iv = substr($data, 0, 16);
    $encrypted_data = substr($data, 16);
    return openssl_decrypt($encrypted_data, 'aes-256-cbc', $encryption_key, 0, $iv);
}

// Carregar as credenciais do .env
$dotenv = [];
if (file_exists('/var/www/agenciamgb/.env')) {
    $dotenv_lines = file('/var/www/agenciamgb/.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($dotenv_lines as $line) {
        list($key, $value) = explode('=', $line, 2);
        $dotenv[$key] = trim($value);
    }
}

// Verificar se todas as credenciais foram carregadas
$required_keys = ['ENCRYPTION_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASS', 'DISCORD_BOT_TOKEN', 'STEAM_API_KEY'];
foreach ($required_keys as $key) {
    if (!isset($dotenv[$key])) {
        die("Erro: Credencial $key não encontrada no arquivo .env");
    }
}

// Descriptografar as credenciais
$encryption_key = $dotenv['ENCRYPTION_KEY'];
$db_host = decrypt_string($dotenv['DB_HOST'], $encryption_key);
$db_name = decrypt_string($dotenv['DB_NAME'], $encryption_key);
$db_user = decrypt_string($dotenv['DB_USER'], $encryption_key);
$db_pass = decrypt_string($dotenv['DB_PASS'], $encryption_key);
$discord_bot_token = decrypt_string($dotenv['DISCORD_BOT_TOKEN'], $encryption_key);
$steam_api_key = decrypt_string($dotenv['STEAM_API_KEY'], $encryption_key);

// Conexão com o banco de dados SQLite
$dbPath = '/var/www/agenciamgb/storage/logs/stats.db';

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
    nome TEXT NOT NULL,
    steam_id TEXT UNIQUE,
    kills INTEGER DEFAULT 0,
    mortes INTEGER DEFAULT 0,
    headshots INTEGER DEFAULT 0,
    kd_ratio REAL GENERATED ALWAYS AS (kills / NULLIF(mortes, 0)) STORED,
    assists INTEGER DEFAULT 0,
    tactical_kills INTEGER DEFAULT 0,
    flank_kills INTEGER DEFAULT 0,
    entry_kills INTEGER DEFAULT 0,
    first_seconds_kills INTEGER DEFAULT 0,
    duels_initiated INTEGER DEFAULT 0,
    awp_kills INTEGER DEFAULT 0,
    awp_purchases INTEGER DEFAULT 0,
    headshot_percentage REAL DEFAULT 0,
    defensive_multi_kills INTEGER DEFAULT 0,
    clutch_wins INTEGER DEFAULT 0,
    survival_rate REAL DEFAULT 0,
    grenade_damage INTEGER DEFAULT 0,
    blinded_enemies INTEGER DEFAULT 0,
    molotov_damage INTEGER DEFAULT 0,
    he_kills INTEGER DEFAULT 0,
    backstab_kills INTEGER DEFAULT 0,
    control_zone_kills INTEGER DEFAULT 0,
    stationary_kills INTEGER DEFAULT 0,
    rotation_time REAL DEFAULT 0,
    eco_rounds_won INTEGER DEFAULT 0,
    pistol_rounds_won INTEGER DEFAULT 0,
    money_saved INTEGER DEFAULT 0,
    total_damage_taken INTEGER DEFAULT 0,
    lowest_kills INTEGER DEFAULT 0,
    bot_eco_deaths INTEGER DEFAULT 0,
    first_kill_deaths INTEGER DEFAULT 0,
    inactive_time REAL DEFAULT 0,
    missed_shots INTEGER DEFAULT 0,
    clutch_losses INTEGER DEFAULT 0,
    last_alive_first_die INTEGER DEFAULT 0,
    no_trade_deaths INTEGER DEFAULT 0,
    missed_before_hit INTEGER DEFAULT 0,
    awp_noscope_misses INTEGER DEFAULT 0,
    leg_shots INTEGER DEFAULT 0,
    wasted_shots INTEGER DEFAULT 0,
    fake_defuse_deaths INTEGER DEFAULT 0,
    wandering_time REAL DEFAULT 0,
    self_blinded INTEGER DEFAULT 0,
    teamkills INTEGER DEFAULT 0,
    exploded_by_c4 INTEGER DEFAULT 0,
    nade_damage_taken INTEGER DEFAULT 0,
    elo INTEGER DEFAULT 1000
);
");

$conn->exec("
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    emoji TEXT,
    UNIQUE(user_id, role)
);
");

$conn->exec("
CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demo_id INTEGER,
    player_id INTEGER,
    kills INTEGER DEFAULT 0,
    mortes INTEGER DEFAULT 0,
    headshots INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    kd_ratio REAL GENERATED ALWAYS AS (kills / NULLIF(mortes, 0)) STORED,
    tactical_kills INTEGER DEFAULT 0,
    flank_kills INTEGER DEFAULT 0,
    entry_kills INTEGER DEFAULT 0,
    first_seconds_kills INTEGER DEFAULT 0,
    duels_initiated INTEGER DEFAULT 0,
    awp_kills INTEGER DEFAULT 0,
    awp_purchases INTEGER DEFAULT 0,
    headshot_percentage REAL DEFAULT 0,
    defensive_multi_kills INTEGER DEFAULT 0,
    clutch_wins INTEGER DEFAULT 0,
    survival_rate REAL DEFAULT 0,
    grenade_damage INTEGER DEFAULT 0,
    blinded_enemies INTEGER DEFAULT 0,
    molotov_damage INTEGER DEFAULT 0,
    he_kills INTEGER DEFAULT 0,
    backstab_kills INTEGER DEFAULT 0,
    control_zone_kills INTEGER DEFAULT 0,
    stationary_kills INTEGER DEFAULT 0,
    rotation_time REAL DEFAULT 0,
    eco_rounds_won INTEGER DEFAULT 0,
    pistol_rounds_won INTEGER DEFAULT 0,
    money_saved INTEGER DEFAULT 0,
    total_damage_taken INTEGER DEFAULT 0,
    lowest_kills INTEGER DEFAULT 0,
    bot_eco_deaths INTEGER DEFAULT 0,
    first_kill_deaths INTEGER DEFAULT 0,
    inactive_time REAL DEFAULT 0,
    missed_shots INTEGER DEFAULT 0,
    clutch_losses INTEGER DEFAULT 0,
    last_alive_first_die INTEGER DEFAULT 0,
    no_trade_deaths INTEGER DEFAULT 0,
    missed_before_hit INTEGER DEFAULT 0,
    awp_noscope_misses INTEGER DEFAULT 0,
    leg_shots INTEGER DEFAULT 0,
    wasted_shots INTEGER DEFAULT 0,
    fake defuse_deaths INTEGER DEFAULT 0,
    wandering_time REAL DEFAULT 0,
    self_blinded INTEGER DEFAULT 0,
    teamkills INTEGER DEFAULT 0,
    exploded_by_c4 INTEGER DEFAULT 0,
    nade_damage_taken INTEGER DEFAULT 0,
    FOREIGN KEY (demo_id) REFERENCES demos (id),
    FOREIGN KEY (player_id) REFERENCES players (id)
);
");

$conn->exec("
CREATE TABLE IF NOT EXISTS heatmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    map_name TEXT NOT NULL,
    heatmap_path TEXT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players (id)
);
");

function log_message($message, $logFile = '/var/www/agenciamgb/storage/logs/general.log') {
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
}

function assign_unique_roles($user_id, $nome, $stats) {
    global $conn;

    // Define as roles únicas com base nas estatísticas e emojis
    $roles = [
        "In-Game Leader" => ["value" => $stats['assists'], "emoji" => "👑"],
        "Tactical Genius" => ["value" => $stats['tactical_kills'], "emoji" => "💡"],
        "Strategist" => ["value" => $stats['flank_kills'], "emoji" => "🗺️"],
        "Entry King" => ["value" => $stats['entry_kills'], "emoji" => "🔑"],
        "Rush Master" => ["value" => $stats['first_seconds_kills'], "emoji" => "🏃‍♂️"],
        "Fearless Fragger" => ["value" => $stats['duels_initiated'], "emoji" => "🗡️"],
        "AWP Master" => ["value" => $stats['awp_kills'], "emoji" => "狙"],
        "AWP Thief" => ["value" => $stats['awp_purchases'], "emoji" => "💰"],
        "Headshot Machine" => ["value" => $stats['headshot_percentage'], "emoji" => "💥"],
        "The Wall" => ["value" => $stats['defensive_multi_kills'], "emoji" => "🛡️"],
        "Clutch God" => ["value" => $stats['clutch_wins'], "emoji" => "💪"],
        "Survivor" => ["value" => $stats['survival_rate'], "emoji" => "🧍‍♂️"],
        "Utility King" => ["value" => $stats['grenade_damage'], "emoji" => "💣"],
        "Flashbang King" => ["value" => $stats['blinded_enemies'], "emoji" => "⚡"],
        "Molotov Magician" => ["value" => $stats['molotov_damage'], "emoji" => "⚗️"],
        "Grenade Master" => ["value" => $stats['he_kills'], "emoji" => "🔥"],
        "Silent Killer" => ["value" => $stats['backstab_kills'], "emoji" => "👻"],
        "Connector King" => ["value" => $stats['control_zone_kills'], "emoji" => "📍"],
        "Camp King" => ["value" => $stats['stationary_kills'], "emoji" => "🌲"],
        "Speedster" => ["value" => $stats['rotation_time'], "emoji" => "💨"],
        "Eco King" => ["value" => $stats['eco_rounds_won'], "emoji" => " Đề"],
        "Pistol Expert" => ["value" => $stats['pistol_rounds_won'], "emoji" => "🔫"],
        "Money Saver" => ["value" => $stats['money_saved'], "emoji" => "💸"],
        "Bullet Sponge" => ["value" => $stats['total_damage_taken'], "emoji" => "🤕"],
        "Silver Elite" => ["value" => $stats['lowest_kills'], "emoji" => "🥈"],
        "Bot Eco" => ["value" => $stats['bot_eco_deaths'], "emoji" => "🤖"],
        "Entry Feeder" => ["value" => $stats['first_kill_deaths'], "emoji" => "新人玩家"],
        "CS Tourist" => ["value" => $stats['inactive_time'], "emoji" => "🚶‍♂️"],
        "Wall Sprayer" => ["value" => $stats['missed_shots'], "emoji" => "🔫"],
        "1vX Choker" => ["value" => $stats['clutch_losses'], "emoji" => "💔"],
        "Last Alive, First to Die" => ["value" => $stats['last_alive_first_die'], "emoji" => "😱"],
        "Baited Again" => ["value" => $stats['no_trade_deaths'], "emoji" => "🐟"],
        "Whiffmaster" => ["value" => $stats['missed_before_hit'], "emoji" => "💨"],
        "AWP No-Scope Enjoyer" => ["value" => $stats['awp_noscope_misses'], "emoji" => "🤷‍♂️"],
        "Leg Shot Lord" => ["value" => $stats['leg_shots'], "emoji" => "🦵"],
        "Can't Spray, Won't Spray" => ["value" => $stats['wasted_shots'], "emoji" => "💦"],
        "Fake Defuse Believer" => ["value" => $stats['fake defuse_deaths'], "emoji" => "🎩"],
        "Lost on the Map" => ["value" => $stats['wandering_time'], "emoji" => "🗺️"],
        "Flash Myself Pro" => ["value" => $stats['self_blinded'], "emoji" => "👁️‍🗨️"],
        "Terrorist CT" => ["value" => $stats['teamkills'], "emoji" => "😡"],
        "Bomberman" => ["value" => $stats['exploded_by_c4'], "emoji" => "💣"],
        "Nade Magnet" => ["value" => $stats['nade_damage_taken'], "emoji" => "💫"]
    ];

    // Remove todas as roles existentes para o jogador
    $deleteQuery = "DELETE FROM roles WHERE user_id = :user_id";
    $deleteStmt = $conn->prepare($deleteQuery);
    $deleteStmt->bindParam(':user_id', $user_id);
    $deleteStmt->execute();

    // Atribui roles únicas com base nas estatísticas
    foreach ($roles as $role => $data) {
        $value = $data['value'];
        $emoji = $data['emoji'];

        if ($value !== null) {
            $insertQuery = "INSERT INTO roles (user_id, role, emoji) VALUES (:user_id, :role, :emoji)";
            $insertStmt = $conn->prepare($insertQuery);
            $insertStmt->bindParam(':user_id', $user_id);
            $insertStmt->bindParam(':role', $role);
            $insertStmt->bindParam(':emoji', $emoji);
            $insertStmt->execute();

            log_message("Role atribuída para $nome: $emoji $role");
        }
    }
}

function assign_generic_roles($user_id, $nome, $stats) {
    global $conn;

    // Define as roles genéricas com base nas estatísticas e emojis
    $roles = [
        "Top Killer" => ["value" => $stats['kills'], "emoji" => "🏆"],
        "Top Mortes" => ["value" => $stats['mortes'], "emoji" => "☠️"],
        "Top Headshots" => ["value" => $stats['headshots'], "emoji" => "🎯"],
        "Top KD Ratio" => ["value" => $stats['kd_ratio'], "emoji" => "📈"]
    ];

    // Remove todas as roles genéricas existentes para o jogador
    $deleteQuery = "DELETE FROM roles WHERE user_id = :user_id AND role IN ('Top Killer', 'Top Mortes', 'Top Headshots', 'Top KD Ratio')";
    $deleteStmt = $conn->prepare($deleteQuery);
    $deleteStmt->bindParam(':user_id', $user_id);
    $deleteStmt->execute();

    // Atribui roles genéricas com base nas estatísticas
    foreach ($roles as $role => $data) {
        $value = $data['value'];
        $emoji = $data['emoji'];

        if ($value !== null) {
            $insertQuery = "INSERT INTO roles (user_id, role, emoji) VALUES (:user_id, :role, :emoji)";
            $insertStmt = $conn->prepare($insertQuery);
            $insertStmt->bindParam(':user_id', $user_id);
            $insertStmt->bindParam(':role', $role);
            $insertStmt->bindParam(':emoji', $emoji);
            $insertStmt->execute();

            log_message("Role genérica atribuída para $nome: $emoji $role");
        }
    }

    // Calcula o novo elo do jogador
    $newElo = calculate_elo($currentElo, $kills, $mortes);

    // Atualiza o elo do jogador no banco de dados
    $updateEloQuery = "UPDATE players SET elo = :elo WHERE id = :player_id";
    $updateEloStmt = $conn->prepare($updateEloQuery);
    $updateEloStmt->bindParam(':elo', $newElo);
    $updateEloStmt->bindParam(':player_id', $playerId);
    $updateEloStmt->execute();

    log_message("Elo atualizado para jogador $nome: $currentElo -> $newElo");
}

function generate_heatmap($player_id, $map_name, $heatmap_data) {
    global $conn;

    $heatmap_dir = '/var/www/agenciamgb/storage/player_cards/';
    if (!is_dir($heatmap_dir)) {
        mkdir($heatmap_dir, 0777, true);
    }

    $heatmap_path = $heatmap_dir . "heatmap_{$player_id}_{$map_name}.png";

    // Gera o heatmap usando as bibliotecas necessárias (ex: GD Library)
    // Aqui está um exemplo simplificado de como gerar um heatmap
    $image = imagecreatetruecolor(1024, 512);
    $background_color = imagecolorallocate($image, 255, 255, 255);
    imagefill($image, 0, 0, $background_color);

    // Exemplo de plotagem de pontos no heatmap
    foreach ($heatmap_data as $point) {
        $x = $point['x'];
        $y = $point['y'];
        $color = imagecolorallocate($image, 255, 0, 0);
        imagesetpixel($image, $x, $y, $color);
    }

    imagepng($image, $heatmap_path);
    imagedestroy($image);

    // Insere o caminho do heatmap no banco de dados
    $insertQuery = "INSERT INTO heatmaps (player_id, map_name, heatmap_path) VALUES (:player_id, :map_name, :heatmap_path)";
    $insertStmt = $conn->prepare($insertQuery);
    $insertStmt->bindParam(':player_id', $player_id);
    $insertStmt->bindParam(':map_name', $map_name);
    $insertStmt->bindParam(':heatmap_path', $heatmap_path);
    $insertStmt->execute();

    log_message("Heatmap gerado e salvo para jogador $player_id no mapa $map_name: $heatmap_path");
}

function calculate_elo($currentElo, $kills, $mortes) {
    // Parâmetros para o cálculo do elo
    $baseEloGain = 10; // Elo base ganho por vitória
    $baseEloLoss = 10; // Elo base perdido por derrota
    $eloAdjustmentFactor = 0.01; // Fator de ajuste para elo baseado no desempenho

    // Cálculo do elo baseado no desempenho
    $eloChange = ($kills - $mortes) * $eloAdjustmentFactor;

    // Ajusta o elo baseado no desempenho
    if ($eloChange > 0) {
        // Vitória
        $newElo = $currentElo + ($baseEloGain + $eloChange);
    } else {
        // Derrota
        $newElo = $currentElo - ($baseEloLoss - $eloChange);
    }

    // Garante que o elo não seja negativo
    if ($newElo < 0) {
        $newElo = 0;
    }

    return $newElo;
}
?>