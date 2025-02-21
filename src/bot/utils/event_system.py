"""
Event System for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:52:20
"""

from typing import Callable, Dict, List, Set
import asyncio
from datetime import datetime
from .logger import Logger

class EventSystem:
    def __init__(self):
        self.logger = Logger('event_system')
        self._handlers: Dict[str, Set[Callable]] = {}
        self._event_history: List[Dict] = []
        self._max_history = 1000

    async def subscribe(self, event_name: str, handler: Callable):
        """Subscrever a um evento"""
        try:
            if event_name not in self._handlers:
                self._handlers[event_name] = set()
            self._handlers[event_name].add(handler)
            
            self.logger.logger.info(
                f"Handler adicionado para evento {event_name}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao subscrever evento: {e}")

    async def unsubscribe(self, event_name: str, handler: Callable):
        """Cancelar subscrição de evento"""
        try:
            if event_name in self._handlers:
                self._handlers[event_name].discard(handler)
                if not self._handlers[event_name]:
                    del self._handlers[event_name]
                    
            self.logger.logger.info(
                f"Handler removido do evento {event_name}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao cancelar subscrição: {e}")

    async def emit(self, event_name: str, data: dict = None):
        """Emitir evento"""
        try:
            if event_name in self._handlers:
                event_data = {
                    'name': event_name,
                    'timestamp': datetime.now(),
                    'data': data
                }
                
                self._add_to_history(event_data)

                tasks = []
                for handler in self._handlers[event_name]:
                    task = asyncio.create_task(handler(event_data))
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)
                
            self.logger.logger.info(
                f"Evento {event_name} emitido com {len(self._handlers.get(event_name, set()))} handlers"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao emitir evento: {e}")

    def _add_to_history(self, event_data: dict):
        """Adicionar evento ao histórico"""
        try:
            self._event_history.append(event_data)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar ao histórico: {e}")

    async def get_history(self, 
                         event_name: str = None, 
                         limit: int = 100) -> List[Dict]:
        """Obter histórico de eventos"""
        try:
            if event_name:
                history = [
                    event for event in self._event_history
                    if event['name'] == event_name
                ]
            else:
                history = self._event_history.copy()

            return history[-limit:]
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter histórico: {e}")
            return []

    async def clear_history(self, event_name: str = None):
        """Limpar histórico de eventos"""
        try:
            if event_name:
                self._event_history = [
                    event for event in self._event_history
                    if event['name'] != event_name
                ]
            else:
                self._event_history.clear()
                
            self.logger.logger.info("Histórico de eventos limpo")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar histórico: {e}")

    async def get_subscribed_events(self) -> Dict[str, int]:
        """Obter eventos com handlers ativos"""
        try:
            return {
                event: len(handlers)
                for event, handlers in self._handlers.items()
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter eventos subscritos: {e}")
            return {}

    async def remove_all_handlers(self, event_name: str):
        """Remover todos os handlers de um evento"""
        try:
            if event_name in self._handlers:
                del self._handlers[event_name]
                
            self.logger.logger.info(
                f"Todos os handlers removidos do evento {event_name}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover handlers: {e}")

    async def has_handlers(self, event_name: str) -> bool:
        """Verificar se evento tem handlers"""
        try:
            return event_name in self._handlers and bool(self._handlers[event_name])
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar handlers: {e}")
            return False

    async def get_handler_count(self, event_name: str) -> int:
        """Obter número de handlers de um evento"""
        try:
            return len(self._handlers.get(event_name, set()))
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter contagem de handlers: {e}")
            return 0