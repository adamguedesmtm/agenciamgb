"""
State Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:12:27
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import asyncio
from .logger import Logger

class StateManager:
    def __init__(self):
        self.logger = Logger('state_manager')
        self._state = {}
        self._history = []
        self._max_history = 100
        self._observers = {}
        self._lock = asyncio.Lock()

    async def set_state(self, key: str, value: Any):
        """Definir valor no estado"""
        try:
            async with self._lock:
                old_value = self._state.get(key)
                self._state[key] = value
                
                # Registrar mudança no histórico
                self._add_to_history(key, old_value, value)
                
                # Notificar observadores
                await self._notify_observers(key, old_value, value)
                
            self.logger.logger.info(f"Estado {key} atualizado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir estado: {e}")

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Obter valor do estado"""
        try:
            return self._state.get(key, default)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estado: {e}")
            return default

    async def delete_state(self, key: str):
        """Deletar valor do estado"""
        try:
            async with self._lock:
                if key in self._state:
                    old_value = self._state[key]
                    del self._state[key]
                    
                    # Registrar mudança no histórico
                    self._add_to_history(key, old_value, None)
                    
                    # Notificar observadores
                    await self._notify_observers(key, old_value, None)
                    
                    self.logger.logger.info(f"Estado {key} deletado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar estado: {e}")

    def _add_to_history(self, key: str, old_value: Any, new_value: Any):
        """Adicionar mudança ao histórico"""
        try:
            change = {
                'key': key,
                'old_value': old_value,
                'new_value': new_value,
                'timestamp': datetime.now()
            }
            
            self._history.append(change)
            
            # Manter tamanho máximo do histórico
            if len(self._history) > self._max_history:
                self._history.pop(0)
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar ao histórico: {e}")

    async def add_observer(self, key: str, callback: callable):
        """Adicionar observador para mudanças"""
        try:
            if key not in self._observers:
                self._observers[key] = []
            self._observers[key].append(callback)
            
            self.logger.logger.info(f"Observador adicionado para {key}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar observador: {e}")

    async def remove_observer(self, key: str, callback: callable):
        """Remover observador"""
        try:
            if key in self._observers:
                self._observers[key].remove(callback)
                if not self._observers[key]:
                    del self._observers[key]
                    
            self.logger.logger.info(f"Observador removido de {key}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover observador: {e}")

    async def _notify_observers(self, key: str, old_value: Any, new_value: Any):
        """Notificar observadores sobre mudanças"""
        try:
            if key in self._observers:
                for callback in self._observers[key]:
                    try:
                        await callback(key, old_value, new_value)
                    except Exception as e:
                        self.logger.logger.error(
                            f"Erro ao notificar observador: {e}"
                        )
        except Exception as e:
            self.logger.logger.error(f"Erro ao notificar observadores: {e}")

    async def get_history(self, key: str = None) -> List[Dict]:
        """Obter histórico de mudanças"""
        try:
            if key:
                return [
                    change for change in self._history
                    if change['key'] == key
                ]
            return self._history.copy()
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter histórico: {e}")
            return []

    async def clear_history(self):
        """Limpar histórico"""
        try:
            self._history.clear()
            self.logger.logger.info("Histórico limpo")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar histórico: {e}")

    async def save_state(self, filename: str):
        """Salvar estado em arquivo"""
        try:
            async with self._lock:
                state_data = {
                    'state': self._state,
                    'history': self._history
                }
                
                with open(filename, 'w') as f:
                    json.dump(state_data, f, indent=4, default=str)
                    
                self.logger.logger.info(f"Estado salvo em {filename}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar estado: {e}")

    async def load_state(self, filename: str):
        """Carregar estado de arquivo"""
        try:
            with open(filename, 'r') as f:
                state_data = json.load(f)
                
            async with self._lock:
                self._state = state_data['state']
                self._history = state_data['history']
                
            self.logger.logger.info(f"Estado carregado de {filename}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar estado: {e}")
