-- config/db.sql
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