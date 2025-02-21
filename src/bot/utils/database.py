"""
Database Manager and Migrations
Author: adamguedesmtm
Created: 2025-02-21 14:16:08
"""

import asyncpg
from typing import Dict, Optional
from .logger import Logger

class DatabaseManager:
    def __init__(self, 
                 config: Dict,
                 logger: Optional[Logger] = None):
        self.config = config
        self.logger = logger or Logger('database')
        self.pool = None

    async def init(self):
        """Inicializar conexão com banco de dados e criar tabelas"""
        try:
            self.pool = await asyncpg.create_pool(**self.config)
            await self._run_migrations()
            self.logger.logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            self.logger.logger.error(f"Erro ao inicializar banco: {e}")
            raise

    async def _run_migrations(self):
        """Executar migrações do banco de dados"""
        async with self.pool.acquire() as conn:
            # Tabela de controle de versão
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Verificar última versão
            current_version = await conn.fetchval(
                "SELECT MAX(version) FROM migrations"
            ) or 0

            # Lista de migrações
            migrations = [
                self._create_base_tables,
                self._create_stats_tables,
                self._create_match_tables,
                self._create_demo_tables,
                self._create_role_tables
            ]

            # Executar migrações pendentes
            for version, migration in enumerate(migrations, start=1):
                if version > current_version:
                    self.logger.logger.info(f"Aplicando migração {version}...")
                    await migration(conn)
                    await conn.execute(
                        "INSERT INTO migrations (version) VALUES ($1)",
                        version
                    )

    async def _create_base_tables(self, conn):
        """Criar tabelas base"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id BIGINT PRIMARY KEY,
                discord_id BIGINT UNIQUE,
                steam_id VARCHAR(32) UNIQUE,
                name VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(32) UNIQUE,
                host VARCHAR(255),
                port INTEGER,
                rcon_password VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    async def _create_stats_tables(self, conn):
        """Criar tabelas de estatísticas"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id BIGINT REFERENCES players(id),
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                headshots INTEGER DEFAULT 0,
                shots_fired INTEGER DEFAULT 0,
                shots_hit INTEGER DEFAULT 0,
                damage_dealt BIGINT DEFAULT 0,
                damage_taken BIGINT DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                rounds_played INTEGER DEFAULT 0,
                rounds_won INTEGER DEFAULT 0,
                playtime_seconds BIGINT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS player_weapons (
                player_id BIGINT REFERENCES players(id),
                weapon VARCHAR(32),
                kills INTEGER DEFAULT 0,
                shots_fired INTEGER DEFAULT 0,
                shots_hit INTEGER DEFAULT 0,
                headshots INTEGER DEFAULT 0,
                damage_dealt BIGINT DEFAULT 0,
                PRIMARY KEY (player_id, weapon)
            )
        """)

    async def _create_match_tables(self, conn):
        """Criar tabelas de partidas"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                match_type VARCHAR(16),
                server_id INTEGER REFERENCES servers(id),
                map VARCHAR(32),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                winner_team VARCHAR(4),
                team1_score INTEGER,
                team2_score INTEGER,
                demo_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS match_players (
                match_id INTEGER REFERENCES matches(id),
                player_id BIGINT REFERENCES players(id),
                team VARCHAR(4),
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                damage BIGINT DEFAULT 0,
                headshots INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                ping_avg INTEGER DEFAULT 0,
                PRIMARY KEY (match_id, player_id)
            )
        """)

    async def _create_demo_tables(self, conn):
        """Criar tabelas para dados de demos"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS demo_stats (
                match_id INTEGER REFERENCES matches(id),
                player_id BIGINT REFERENCES players(id),
                round_number INTEGER,
                kill_count INTEGER DEFAULT 0,
                death_count INTEGER DEFAULT 0,
                assist_count INTEGER DEFAULT 0,
                headshot_count INTEGER DEFAULT 0,
                damage_dealt INTEGER DEFAULT 0,
                flash_duration FLOAT DEFAULT 0,
                flash_assists INTEGER DEFAULT 0,
                utility_damage INTEGER DEFAULT 0,
                enemies_flashed INTEGER DEFAULT 0,
                PRIMARY KEY (match_id, player_id, round_number)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS demo_positions (
                match_id INTEGER REFERENCES matches(id),
                round_number INTEGER,
                tick INTEGER,
                player_id BIGINT REFERENCES players(id),
                x FLOAT,
                y FLOAT,
                z FLOAT,
                view_x FLOAT,
                view_y FLOAT,
                health INTEGER,
                armor INTEGER,
                active_weapon VARCHAR(32),
                PRIMARY KEY (match_id, round_number, tick, player_id)
            )
        """)

    async def _create_role_tables(self, conn):
        """Criar tabelas para sistema de roles"""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS role_history (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(id),
                role_name VARCHAR(64),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                removed_at TIMESTAMP,
                is_unique BOOLEAN DEFAULT FALSE,
                position INTEGER,
                stat_value FLOAT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS role_stats (
                player_id BIGINT REFERENCES players(id),
                role_name VARCHAR(64),
                time_held BIGINT DEFAULT 0,
                times_earned INTEGER DEFAULT 0,
                last_earned TIMESTAMP,
                best_position INTEGER,
                highest_stat_value FLOAT,
                PRIMARY KEY (player_id, role_name)
            )
        """)

        # Índices para performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_stats_kills ON player_stats(kills DESC);
            CREATE INDEX IF NOT EXISTS idx_player_stats_headshots ON player_stats(headshots DESC);
            CREATE INDEX IF NOT EXISTS idx_match_players_score ON match_players(score DESC);
            CREATE INDEX IF NOT EXISTS idx_role_history_dates ON role_history(assigned_at, removed_at);
            CREATE INDEX IF NOT EXISTS idx_demo_positions_match ON demo_positions(match_id, round_number);
        """)

    async def close(self):
        """Fechar conexão com banco de dados"""
        if self.pool:
            await self.pool.close()