"""
Database Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:13:08
"""

import asyncpg
import os
import json
from datetime import datetime
from .logger import Logger

class Database:
    def __init__(self):
        self.logger = Logger('database')
        self.pool = None
        self.db_config = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', 5432)
        }

    async def connect(self):
        """Estabelecer conexão com o banco de dados"""
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            await self._init_tables()
            self.logger.logger.info("Conexão com banco de dados estabelecida")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao conectar ao banco: {e}")
            return False

    async def _init_tables(self):
        """Inicializar tabelas do banco de dados"""
        try:
            async with self.pool.acquire() as conn:
                # Tabela de matches
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS matches (
                        id SERIAL PRIMARY KEY,
                        match_id VARCHAR(50) UNIQUE NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        map_name VARCHAR(50),
                        score_ct INTEGER DEFAULT 0,
                        score_t INTEGER DEFAULT 0,
                        winner VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Tabela de players
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS players (
                        id SERIAL PRIMARY KEY,
                        steam_id VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(100),
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_matches INTEGER DEFAULT 0,
                        total_wins INTEGER DEFAULT 0,
                        total_kills INTEGER DEFAULT 0,
                        total_deaths INTEGER DEFAULT 0
                    )
                """)

                # Tabela de match_players
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS match_players (
                        id SERIAL PRIMARY KEY,
                        match_id INTEGER REFERENCES matches(id),
                        player_id INTEGER REFERENCES players(id),
                        team VARCHAR(10),
                        kills INTEGER DEFAULT 0,
                        deaths INTEGER DEFAULT 0,
                        assists INTEGER DEFAULT 0,
                        score INTEGER DEFAULT 0,
                        mvps INTEGER DEFAULT 0,
                        UNIQUE(match_id, player_id)
                    )
                """)

                # Tabela de bans
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS bans (
                        id SERIAL PRIMARY KEY,
                        steam_id VARCHAR(50) NOT NULL,
                        reason TEXT,
                        admin_id VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                """)

                # Tabela de logs
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS server_logs (
                        id SERIAL PRIMARY KEY,
                        type VARCHAR(20) NOT NULL,
                        message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Tabela de configurações
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS server_config (
                        key VARCHAR(50) PRIMARY KEY,
                        value JSONB,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                self.logger.logger.info("Tabelas inicializadas com sucesso")

        except Exception as e:
            self.logger.logger.error(f"Erro ao inicializar tabelas: {e}")
            raise

    async def add_player(self, steam_id: str, name: str):
        """Adicionar ou atualizar jogador"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO players (steam_id, name)
                    VALUES ($1, $2)
                    ON CONFLICT (steam_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        last_seen = CURRENT_TIMESTAMP
                    RETURNING id
                """
                return await conn.fetchval(query, steam_id, name)
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar jogador: {e}")
            return None

    async def update_player_stats(self, player_id: int, stats: dict):
        """Atualizar estatísticas do jogador"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE players
                    SET
                        total_matches = total_matches + 1,
                        total_wins = total_wins + $2,
                        total_kills = total_kills + $3,
                        total_deaths = total_deaths + $4,
                        last_seen = CURRENT_TIMESTAMP
                    WHERE id = $1
                """
                await conn.execute(
                    query,
                    player_id,
                    stats.get('win', 0),
                    stats.get('kills', 0),
                    stats.get('deaths', 0)
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar estatísticas: {e}")

    async def create_match(self, match_data: dict):
        """Criar nova partida"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO matches
                    (match_id, start_time, map_name)
                    VALUES ($1, $2, $3)
                    RETURNING id
                """
                return await conn.fetchval(
                    query,
                    match_data['match_id'],
                    match_data['start_time'],
                    match_data.get('map_name', 'unknown')
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar partida: {e}")
            return None

    async def update_match(self, match_id: str, match_data: dict):
        """Atualizar dados da partida"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE matches
                    SET
                        end_time = $2,
                        score_ct = $3,
                        score_t = $4,
                        winner = $5
                    WHERE match_id = $1
                """
                await conn.execute(
                    query,
                    match_id,
                    match_data.get('end_time'),
                    match_data.get('score_ct', 0),
                    match_data.get('score_t', 0),
                    match_data.get('winner')
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar partida: {e}")

    async def add_match_player(self, match_id: int, player_data: dict):
        """Adicionar jogador à partida"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO match_players
                    (match_id, player_id, team, kills, deaths, assists, score, mvps)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                await conn.execute(
                    query,
                    match_id,
                    player_data['player_id'],
                    player_data.get('team'),
                    player_data.get('kills', 0),
                    player_data.get('deaths', 0),
                    player_data.get('assists', 0),
                    player_data.get('score', 0),
                    player_data.get('mvps', 0)
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar jogador à partida: {e}")

    async def add_ban(self, ban_data: dict):
        """Adicionar ban"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO bans
                    (steam_id, reason, admin_id, expires_at)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                """
                return await conn.fetchval(
                    query,
                    ban_data['steam_id'],
                    ban_data.get('reason'),
                    ban_data.get('admin_id'),
                    ban_data.get('expires_at')
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar ban: {e}")
            return None

    async def get_player_stats(self, steam_id: str):
        """Obter estatísticas do jogador"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT
                        p.*,
                        COUNT(DISTINCT mp.match_id) as matches_played,
                        SUM(mp.kills) as total_match_kills,
                        SUM(mp.deaths) as total_match_deaths,
                        SUM(mp.assists) as total_assists,
                        SUM(mp.mvps) as total_mvps
                    FROM players p
                    LEFT JOIN match_players mp ON p.id = mp.player_id
                    WHERE p.steam_id = $1
                    GROUP BY p.id
                """
                return await conn.fetchrow(query, steam_id)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return None

    async def get_match_history(self, steam_id: str, limit: int = 10):
        """Obter histórico de partidas do jogador"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT
                        m.*,
                        mp.team,
                        mp.kills,
                        mp.deaths,
                        mp.assists,
                        mp.score,
                        mp.mvps
                    FROM matches m
                    JOIN match_players mp ON m.id = mp.match_id
                    JOIN players p ON mp.player_id = p.id
                    WHERE p.steam_id = $1
                    ORDER BY m.start_time DESC
                    LIMIT $2
                """
                return await conn.fetch(query, steam_id, limit)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter histórico: {e}")
            return []

    async def check_ban(self, steam_id: str):
        """Verificar se jogador está banido"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT *
                    FROM bans
                    WHERE steam_id = $1
                    AND active = TRUE
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """
                return await conn.fetchrow(query, steam_id)
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar ban: {e}")
            return None

    async def save_config(self, key: str, value: dict):
        """Salvar configuração"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO server_config (key, value)
                    VALUES ($1, $2)
                    ON CONFLICT (key)
                    DO UPDATE SET
                        value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                """
                await conn.execute(query, key, json.dumps(value))
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar configuração: {e}")

    async def get_config(self, key: str):
        """Obter configuração"""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT value FROM server_config WHERE key = $1"
                result = await conn.fetchval(query, key)
                return json.loads(result) if result else None
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter configuração: {e}")
            return None

    async def add_log(self, log_type: str, message: str):
        """Adicionar log"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO server_logs (type, message)
                    VALUES ($1, $2)
                """
                await conn.execute(query, log_type, message)
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar log: {e}")
