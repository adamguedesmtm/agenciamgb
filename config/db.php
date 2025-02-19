<?php
// config/db.php
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
    nade_damage_taken INTEGER DEFAULT 0
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
        "Fake Defuse Believer" => ["value" => $stats['fake_defuse_deaths'], "emoji" => "🎩"],
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
}

function insert_game_history($demo_id, $player_id, $stats) {
    global $conn;

    $kills = $stats['kills'];
    $mortes = $stats['deaths'];
    $headshots = $stats['headshots'];
    $assists = $stats['assists'];
    $tactical_kills = $stats['tactical_kills'];
    $flank_kills = $stats['flank_kills'];
    $entry_kills = $stats['entry_kills'];
    $first_seconds_kills = $stats['first_seconds_kills'];
    $duels_initiated = $stats['duels_initiated'];
    $awp_kills = $stats['awp_kills'];
    $awp_purchases = $stats['awp_purchases'];
    $headshot_percentage = $stats['headshot_percentage'];
    $defensive_multi_kills = $stats['defensive_multi_kills'];
    $clutch_wins = $stats['clutch_wins'];
    $survival_rate = $stats['survival_rate'];
    $grenade_damage = $stats['grenade_damage'];
    $blinded_enemies = $stats['blinded_enemies'];
    $molotov_damage = $stats['molotov_damage'];
    $he_kills = $stats['he_kills'];
    $backstab_kills = $stats['backstab_kills'];
    $control_zone_kills = $stats['control_zone_kills'];
    $stationary_kills = $stats['stationary_kills'];
    $rotation_time = $stats['rotation_time'];
    $eco_rounds_won = $stats['eco_rounds_won'];
    $pistol_rounds_won = $stats['pistol_rounds_won'];
    $money_saved = $stats['money_saved'];
    $total_damage_taken = $stats['total_damage_taken'];
    $lowest_kills = $stats['lowest_kills'];
    $bot_eco_deaths = $stats['bot_eco_deaths'];
    $first_kill_deaths = $stats['first_kill_deaths'];
    $inactive_time = $stats['inactive_time'];
    $missed_shots = $stats['missed_shots'];
    $clutch_losses = $stats['clutch_losses'];
    $last_alive_first_die = $stats['last_alive_first_die'];
    $no_trade_deaths = $stats['no_trade_deaths'];
    $missed_before_hit = $stats['missed_before_hit'];
    $awp_noscope_misses = $stats['awp_noscope_misses'];
    $leg_shots = $stats['leg_shots'];
    $wasted_shots = $stats['wasted_shots'];
    $fake_defuse_deaths = $stats['fake_defuse_deaths'];
    $wandering_time = $stats['wandering_time'];
    $self_blinded = $stats['self_blinded'];
    $teamkills = $stats['teamkills'];
    $exploded_by_c4 = $stats['exploded_by_c4'];
    $nade_damage_taken = $stats['nade_damage_taken'];

    $insertQuery = "INSERT INTO game_history (demo_id, player_id, kills, mortes, headshots, assists, tactical_kills, flank_kills, entry_kills, first_seconds_kills, duels_initiated, awp_kills, awp_purchases, headshot_percentage, defensive_multi_kills, clutch_wins, survival_rate, grenade_damage, blinded_enemies, molotov_damage, he_kills, backstab_kills, control_zone_kills, stationary_kills, rotation_time, eco_rounds_won, pistol_rounds_won, money_saved, total_damage_taken, lowest_kills, bot_eco_deaths, first_kill_deaths, inactive_time, missed_shots, clutch_losses, last_alive_first_die, no_trade_deaths, missed_before_hit, awp_noscope_misses, leg_shots, wasted_shots, fake_defuse_deaths, wandering_time, self_blinded, teamkills, exploded_by_c4, nade_damage_taken) VALUES (:demo_id, :player_id, :kills, :mortes, :headshots, :assists, :tactical_kills, :flank_kills, :entry_kills, :first_seconds_kills, :duels_initiated, :awp_kills, :awp_purchases, :headshot_percentage, :defensive_multi_kills, :clutch_wins, :survival_rate, :grenade_damage, :blinded_enemies, :molotov_damage, :he_kills, :backstab_kills, :control_zone_kills, :stationary_kills, :rotation_time, :eco_rounds_won, :pistol_rounds_won, :money_saved, :total_damage_taken, :lowest_kills, :bot_eco_deaths, :first_kill_deaths, :inactive_time, :missed_shots, :clutch_losses, :last_alive_first_die, :no_trade_deaths, :missed_before_hit, :awp_noscope_misses, :leg_shots, :wasted_shots, :fake_defuse_deaths, :wandering_time, :self_blinded, :teamkills, :exploded_by_c4, :nade_damage_taken)";
    $insertStmt = $conn->prepare($insertQuery);
    $insertStmt->bindParam(':demo_id', $demo_id);
    $insertStmt->bindParam(':player_id', $player_id);
    $insertStmt->bindParam(':kills', $kills);
    $insertStmt->bindParam(':mortes', $mortes);
    $insertStmt->bindParam(':headshots', $headshots);
    $insertStmt->bindParam(':assists', $assists);
    $insertStmt->bindParam(':tactical_kills', $tactical_kills);
    $insertStmt->bindParam(':flank_kills', $flank_kills);
    $insertStmt->bindParam(':entry_kills', $entry_kills);
    $insertStmt->bindParam(':first_seconds_kills', $first_seconds_kills);
    $insertStmt->bindParam(':duels_initiated', $duels_initiated);
    $insertStmt->bindParam(':awp_kills', $awp_kills);
    $insertStmt->bindParam(':awp_purchases', $awp_purchases);
    $insertStmt->bindParam(':headshot_percentage', $headshot_percentage);
    $insertStmt->bindParam(':defensive_multi_kills', $defensive_multi_kills);
    $insertStmt->bindParam(':clutch_wins', $clutch_wins);
    $insertStmt->bindParam(':survival_rate', $survival_rate);
    $insertStmt->bindParam(':grenade_damage', $grenade_damage);
    $insertStmt->bindParam(':blinded_enemies', $blinded_enemies);
    $insertStmt->bindParam(':molotov_damage', $molotov_damage);
    $insertStmt->bindParam(':he_kills', $he_kills);
    $insertStmt->bindParam(':backstab_kills', $backstab_kills);
    $insertStmt->bindParam(':control_zone_kills', $control_zone_kills);
    $insertStmt->bindParam(':stationary_kills', $stationary_kills);
    $insertStmt->bindParam(':rotation_time', $rotation_time);
    $insertStmt->bindParam(':eco_rounds_won', $eco_rounds_won);
    $insertStmt->bindParam(':pistol_rounds_won', $pistol_rounds_won);
    $insertStmt->bindParam(':money_saved', $money_saved);
    $insertStmt->bindParam(':total_damage_taken', $total_damage_taken);
    $insertStmt->bindParam(':lowest_kills', $lowest_kills);
    $insertStmt->bindParam(':bot_eco_deaths', $bot_eco_deaths);
    $insertStmt->bindParam(':first_kill_deaths', $first_kill_deaths);
    $insertStmt->bindParam(':inactive_time', $inactive_time);
    $insertStmt->bindParam(':missed_shots', $missed_shots);
    $insertStmt->bindParam(':clutch_losses', $clutch_losses);
    $insertStmt->bindParam(':last_alive_first_die', $last_alive_first_die);
    $insertStmt->bindParam(':no_trade_deaths', $no_trade_deaths);
    $insertStmt->bindParam(':missed_before_hit', $missed_before_hit);
    $insertStmt->bindParam(':awp_noscope_misses', $awp_noscope_misses);
    $insertStmt->bindParam(':leg_shots', $leg_shots);
    $insertStmt->bindParam(':wasted_shots', $wasted_shots);
    $insertStmt->bindParam(':fake_defuse_deaths', $fake_defuse_deaths);
    $insertStmt->bindParam(':wandering_time', $wandering_time);
    $insertStmt->bindParam(':self_blinded', $self_blinded);
    $insertStmt->bindParam(':teamkills', $teamkills);
    $insertStmt->bindParam(':exploded_by_c4', $exploded_by_c4);
    $insertStmt->bindParam(':nade_damage_taken', $nade_damage_taken);
    $insertStmt->execute();

    log_message("Histórico de jogo inserido para demo $demo_id e jogador $player_id");
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
?>