"""
Statistics Collector for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:24:21
"""

import asyncio
import json
import os
from datetime import datetime
from .logger import Logger
from .database import Database

class StatsCollector:
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('stats_collector')
        self.db = Database()
        self.stats_cache = {}
        
    async def collect_server_stats(self):
        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'players': await self._get_player_count(),
                'map': await self._get_current_map(),
                'performance': await self._get_server_performance(),
                'system': await self._get_system_stats()
            }
            
            await self._save_stats(stats)
            self.stats_cache = stats
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao coletar estatísticas: {e}")
            
    async def _get_player_count(self):
        try:
            # Implementar lógica real de contagem de players
            return {
                'total': 0,
                'ct': 0,
                't': 0,
                'spectators': 0
            }
        except:
            return {'total': 0, 'ct': 0, 't': 0, 'spectators': 0}
            
    async def _get_current_map(self):
        try:
            # Implementar lógica real de obtenção do mapa
            return {
                'name': 'de_mirage',
                'time_elapsed': 0,
                'score_ct': 0,
                'score_t': 0
            }
        except:
            return {'name': 'unknown', 'time_elapsed': 0, 'score_ct': 0, 'score_t': 0}
            
    async def _get_server_performance(self):
        try:
            return {
                'tickrate': 128,
                'fps': 128,
                'var': 0.5,
                'ping': 5
            }
        except:
            return {'tickrate': 0, 'fps': 0, 'var': 0, 'ping': 0}
            
    async def _get_system_stats(self):
        try:
            return {
                'cpu': os.getloadavg()[0],
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
                'network': {
                    'in': psutil.net_io_counters().bytes_recv,
                    'out': psutil.net_io_counters().bytes_sent
                }
            }
        except:
            return {'cpu': 0, 'memory': 0, 'disk': 0, 'network': {'in': 0, 'out': 0}}
            
    async def _save_stats(self, stats):
        try:
            query = """
                INSERT INTO server_stats 
                (timestamp, stats_data)
                VALUES ($1, $2)
            """
            await self.db.pool.execute(query, stats['timestamp'], json.dumps(stats))
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar estatísticas: {e}")

    async def get_stats_summary(self, period='day'):
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT stats_data->>'map') as maps_played,
                    AVG((stats_data->>'players'->>'total')::int) as avg_players,
                    MAX((stats_data->>'players'->>'total')::int) as max_players,
                    AVG((stats_data->>'system'->>'cpu')::float) as avg_cpu,
                    AVG((stats_data->>'system'->>'memory')::float) as avg_memory
                FROM server_stats
                WHERE timestamp > NOW() - INTERVAL '1 ' || $1
            """
            return await self.db.pool.fetchrow(query, period)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter resumo de estatísticas: {e}")
            return None