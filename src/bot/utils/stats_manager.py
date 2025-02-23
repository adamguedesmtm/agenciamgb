"""
Stats Database Manager
Author: adamguedesmtm
Created: 2025-02-21 13:58:35
"""

import asyncpg
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .logger import Logger
from .metrics import MetricsManager

class StatsManager:
    def __init__(self, 
                 db_config: Dict,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.db_config = db_config
        self.logger = logger or Logger('stats_manager')
        self.metrics = metrics
        self.pool = None

    async def init(self):
        """Inicializar conexão com banco de dados"""
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            await self._create_tables()
            self.logger.logger.info("Conexão com banco de dados estabelecida")
        except Exception as e:
            self.logger.logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    async def _create_tables(self):
        """Criar tabelas necessárias"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id BIGINT PRIMARY KEY,
                    discord_id BIGINT UNIQUE,
                    name VARCHAR(64),
                    steam_id VARCHAR(32) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY,
                    match_type VARCHAR(16),
                    map VARCHAR(32),
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    winner_team VARCHAR(16),
                    score_team1 INTEGER,
                    score_team2 INTEGER
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    player_id BIGINT REFERENCES players(id),
                    match_id INTEGER REFERENCES matches(id),
                    team VARCHAR(16),
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    assists INTEGER DEFAULT 0,
                    headshots INTEGER DEFAULT 0,
                    score INTEGER DEFAULT 0,
                    mvps INTEGER DEFAULT 0,
                    PRIMARY KEY (player_id, match_id)
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS player_ratings (
                    player_id BIGINT REFERENCES players(id),
                    rating_type VARCHAR(16),
                    rating FLOAT DEFAULT 1000,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (player_id, rating_type)
                )
            """)

    async def register_player(self, discord_id: int, name: str, steam_id: str) -> bool:
        """Registrar novo jogador"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO players (discord_id, name, steam_id)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (discord_id) DO UPDATE
                    SET name = $2, steam_id = $3
                """, discord_id, name, steam_id)
                return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar jogador: {e}")
            return False

    async def record_match(self, match_data: Dict) -> Optional[int]:
        """Registrar partida completa"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Inserir partida
                    match_id = await conn.fetchval("""
                        INSERT INTO matches (
                            match_type, map, start_time, end_time,
                            winner_team, score_team1, score_team2
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                    """, match_data['type'], match_data['map'],
                        match_data['start_time'], match_data['end_time'],
                        match_data['winner_team'], 
                        match_data['score_team1'],
                        match_data['score_team2'])

                    # Registrar stats dos jogadores
                    for player_stats in match_data['player_stats']:
                        await conn.execute("""
                            INSERT INTO player_stats (
                                player_id, match_id, team, kills, deaths,
                                assists, headshots, score, mvps
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """, player_stats['player_id'], match_id,
                            player_stats['team'], player_stats['kills'],
                            player_stats['deaths'], player_stats['assists'],
                            player_stats['headshots'], player_stats['score'],
                            player_stats['mvps'])

                    # Atualizar ratings
                    await self._update_ratings(conn, match_data)

                    if self.metrics:
                        await self.metrics.record_command('match_recorded')

                    return match_id

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar partida: {e}")
            return None

    async def _update_ratings(self, conn, match_data: Dict):
        """Atualizar ratings dos jogadores"""
        try:
            for player_stats in match_data['player_stats']:
                # Calcular novo rating
                rating_change = self._calculate_rating_change(
                    player_stats,
                    match_data['winner_team'] == player_stats['team']
                )

                # Atualizar na base
                await conn.execute("""
                    INSERT INTO player_ratings (
                        player_id, rating_type, rating, games_played, wins
                    ) VALUES ($1, $2, 1000 + $3, 1, $4)
                    ON CONFLICT (player_id, rating_type) DO UPDATE
                    SET rating = player_ratings.rating + $3,
                        games_played = player_ratings.games_played + 1,
                        wins = player_ratings.wins + $4,
                        last_update = CURRENT_TIMESTAMP
                """, player_stats['player_id'], match_data['type'],
                    rating_change, 
                    1 if match_data['winner_team'] == player_stats['team'] else 0)

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar ratings: {e}")

    def _calculate_rating_change(self, stats: Dict, won: bool) -> float:
        """Calcular mudança de rating baseado na performance"""
        try:
            base_change = 20 if won else -20
            
            # Modificadores baseados na performance
            kd_ratio = stats['kills'] / max(1, stats['deaths'])
            kd_modifier = (kd_ratio - 1.0) * 5
            
            impact_modifier = (stats['mvps'] * 2) + \
                            (stats['headshots'] / max(1, stats['kills']) * 5)
            
            return base_change + kd_modifier + impact_modifier

        except Exception as e:
            self.logger.logger.error(f"Erro ao calcular rating: {e}")
            return 0

    async def get_player_stats(self, player_id: int) -> Optional[Dict]:
        """Obter estatísticas completas do jogador"""
        try:
            async with self.pool.acquire() as conn:
                stats = {}
                
                # Ratings
                ratings = await conn.fetch("""
                    SELECT rating_type, rating, games_played, wins
                    FROM player_ratings
                    WHERE player_id = $1
                """, player_id)
                
                stats['ratings'] = {
                    r['rating_type']: {
                        'rating': r['rating'],
                        'games': r['games_played'],
                        'wins': r['wins']
                    } for r in ratings
                }

                # Estatísticas gerais
                overall = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_matches,
                        SUM(CASE WHEN team = winner_team THEN 1 ELSE 0 END) as wins,
                        SUM(kills) as total_kills,
                        SUM(deaths) as total_deaths,
                        SUM(assists) as total_assists,
                        SUM(headshots) as total_headshots,
                        SUM(mvps) as total_mvps
                    FROM player_stats ps
                    JOIN matches m ON ps.match_id = m.id
                    WHERE player_id = $1
                """, player_id)

                if overall:
                    stats.update({
                        'matches': overall['total_matches'],
                        'wins': overall['wins'],
                        'kills': overall['total_kills'],
                        'deaths': overall['total_deaths'],
                        'assists': overall['total_assists'],
                        'headshots': overall['total_headshots'],
                        'mvps': overall['total_mvps']
                    })

                # Mapas mais jogados
                maps = await conn.fetch("""
                    SELECT map, COUNT(*) as count
                    FROM player_stats ps
                    JOIN matches m ON ps.match_id = m.id
                    WHERE player_id = $1
                    GROUP BY map
                    ORDER BY count DESC
                    LIMIT 3
                """, player_id)

                stats['most_played_maps'] = [
                    (m['map'], m['count']) for m in maps
                ]

                return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats do jogador: {e}")
            return None

    async def get_top_players_by_map(self, map_name: str, limit: int = 5) -> List[Dict]:
        """Buscar melhores jogadores por mapa."""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT 
                        p.name AS player_name,
                        ps.kills,
                        ps.deaths,
                        ps.headshots,
                        ps.mvps
                    FROM player_stats ps
                    JOIN players p ON ps.player_id = p.id
                    WHERE ps.map = $1
                    ORDER BY ps.kills DESC, ps.headshots DESC
                    LIMIT $2
                """, map_name, limit)

                return [
                    {
                        "name": r["player_name"],
                        "kills": r["kills"],
                        "deaths": r["deaths"],
                        "headshots": r["headshots"],
                        "mvps": r["mvps"]
                    }
                    for r in results
                ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao buscar top jogadores por mapa: {e}")
            return []

    async def get_leaderboard(self, rating_type: str, limit: int = 10) -> List[Dict]:
        """Obter ranking dos jogadores"""
        try:
            async with self.pool.acquire() as conn:
                leaders = await conn.fetch("""
                    SELECT 
                        p.name,
                        pr.rating,
                        pr.games_played,
                        pr.wins
                    FROM player_ratings pr
                    JOIN players p ON pr.player_id = p.id
                    WHERE pr.rating_type = $1
                    ORDER BY pr.rating DESC
                    LIMIT $2
                """, rating_type, limit)

                return [
                    {
                        'name': l['name'],
                        'rating': round(l['rating'], 2),
                        'games': l['games_played'],
                        'wins': l['wins']
                    } for l in leaders
                ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter leaderboard: {e}")
            return []
        
    async def get_rank_info(self, rating: float) -> Dict:
        """Obter informações sobre o rank atual."""
        ranks = [
            {"name": "Bronze", "min_rating": 800, "icon": "🥉", "next_rank": "Silver", "points_to_next": 1000 - rating},
            {"name": "Silver", "min_rating": 1000, "icon": "🥈", "next_rank": "Gold", "points_to_next": 1200 - rating},
            {"name": "Gold", "min_rating": 1200, "icon": "🏆", "next_rank": "Platinum", "points_to_next": 1500 - rating},
            {"name": "Platinum", "min_rating": 1500, "icon": "✨", "next_rank": "Diamond", "points_to_next": 1800 - rating},
            {"name": "Diamond", "min_rating": 1800, "icon": "💎", "next_rank": "Elite", "points_to_next": 2200 - rating},
            {"name": "Elite", "min_rating": 2200, "icon": "👑", "next_rank": None, "points_to_next": 0}
        ]

        for rank in ranks:
            if rating >= rank["min_rating"]:
                return {
                    "name": rank["name"],
                    "rating": rating,
                    "icon": rank["icon"],
                    "next_rank": rank["next_rank"],
                    "points_to_next": max(rank["points_to_next"], 0),
                    "progress": ((rating - rank["min_rating"]) / (rank.get("points_to_next", 1000))) * 100
                }

        return {"name": "Unranked", "rating": rating, "icon": "❓", "next_rank": "Bronze", "points_to_next": 800 - rating, "progress": 0}