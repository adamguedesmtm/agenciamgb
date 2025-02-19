CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kills INTEGER,
    deaths INTEGER,
    kd_ratio REAL,
    headshots INTEGER
);

CREATE TABLE demos (
    id INTEGER PRIMARY KEY,
    player_id INTEGER,
    demo_file TEXT,
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE TABLE map_pool (
    id INTEGER PRIMARY KEY,
    map_name TEXT
);

CREATE TABLE active_servers (
    id INTEGER PRIMARY KEY,
    server_name TEXT,
    status TEXT
);