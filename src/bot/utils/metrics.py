"""
Metrics Manager
Author: adamguedesmtm
Created: 2025-02-21 13:49:37
"""

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import start_http_server
from typing import Dict, Optional
from .logger import Logger

class MetricsManager:
    def __init__(self, port: int = 9090):
        self.logger = Logger('metrics')
        self.port = port
        
        # Métricas do bot
        self.commands_total = Counter(
            'bot_commands_total',
            'Total de comandos executados',
            ['command']
        )
        
        self.queue_players = Gauge(
            'queue_players',
            'Número de jogadores na fila',
            ['queue_type']
        )
        
        self.matches_total = Counter(
            'matches_total',
            'Total de partidas iniciadas',
            ['match_type']
        )
        
        self.match_duration = Histogram(
            'match_duration_seconds',
            'Duração das partidas',
            ['match_type']
        )
        
        self.server_status = Gauge(
            'server_status',
            'Status do servidor',
            ['server_type']
        )
        
        self.player_stats = Counter(
            'player_stats',
            'Estatísticas dos jogadores',
            ['stat_type', 'player_id']
        )
        
        # Iniciar servidor de métricas
        try:
            start_http_server(port)
            self.logger.logger.info(f"Servidor de métricas iniciado na porta {port}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar servidor de métricas: {e}")

    async def record_command(self, command: str):
        """Registrar comando executado"""
        try:
            self.commands_total.labels(command=command).inc()
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar comando: {e}")

    async def update_queue_count(self, queue_type: str, count: int):
        """Atualizar contador de jogadores na fila"""
        try:
            self.queue_players.labels(queue_type=queue_type).set(count)
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar contagem da fila: {e}")

    async def record_match_start(self, match_type: str):
        """Registrar início de partida"""
        try:
            self.matches_total.labels(match_type=match_type).inc()
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar início de partida: {e}")

    async def record_match_duration(self, match_type: str, duration: float):
        """Registrar duração de partida"""
        try:
            self.match_duration.labels(match_type=match_type).observe(duration)
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar duração de partida: {e}")

    async def update_server_status(self, server_type: str, status: int):
        """Atualizar status do servidor"""
        try:
            self.server_status.labels(server_type=server_type).set(status)
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar status do servidor: {e}")

    async def record_player_stat(self, stat_type: str, player_id: str, value: float = 1):
        """Registrar estatística de jogador"""
        try:
            self.player_stats.labels(
                stat_type=stat_type,
                player_id=player_id
            ).inc(value)
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar estatística: {e}")