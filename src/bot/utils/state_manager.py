"""
State Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 11:30:00
"""

from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import asyncio
from datetime import datetime
import copy
from .logger import Logger
from .metrics import MetricsManager

class StateManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('state_manager')
        self.metrics = metrics_manager
        self._state: Dict = {}
        self._history: List[Dict] = []
        self._observers: Dict[str, List[callable]] = {}
        self._max_history = 100
        self._auto_save = True
        self._save_interval = 300  # 5 minutos
        self._save_task = None
        self._storage_path = Path('/opt/cs2server/data/state.json')
        self._backup_path = Path('/opt/cs2server/data/state.backup.json')
        self._running = False

    async def initialize(self):
        """Inicializar gerenciador de estado"""
        try:
            # Criar diretório se necessário
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Carregar estado salvo
            await self.load_state()
            
            # Iniciar tarefa de auto-save
            self._running = True
            if self._auto_save:
                self._save_task = asyncio.create_task(
                    self._auto_save_loop()
                )
                
            self.logger.logger.info("State manager iniciado")

        except Exception as e:
            self.logger.logger.error(f"Erro ao inicializar: {e}")
            raise

    async def load_state(self):
        """Carregar estado do arquivo"""
        try:
            if not self._storage_path.exists():
                return
                
            try:
                with open(self._storage_path, 'r') as f:
                    self._state = json.load(f)
            except:
                # Tentar carregar backup
                if self._backup_path.exists():
                    with open(self._backup_path, 'r') as f:
                        self._state = json.load(f)
                        
            self.logger.logger.info("Estado carregado")
            
            # Registrar snapshot inicial
            self._add_to_history(
                'load',
                None,
                copy.deepcopy(self._state)
            )

        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar estado: {e}")

    async def save_state(self):
        """Salvar estado em arquivo"""
        try:
            # Fazer backup do arquivo atual
            if self._storage_path.exists():
                self._storage_path.rename(self._backup_path)
                
            # Salvar novo estado
            with open(self._storage_path, 'w') as f:
                json.dump(self._state, f, indent=4)
                
            self.logger.logger.info("Estado salvo")
            
            # Registrar métrica
            await self.metrics.record_metric('state.saved', 1)

        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar estado: {e}")

    async def _auto_save_loop(self):
        """Loop de auto-save"""
        try:
            while self._running:
                await asyncio.sleep(self._save_interval)
                await self.save_state()
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.logger.error(f"Erro no auto-save: {e}")

    async def set_state(self,
                       key: str,
                       value: Any,
                       notify: bool = True) -> bool:
        """Definir valor no estado"""
        try:
            # Armazenar valor anterior
            old_value = self._state.get(key)
            
            # Atualizar estado
            self._state[key] = value
            
            # Adicionar ao histórico
            self._add_to_history(
                'set',
                key,
                value,
                old_value
            )
            
            # Notificar observers
            if notify:
                await self._notify_observers(key, value, old_value)
                
            # Registrar métrica
            await self.metrics.record_metric('state.updates', 1)
            
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao definir estado: {e}")
            return False

    async def get_state(self, key: str, default: Any = None) -> Any:
        """Obter valor do estado"""
        try:
            return self._state.get(key, default)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estado: {e}")
            return default

    async def delete_state(self, key: str, notify: bool = True) -> bool:
        """Deletar valor do estado"""
        try:
            if key not in self._state:
                return False

            # Armazenar valor anterior
            old_value = self._state[key]
            
            # Remover do estado
            del self._state[key]
            
            # Adicionar ao histórico
            self._add_to_history(
                'delete',
                key,
                None,
                old_value
            )
            
            # Notificar observers
            if notify:
                await self._notify_observers(key, None, old_value)
                
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar estado: {e}")
            return False

    def _add_to_history(self,
                       action: str,
                       key: str,
                       value: Any,
                       old_value: Any = None):
        """Adicionar entrada ao histórico"""
        try:
            entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': action,
                'key': key,
                'value': value,
                'old_value': old_value
            }
            
            self._history.append(entry)
            
            # Limitar tamanho do histórico
            while len(self._history) > self._max_history:
                self._history.pop(0)

        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar histórico: {e}")

    async def _notify_observers(self,
                              key: str,
                              value: Any,
                              old_value: Any):
        """Notificar observers sobre mudança"""
        try:
            if key not in self._observers:
                return

            for callback in self._observers[key]:
                try:
                    result = callback(value, old_value)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    self.logger.logger.error(
                        f"Erro em observer de {key}: {e}"
                    )

        except Exception as e:
            self.logger.logger.error(f"Erro ao notificar: {e}")

    def observe(self, key: str, callback: callable):
        """Registrar observer para mudanças"""
        try:
            if key not in self._observers:
                self._observers[key] = []
            self._observers[key].append(callback)
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar observer: {e}")

    def unobserve(self, key: str, callback: callable):
        """Remover observer"""
        try:
            if key in self._observers:
                if callback in self._observers[key]:
                    self._observers[key].remove(callback)
                if not self._observers[key]:
                    del self._observers[key]
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover observer: {e}")

    async def get_history(self,
                         key: str = None,
                         limit: int = None) -> List[Dict]:
        """Obter histórico de mudanças"""
        try:
            history = self._history
            
            if key:
                history = [
                    h for h in history
                    if h['key'] == key
                ]
                
            if limit:
                history = history[-limit:]
                
            return history

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter histórico: {e}")
            return []

    async def clear_state(self, notify: bool = True):
        """Limpar todo o estado"""
        try:
            # Armazenar estado anterior
            old_state = copy.deepcopy(self._state)
            
            # Limpar estado
            self._state.clear()
            
            # Adicionar ao histórico
            self._add_to_history(
                'clear',
                None,
                {},
                old_state
            )
            
            # Notificar observers
            if notify:
                for key in old_state:
                    await self._notify_observers(
                        key,
                        None,
                        old_state[key]
                    )
                    
            # Salvar estado
            await self.save_state()
            
            self.logger.logger.info("Estado limpo")

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar estado: {e}")

    async def get_snapshot(self) -> Dict:
        """Obter snapshot do estado atual"""
        try:
            return copy.deepcopy(self._state)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter snapshot: {e}")
            return {}

    async def restore_snapshot(self,
                             snapshot: Dict,
                             notify: bool = True):
        """Restaurar estado a partir de snapshot"""
        try:
            # Armazenar estado anterior
            old_state = copy.deepcopy(self._state)
            
            # Restaurar estado
            self._state = copy.deepcopy(snapshot)
            
            # Adicionar ao histórico
            self._add_to_history(
                'restore',
                None,
                snapshot,
                old_state
            )
            
            # Notificar observers
            if notify:
                # Notificar sobre valores removidos
                for key in old_state:
                    if key not in self._state:
                        await self._notify_observers(
                            key,
                            None,
                            old_state[key]
                        )
                        
                # Notificar sobre valores novos/alterados
                for key, value in self._state.items():
                    if key not in old_state:
                        await self._notify_observers(
                            key,
                            value,
                            None
                        )
                    elif value != old_state[key]:
                        await self._notify_observers(
                            key,
                            value,
                            old_state[key]
                        )
                        
            # Salvar estado
            await self.save_state()
            
            self.logger.logger.info("Snapshot restaurado")

        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar snapshot: {e}")

    async def stop(self):
        """Parar gerenciador de estado"""
        try:
            self._running = False
            
            # Cancelar tarefa de auto-save
            if self._save_task:
                self._save_task.cancel()
                try:
                    await self._save_task
                except asyncio.CancelledError:
                    pass
                    
            # Salvar estado final
            await self.save_state()
            
            self.logger.logger.info("State manager parado")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar: {e}")

    def set_auto_save(self, enabled: bool, interval: int = None):
        """Configurar auto-save"""
        try:
            self._auto_save = enabled
            
            if interval is not None:
                if interval < 1:
                    raise ValueError("Intervalo deve ser maior que 0")
                self._save_interval = interval
                
            # Reiniciar tarefa se necessário
            if self._save_task:
                self._save_task.cancel()
                
            if enabled and self._running:
                self._save_task = asyncio.create_task(
                    self._auto_save_loop()
                )
                
            self.logger.logger.info(
                f"Auto-save {'ativado' if enabled else 'desativado'}"
            )
            
        except Exception as e:
            self.logger.logger.error(
                f"Erro ao configurar auto-save: {e}"
            )