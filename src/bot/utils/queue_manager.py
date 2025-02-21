"""
Queue Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 07:20:25
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
from collections import deque
from .logger import Logger
from .metrics import MetricsManager

class QueueItem:
    def __init__(self, data: Any, priority: int = 0):
        self.id = str(uuid.uuid4())
        self.data = data
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.processed_at = None
        self.error = None
        self.retries = 0

class Queue:
    def __init__(self, name: str, max_size: int = None):
        self.name = name
        self.max_size = max_size
        self.items = deque()
        self.processing = set()
        self.created_at = datetime.utcnow()
        self.total_processed = 0
        self.total_errors = 0

class QueueManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('queue_manager')
        self.metrics = metrics_manager
        self._queues: Dict[str, Queue] = {}
        self._handlers: Dict[str, Callable] = {}
        self._default_handler: Optional[Callable] = None
        self._running = False
        self._processing_tasks: Dict[str, asyncio.Task] = {}

    async def create_queue(self, 
                         name: str,
                         max_size: int = None,
                         handler: Callable = None) -> bool:
        """Criar nova fila"""
        try:
            if name in self._queues:
                return False

            queue = Queue(name, max_size)
            self._queues[name] = queue
            
            if handler:
                self._handlers[name] = handler
                
            self.logger.logger.info(f"Fila {name} criada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao criar fila: {e}")
            return False

    async def enqueue(self,
                     queue_name: str,
                     data: Any,
                     priority: int = 0) -> Optional[str]:
        """Adicionar item à fila"""
        try:
            if queue_name not in self._queues:
                raise ValueError(f"Fila {queue_name} não existe")

            queue = self._queues[queue_name]
            
            # Verificar limite
            if (queue.max_size and 
                len(queue.items) >= queue.max_size):
                raise ValueError(f"Fila {queue_name} está cheia")
                
            item = QueueItem(data, priority)
            
            # Inserir mantendo ordenação por prioridade
            for i, existing in enumerate(queue.items):
                if item.priority > existing.priority:
                    queue.items.insert(i, item)
                    break
            else:
                queue.items.append(item)
                
            # Registrar métrica
            await self.metrics.record_metric(
                f"queue.{queue_name}.enqueued",
                1
            )
            
            # Iniciar processamento se necessário
            if self._running:
                self._ensure_processing(queue_name)
                
            return item.id

        except Exception as e:
            self.logger.logger.error(f"Erro ao enfileirar: {e}")
            return None

    def _ensure_processing(self, queue_name: str):
        """Garantir que fila está sendo processada"""
        if (queue_name not in self._processing_tasks or
            self._processing_tasks[queue_name].done()):
            task = asyncio.create_task(
                self._process_queue(queue_name)
            )
            self._processing_tasks[queue_name] = task

    async def _process_queue(self, queue_name: str):
        """Processar itens da fila"""
        try:
            queue = self._queues[queue_name]
            handler = self._handlers.get(
                queue_name,
                self._default_handler
            )
            
            if not handler:
                raise ValueError(
                    f"Nenhum handler definido para fila {queue_name}"
                )
            
            while self._running:
                if not queue.items:
                    await asyncio.sleep(1)
                    continue
                    
                item = queue.items[0]
                
                try:
                    # Processar item
                    queue.processing.add(item.id)
                    result = handler(item.data)
                    if asyncio.iscoroutine(result):
                        await result
                        
                    # Remover item processado
                    queue.items.popleft()
                    queue.processing.remove(item.id)
                    queue.total_processed += 1
                    
                    # Registrar métricas
                    await self.metrics.record_metric(
                        f"queue.{queue_name}.processed",
                        1
                    )
                    
                except Exception as e:
                    queue.total_errors += 1
                    item.error = str(e)
                    item.retries += 1
                    
                    # Mover para o final da fila
                    queue.items.popleft()
                    queue.items.append(item)
                    
                    # Registrar métricas
                    await self.metrics.record_metric(
                        f"queue.{queue_name}.errors",
                        1
                    )
                    
                    self.logger.logger.error(
                        f"Erro ao processar item {item.id}: {e}"
                    )
                    
                finally:
                    if item.id in queue.processing:
                        queue.processing.remove(item.id)

        except Exception as e:
            self.logger.logger.error(
                f"Erro no processamento da fila {queue_name}: {e}"
            )

    async def set_handler(self,
                         queue_name: str,
                         handler: Callable) -> bool:
        """Definir handler para fila"""
        try:
            if queue_name not in self._queues:
                return False

            self._handlers[queue_name] = handler
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao definir handler: {e}")
            return False

    def set_default_handler(self, handler: Callable):
        """Definir handler padrão"""
        try:
            self._default_handler = handler
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir handler padrão: {e}")

    async def get_queue_info(self, queue_name: str) -> Optional[Dict]:
        """Obter informações da fila"""
        try:
            if queue_name not in self._queues:
                return None

            queue = self._queues[queue_name]
            return {
                'name': queue.name,
                'size': len(queue.items),
                'max_size': queue.max_size,
                'processing': len(queue.processing),
                'total_processed': queue.total_processed,
                'total_errors': queue.total_errors,
                'created_at': queue.created_at.isoformat(),
                'has_handler': (
                    queue_name in self._handlers or
                    self._default_handler is not None
                )
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da fila: {e}")
            return None

    async def list_queues(self) -> List[Dict]:
        """Listar todas as filas"""
        try:
            return [
                await self.get_queue_info(name)
                for name in self._queues
            ]
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar filas: {e}")
            return []

    async def remove_queue(self, queue_name: str) -> bool:
        """Remover fila"""
        try:
            if queue_name not in self._queues:
                return False

            # Cancelar processamento
            if queue_name in self._processing_tasks:
                self._processing_tasks[queue_name].cancel()
                try:
                    await self._processing_tasks[queue_name]
                except asyncio.CancelledError:
                    pass
                del self._processing_tasks[queue_name]
                
            # Remover handlers
            if queue_name in self._handlers:
                del self._handlers[queue_name]
                
            del self._queues[queue_name]
            
            self.logger.logger.info(f"Fila {queue_name} removida")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover fila: {e}")
            return False

    async def start(self):
        """Iniciar processamento das filas"""
        try:
            self._running = True
            
            # Iniciar processamento de todas as filas
            for queue_name in self._queues:
                self._ensure_processing(queue_name)
                
            self.logger.logger.info("Processamento iniciado")

        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar processamento: {e}")

    async def stop(self):
        """Parar processamento das filas"""
        try:
            self._running = False
            
            # Cancelar todas as tasks
            for task in self._processing_tasks.values():
                task.cancel()
                
            # Aguardar cancelamento
            if self._processing_tasks:
                await asyncio.gather(
                    *self._processing_tasks.values(),
                    return_exceptions=True
                )
                
            self._processing_tasks.clear()
            self.logger.logger.info("Processamento parado")

        except Exception as e:
            self.logger.logger.error(f"Erro ao parar processamento: {e}")

    async def clear_queue(self, queue_name: str) -> int:
        """Limpar fila"""
        try:
            if queue_name not in self._queues:
                return 0

            queue = self._queues[queue_name]
            count = len(queue.items)
            queue.items.clear()
            
            self.logger.logger.info(f"Fila {queue_name} limpa")
            return count

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar fila: {e}")
            return 0

    async def get_item(self,
                      queue_name: str,
                      item_id: str) -> Optional[Dict]:
        """Obter informações do item"""
        try:
            if queue_name not in self._queues:
                return None

            queue = self._queues[queue_name]
            
            # Procurar item
            for item in queue.items:
                if item.id == item_id:
                    return {
                        'id': item.id,
                        'priority': item.priority,
                        'created_at': item.created_at.isoformat(),
                        'processed_at': (
                            item.processed_at.isoformat()
                            if item.processed_at else None
                        ),
                        'error': item.error,
                        'retries': item.retries,
                        'processing': item.id in queue.processing
                    }
                    
            return None

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter item: {e}")
            return None