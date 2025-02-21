"""
Queue Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:12:27
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from .logger import Logger

class QueueManager:
    def __init__(self, max_size: int = 1000):
        self.logger = Logger('queue_manager')
        self.max_size = max_size
        self._queues: Dict[str, List[Dict]] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._processing: Dict[str, bool] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def create_queue(self, queue_name: str, max_size: int = None):
        """Criar nova fila"""
        try:
            if queue_name in self._queues:
                raise ValueError(f"Fila {queue_name} já existe")

            self._queues[queue_name] = []
            self._subscribers[queue_name] = []
            self._processing[queue_name] = False
            self._locks[queue_name] = asyncio.Lock()
            
            if max_size:
                self.max_size = max_size

            self.logger.logger.info(f"Fila {queue_name} criada")
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar fila: {e}")

    async def delete_queue(self, queue_name: str):
        """Deletar fila"""
        try:
            if queue_name in self._queues:
                del self._queues[queue_name]
                del self._subscribers[queue_name]
                del self._processing[queue_name]
                del self._locks[queue_name]
                
                self.logger.logger.info(f"Fila {queue_name} deletada")
        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar fila: {e}")

    async def enqueue(self, queue_name: str, item: Any, priority: int = 0):
        """
        Adicionar item à fila
        priority: 0 (baixa) a 10 (alta)
        """
        try:
            if queue_name not in self._queues:
                raise ValueError(f"Fila {queue_name} não existe")

            if len(self._queues[queue_name]) >= self.max_size:
                raise ValueError(f"Fila {queue_name} está cheia")

            queue_item = {
                'item': item,
                'priority': priority,
                'timestamp': datetime.now()
            }

            async with self._locks[queue_name]:
                # Inserir mantendo ordem de prioridade
                queue = self._queues[queue_name]
                index = 0
                for i, existing in enumerate(queue):
                    if existing['priority'] < priority:
                        index = i
                        break
                    elif existing['priority'] == priority:
                        index = i + 1
                queue.insert(index, queue_item)

            # Notificar subscribers
            await self._notify_subscribers(queue_name, 'enqueue', queue_item)
            
            self.logger.logger.info(
                f"Item adicionado à fila {queue_name} com prioridade {priority}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar à fila: {e}")

    async def dequeue(self, queue_name: str) -> Optional[Any]:
        """Remover e retornar próximo item da fila"""
        try:
            if queue_name not in self._queues:
                raise ValueError(f"Fila {queue_name} não existe")

            async with self._locks[queue_name]:
                if not self._queues[queue_name]:
                    return None

                item = self._queues[queue_name].pop(0)
                
                # Notificar subscribers
                await self._notify_subscribers(queue_name, 'dequeue', item)
                
                return item['item']
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover da fila: {e}")
            return None

    async def peek(self, queue_name: str) -> Optional[Any]:
        """Visualizar próximo item sem remover"""
        try:
            if queue_name not in self._queues:
                raise ValueError(f"Fila {queue_name} não existe")

            if not self._queues[queue_name]:
                return None

            return self._queues[queue_name][0]['item']
        except Exception as e:
            self.logger.logger.error(f"Erro ao visualizar fila: {e}")
            return None

    async def subscribe(self, queue_name: str, callback: Callable):
        """Subscrever a eventos da fila"""
        try:
            if queue_name not in self._queues:
                raise ValueError(f"Fila {queue_name} não existe")

            if callback not in self._subscribers[queue_name]:
                self._subscribers[queue_name].append(callback)
                
            self.logger.logger.info(
                f"Novo subscriber adicionado à fila {queue_name}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao subscrever: {e}")

    async def unsubscribe(self, queue_name: str, callback: Callable):
        """Cancelar subscrição"""
        try:
            if queue_name in self._subscribers:
                self._subscribers[queue_name].remove(callback)
                self.logger.logger.info(
                    f"Subscriber removido da fila {queue_name}"
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao cancelar subscrição: {e}")

    async def _notify_subscribers(self, queue_name: str, event: str, data: Any):
        """Notificar subscribers sobre eventos"""
        try:
            if queue_name in self._subscribers:
                for callback in self._subscribers[queue_name]:
                    try:
                        await callback(event, data)
                    except Exception as e:
                        self.logger.logger.error(
                            f"Erro ao notificar subscriber: {e}"
                        )
        except Exception as e:
            self.logger.logger.error(f"Erro ao notificar subscribers: {e}")

    async def clear(self, queue_name: str):
        """Limpar fila"""
        try:
            if queue_name in self._queues:
                async with self._locks[queue_name]:
                    self._queues[queue_name].clear()
                await self._notify_subscribers(queue_name, 'clear', None)
                
                self.logger.logger.info(f"Fila {queue_name} limpa")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar fila: {e}")

    async def size(self, queue_name: str) -> int:
        """Obter tamanho da fila"""
        try:
            return len(self._queues.get(queue_name, []))
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter tamanho da fila: {e}")
            return 0

    async def is_empty(self, queue_name: str) -> bool:
        """Verificar se fila está vazia"""
        try:
            return len(self._queues.get(queue_name, [])) == 0
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar fila: {e}")
            return True

    async def get_stats(self, queue_name: str) -> Dict:
        """Obter estatísticas da fila"""
        try:
            if queue_name not in self._queues:
                return {}

            queue = self._queues[queue_name]
            return {
                'size': len(queue),
                'empty': len(queue) == 0,
                'max_size': self.max_size,
                'subscribers': len(self._subscribers[queue_name]),
                'processing': self._processing[queue_name],
                'priority_distribution': self._get_priority_distribution(queue)
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def _get_priority_distribution(self, queue: List[Dict]) -> Dict[int, int]:
        """Obter distribuição de prioridades"""
        try:
            distribution = {}
            for item in queue:
                priority = item['priority']
                distribution[priority] = distribution.get(priority, 0) + 1
            return distribution
        except Exception as e:
            self.logger.logger.error(
                f"Erro ao obter distribuição de prioridades: {e}"
            )
            return {}