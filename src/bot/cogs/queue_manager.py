"""
Queue Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:25:06
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from .metrics import MetricsManager
from .logger import Logger

class QueueType(Enum):
    COMPETITIVE = "5v5"
    WINGMAN = "2v2"
    RETAKE = "retake"

class QueueManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('queue_manager')
        self.metrics = metrics_manager
        
        # Filas por tipo
        self._queues: Dict[QueueType, List[Dict]] = {
            QueueType.COMPETITIVE: [],  # 5v5
            QueueType.WINGMAN: [],      # 2v2
            QueueType.RETAKE: []        # Retake
        }
        
        # Limites por tipo
        self._queue_limits = {
            QueueType.COMPETITIVE: 10,  # 5v5 = 10 jogadores
            QueueType.WINGMAN: 4,       # 2v2 = 4 jogadores
            QueueType.RETAKE: 10        # Retake = máx 10
        }
        
        # Cache de últimos jogos por jogador
        self._recent_games: Dict[str, List[datetime]] = {}
        self._cooldown_minutes = 10  # Cooldown entre jogos
        
    async def add_player(self,
                        queue_type: QueueType,
                        player_id: str,
                        player_name: str,
                        rank: Optional[int] = None) -> Dict:
        """
        Adicionar jogador à fila
        
        Args:
            queue_type: Tipo de fila
            player_id: ID do jogador
            player_name: Nome do jogador
            rank: Rank opcional para matchmaking
            
        Returns:
            Status da adição
        """
        try:
            queue = self._queues[queue_type]
            
            # Verificar se já está em alguma fila
            for q in self._queues.values():
                if any(p['id'] == player_id for p in q):
                    return {
                        'success': False,
                        'message': 'Jogador já está em fila'
                    }
                    
            # Verificar cooldown
            if not self._can_queue(player_id):
                return {
                    'success': False,
                    'message': 'Aguarde o cooldown entre jogos'
                }
                
            # Verificar limite
            if len(queue) >= self._queue_limits[queue_type]:
                return {
                    'success': False,
                    'message': 'Fila cheia'
                }
                
            # Adicionar jogador
            queue.append({
                'id': player_id,
                'name': player_name,
                'rank': rank,
                'joined_at': datetime.utcnow()
            })
            
            await self.metrics.record_metric(
                'queue.player_added',
                1,
                {
                    'queue_type': queue_type.value,
                    'queue_size': len(queue)
                }
            )
            
            return {
                'success': True,
                'position': len(queue),
                'queue_size': len(queue),
                'limit': self._queue_limits[queue_type]
            }
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar jogador: {e}")
            return {'success': False, 'message': 'Erro interno'}
            
    async def remove_player(self,
                          queue_type: QueueType,
                          player_id: str) -> Dict:
        """
        Remover jogador da fila
        
        Args:
            queue_type: Tipo de fila
            player_id: ID do jogador
            
        Returns:
            Status da remoção
        """
        try:
            queue = self._queues[queue_type]
            
            # Encontrar e remover jogador
            for i, player in enumerate(queue):
                if player['id'] == player_id:
                    queue.pop(i)
                    
                    await self.metrics.record_metric(
                        'queue.player_removed',
                        1,
                        {
                            'queue_type': queue_type.value,
                            'queue_size': len(queue)
                        }
                    )
                    
                    return {
                        'success': True,
                        'queue_size': len(queue)
                    }
                    
            return {
                'success': False,
                'message': 'Jogador não está na fila'
            }
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover jogador: {e}")
            return {'success': False, 'message': 'Erro interno'}
            
    def get_queue_status(self, queue_type: QueueType) -> Dict:
        """
        Obter status da fila
        
        Args:
            queue_type: Tipo de fila
            
        Returns:
            Status atual da fila
        """
        queue = self._queues[queue_type]
        return {
            'type': queue_type.value,
            'players': [
                {
                    'name': p['name'],
                    'waiting_time': (
                        datetime.utcnow() - p['joined_at']
                    ).total_seconds() // 60
                }
                for p in queue
            ],
            'size': len(queue),
            'limit': self._queue_limits[queue_type]
        }
        
    def is_queue_ready(self, queue_type: QueueType) -> bool:
        """Verificar se fila está pronta"""
        return len(self._queues[queue_type]) >= self._queue_limits[queue_type]
        
    async def clear_queue(self, queue_type: QueueType) -> None:
        """Limpar fila específica"""
        old_size = len(self._queues[queue_type])
        self._queues[queue_type].clear()
        
        await self.metrics.record_metric(
            'queue.cleared',
            old_size,
            {'queue_type': queue_type.value}
        )
        
    def get_players(self, queue_type: QueueType) -> List[Dict]:
        """Obter lista de jogadores na fila"""
        return self._queues[queue_type].copy()
        
    def _can_queue(self, player_id: str) -> bool:
        """Verificar se jogador pode entrar na fila (cooldown)"""
        if player_id not in self._recent_games:
            return True
            
        now = datetime.utcnow()
        cooldown = timedelta(minutes=self._cooldown_minutes)
        
        # Limpar jogos antigos
        self._recent_games[player_id] = [
            game_time for game_time in self._recent_games[player_id]
            if now - game_time < cooldown
        ]
        
        return len(self._recent_games[player_id]) == 0
        
    async def register_game(self, player_ids: List[str]):
        """Registrar jogo para cooldown"""
        now = datetime.utcnow()
        for player_id in player_ids:
            if player_id not in self._recent_games:
                self._recent_games[player_id] = []
            self._recent_games[player_id].append(now)
            
        await self.metrics.record_metric(
            'queue.game_registered',
            len(player_ids),
            {'players': len(player_ids)}
        )