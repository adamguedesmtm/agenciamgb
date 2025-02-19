<?php
try {
    $conn = new PDO('sqlite:/var/www/stats/stats.db');
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