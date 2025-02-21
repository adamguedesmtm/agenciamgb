"""
Queue Manager
Author: adamguedesmtm
Created: 2025-02-21 13:56:20
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from .logger import Logger
from .metrics import MetricsManager

class QueueManager:
    def __init__(self,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.logger = logger or Logger('queue_manager')
        self.metrics = metrics
        self.queues = {
            'competitive': {
                'players': [],
                'min_players': 10,
                'max_players': 10,
                'timeout': 300  # 5 minutos
            },
            'wingman': {
                'players': [],
                'min_players': 4,
                'max_players': 4,
                'timeout': 180  # 3 minutos
            },
            'retake': {
                'players': [],
                'min_players': 6,
                'max_players': 10,
                'timeout': 120  # 2 minutos
            }
        }
        self.player_queues: Dict[int, str] = {}  # Mapear jogador -> fila
        self.queue_timeouts: Dict[int, datetime] = {}  # Timeouts dos jogadores

    async def add_player(self, player_id: int, queue_type: str, player_name: str) -> Optional[int]:
        """Adicionar jogador à fila"""
        try:
            if queue_type not in self.queues:
                raise ValueError(f"Tipo de fila inválido: {queue_type}")

            queue = self.queues[queue_type]

            # Verificar se jogador já está em alguma fila
            if player_id in self.player_queues:
                return None

            # Verificar se fila está cheia
            if len(queue['players']) >= queue['max_players']:
                return None

            # Adicionar jogador
            player = {
                'id': player_id,
                'name': player_name,
                'joined_at': datetime.utcnow()
            }
            queue['players'].append(player)
            
            # Registrar em qual fila o jogador está
            self.player_queues[player_id] = queue_type
            
            # Definir timeout
            self.queue_timeouts[player_id] = datetime.utcnow() + \
                                           timedelta(seconds=queue['timeout'])

            if self.metrics:
                await self.metrics.update_queue_count(
                    queue_type,
                    len(queue['players'])
                )

            return len(queue['players'])

        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar jogador: {e}")
            return None

    async def remove_player(self, player_id: int, queue_type: str) -> bool:
        """Remover jogador da fila"""
        try:
            if queue_type not in self.queues:
                return False

            queue = self.queues[queue_type]

            # Encontrar e remover jogador
            for i, player in enumerate(queue['players']):
                if player['id'] == player_id:
                    queue['players'].pop(i)
                    
                    # Limpar registros do jogador
                    if player_id in self.player_queues:
                        del self.player_queues[player_id]
                    if player_id in self.queue_timeouts:
                        del self.queue_timeouts[player_id]

                    if self.metrics:
                        await self.metrics.update_queue_count(
                            queue_type,
                            len(queue['players'])
                        )

                    return True

            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover jogador: {e}")
            return False

    async def get_queue_info(self, queue_type: str) -> Optional[Dict]:
        """Obter informações da fila"""
        try:
            if queue_type not in self.queues:
                return None

            queue = self.queues[queue_type]
            
            # Remover jogadores com timeout
            now = datetime.utcnow()
            for player in queue['players'][:]:  # Copiar lista para iteração
                if player['id'] in self.queue_timeouts:
                    if now > self.queue_timeouts[player['id']]:
                        await self.remove_player(player['id'], queue_type)

            return {
                'type': queue_type,
                'players': queue['players'],
                'min_players': queue['min_players'],
                'max_players': queue['max_players'],
                'timeout': queue['timeout']
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da fila: {e}")
            return None

    async def check_ready(self, queue_type: str) -> bool:
        """Verificar se fila está pronta para começar"""
        try:
            if queue_type not in self.queues:
                return False

            queue = self.queues[queue_type]
            return len(queue['players']) >= queue['min_players']

        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar fila: {e}")
            return False

    async def clear_queue(self, queue_type: str) -> bool:
        """Limpar fila específica"""
        try:
            if queue_type not in self.queues:
                return False

            queue = self.queues[queue_type]
            
            # Remover todos os jogadores
            for player in queue['players']:
                if player['id'] in self.player_queues:
                    del self.player_queues[player['id']]
                if player['id'] in self.queue_timeouts:
                    del self.queue_timeouts[player['id']]

            queue['players'].clear()

            if self.metrics:
                await self.metrics.update_queue_count(queue_type, 0)

            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar fila: {e}")
            return False

    def is_in_queue(self, player_id: int) -> bool:
        """Verificar se jogador está em alguma fila"""
        return player_id in self.player_queues

    async def get_player_queue(self, player_id: int) -> Optional[str]:
        """Obter fila em que o jogador está"""
        return self.player_queues.get(player_id)

    async def extend_timeout(self, player_id: int, seconds: int = 60) -> bool:
        """Estender timeout do jogador"""
        try:
            if player_id not in self.queue_timeouts:
                return False

            self.queue_timeouts[player_id] += timedelta(seconds=seconds)
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao estender timeout: {e}")
            return False