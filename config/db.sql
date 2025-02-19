-- Script SQL para criar o banco de dados

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

-- Adiciona emojis nas descrições das roles
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    emoji TEXT,
    UNIQUE(user_id, role)
);

-- Tabela para histórico de jogos
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