"""
Event Bus for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 07:02:56
"""

from typing import Dict, List, Callable, Any, Optional
import asyncio
from datetime import datetime
from .logger import Logger
from .metrics import MetricsManager

class EventBus:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('event_bus')
        self.metrics = metrics_manager
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: Dict[str, List[Dict]] = {}
        self._max_history = 1000
        self._running = True

    async def subscribe(self, event: str, callback: Callable) -> bool:
        """Subscrever a um evento"""
        try:
            if event not in self._subscribers:
                self._subscribers[event] = []
            
            if callback not in self._subscribers[event]:
                self._subscribers[event].append(callback)
                self.logger.logger.info(
                    f"Novo subscriber para evento {event}"
                )
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao subscrever evento: {e}")
            return False

    async def unsubscribe(self, event: str, callback: Callable) -> bool:
        """Cancelar subscrição de evento"""
        try:
            if (event in self._subscribers and 
                callback in self._subscribers[event]):
                self._subscribers[event].remove(callback)
                if not self._subscribers[event]:
                    del self._subscribers[event]
                self.logger.logger.info(
                    f"Subscriber removido do evento {event}"
                )
                return True
            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao cancelar subscrição: {e}")
            return False

    async def publish(self, 
                     event: str, 
                     data: Any = None,
                     sync: bool = False) -> List[Any]:
        """
        Publicar evento
        sync: Se True, aguarda todos os handlers
        """
        try:
            if not self._running:
                raise RuntimeError("Event bus não está em execução")

            timestamp = datetime.utcnow()
            
            # Registrar no histórico
            if event not in self._history:
                self._history[event] = []
            self._history[event].append({
                'timestamp': timestamp,
                'data': data
            })
            
            # Limitar tamanho do histórico
            if len(self._history[event]) > self._max_history:
                self._history[event].pop(0)
            
            # Registrar métrica
            await self.metrics.record_metric(
                f"events.published.{event}",
                1
            )
            
            if event not in self._subscribers:
                return []
            
            results = []
            tasks = []
            
            # Notificar subscribers
            for callback in self._subscribers[event]:
                if sync:
                    try:
                        result = callback(data)
                        if asyncio.iscoroutine(result):
                            result = await result
                        results.append(result)
                    except Exception as e:
                        self.logger.logger.error(
                            f"Erro em handler do evento {event}: {e}"
                        )
                        results.append(None)
                else:
                    task = asyncio.create_task(
                        self._execute_handler(event, callback, data)
                    )
                    tasks.append(task)
                    
            if not sync and tasks:
                # Aguardar tasks sem bloquear
                asyncio.gather(*tasks)
                
            return results

        except Exception as e:
            self.logger.logger.error(f"Erro ao publicar evento: {e}")
            return []

    async def _execute_handler(self,
                             event: str,
                             handler: Callable,
                             data: Any):
        """Executar handler de evento"""
        try:
            result = handler(data)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            self.logger.logger.error(
                f"Erro em handler do evento {event}: {e}"
            )

    def get_subscribers(self, event: str = None) -> Dict[str, int]:
        """Obter número de subscribers por evento"""
        try:
            if event:
                return {
                    event: len(self._subscribers.get(event, []))
                }
            return {
                evt: len(subs)
                for evt, subs in self._subscribers.items()
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter subscribers: {e}")
            return {}

    def get_event_history(self,
                         event: str,
                         limit: int = None) -> List[Dict]:
        """Obter histórico de eventos"""
        try:
            if event not in self._history:
                return []
                
            history = self._history[event]
            if limit:
                history = history[-limit:]
                
            return [
                {
                    'timestamp': evt['timestamp'].isoformat(),
                    'data': evt['data']
                }
                for evt in history
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter histórico: {e}")
            return []

    def clear_history(self, event: str = None):
        """Limpar histórico de eventos"""
        try:
            if event:
                if event in self._history:
                    self._history[event].clear()
            else:
                self._history.clear()
                
            self.logger.logger.info(
                f"Histórico limpo: {event or 'todos'}"
            )

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar histórico: {e}")

    async def stop(self):
        """Parar event bus"""
        try:
            self._running = False
            self.logger.logger.info("Event bus parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar event bus: {e}")

    async def start(self):
        """Iniciar event bus"""
        try:
            self._running = True
            self.logger.logger.info("Event bus iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar event bus: {e}")

    def set_max_history(self, size: int):
        """Definir tamanho máximo do histórico"""
        try:
            if size < 1:
                raise ValueError("Tamanho deve ser maior que 0")
                
            self._max_history = size
            
            # Ajustar históricos existentes
            for event in self._history:
                while len(self._history[event]) > size:
                    self._history[event].pop(0)
                    
            self.logger.logger.info(
                f"Tamanho máximo do histórico: {size}"
            )

        except Exception as e:
            self.logger.logger.error(
                f"Erro ao definir tamanho do histórico: {e}"
            )

    async def has_subscribers(self, event: str) -> bool:
        """Verificar se evento tem subscribers"""
        try:
            return (
                event in self._subscribers and
                bool(self._subscribers[event])
            )
        except Exception as e:
            self.logger.logger.error(
                f"Erro ao verificar subscribers: {e}"
            )
            return False

    async def get_stats(self) -> Dict:
        """Obter estatísticas do event bus"""
        try:
            stats = {
                'total_events': len(self._subscribers),
                'total_subscribers': sum(
                    len(subs)
                    for subs in self._subscribers.values()
                ),
                'events': self.get_subscribers(),
                'history_size': {
                    event: len(history)
                    for event, history in self._history.items()
                }
            }
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}