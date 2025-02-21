"""
Rate Limiter for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:56:22
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional, Tuple
import asyncio
from .logger import Logger

class RateLimiter:
    def __init__(self):
        self.logger = Logger('rate_limiter')
        self._limits = {}  # Configurações de limite por chave
        self._counters = defaultdict(list)  # Contadores por chave
        self._blocked = {}  # Chaves bloqueadas
        self._cleanup_task = None

    async def start(self):
        """Iniciar rate limiter"""
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.logger.info("Rate limiter iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar rate limiter: {e}")

    async def stop(self):
        """Parar rate limiter"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            self.logger.logger.info("Rate limiter parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar rate limiter: {e}")

    def set_limit(self, key: str, max_requests: int, window: int):
        """
        Definir limite de requisições
        key: Identificador do limite
        max_requests: Número máximo de requisições
        window: Janela de tempo em segundos
        """
        try:
            self._limits[key] = {
                'max_requests': max_requests,
                'window': window
            }
            self.logger.logger.info(
                f"Limite definido: {key} - {max_requests} req/{window}s"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir limite: {e}")

    async def check(self, key: str, identifier: str) -> Tuple[bool, Optional[int]]:
        """
        Verificar se requisição está dentro do limite
        Retorna: (permitido, tempo_restante_bloqueio)
        """
        try:
            if key not in self._limits:
                return True, None

            # Verificar bloqueio
            if self._is_blocked(identifier):
                return False, self._get_block_remaining(identifier)

            limit = self._limits[key]
            now = time.time()
            
            # Limpar requisições antigas
            self._counters[identifier] = [
                t for t in self._counters[identifier]
                if now - t <= limit['window']
            ]
            
            # Verificar limite
            if len(self._counters[identifier]) >= limit['max_requests']:
                # Bloquear por 2x a janela de tempo
                await self._block(identifier, limit['window'] * 2)
                return False, limit['window'] * 2

            # Registrar requisição
            self._counters[identifier].append(now)
            return True, None

        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar limite: {e}")
            return False, None

    def _is_blocked(self, identifier: str) -> bool:
        """Verificar se identificador está bloqueado"""
        try:
            if identifier not in self._blocked:
                return False
                
            if time.time() >= self._blocked[identifier]:
                del self._blocked[identifier]
                return False
                
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar bloqueio: {e}")
            return False

    async def _block(self, identifier: str, duration: int):
        """Bloquear identificador"""
        try:
            self._blocked[identifier] = time.time() + duration
            self.logger.logger.warning(
                f"Identificador {identifier} bloqueado por {duration}s"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao bloquear: {e}")

    def _get_block_remaining(self, identifier: str) -> Optional[int]:
        """Obter tempo restante de bloqueio"""
        try:
            if identifier not in self._blocked:
                return None
                
            remaining = int(self._blocked[identifier] - time.time())
            return max(0, remaining)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter tempo de bloqueio: {e}")
            return None

    async def _cleanup_loop(self):
        """Loop de limpeza de dados antigos"""
        try:
            while True:
                try:
                    now = time.time()
                    
                    # Limpar contadores antigos
                    for identifier in list(self._counters.keys()):
                        max_window = max(
                            limit['window']
                            for limit in self._limits.values()
                        )
                        self._counters[identifier] = [
                            t for t in self._counters[identifier]
                            if now - t <= max_window
                        ]
                        if not self._counters[identifier]:
                            del self._counters[identifier]
                    
                    # Limpar bloqueios expirados
                    for identifier in list(self._blocked.keys()):
                        if now >= self._blocked[identifier]:
                            del self._blocked[identifier]
                    
                    await asyncio.sleep(60)  # Executar a cada minuto
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no cleanup: {e}")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            pass

    def get_limits(self) -> Dict:
        """Obter limites configurados"""
        return self._limits.copy()

    def get_status(self, identifier: str) -> Dict:
        """Obter status do identificador"""
        try:
            now = time.time()
            status = {
                'requests': len(self._counters[identifier]),
                'blocked': self._is_blocked(identifier),
                'block_remaining': self._get_block_remaining(identifier)
            }
            
            # Adicionar informações por limite
            status['limits'] = {}
            for key, limit in self._limits.items():
                requests = len([
                    t for t in self._counters[identifier]
                    if now - t <= limit['window']
                ])
                status['limits'][key] = {
                    'requests': requests,
                    'max_requests': limit['max_requests'],
                    'window': limit['window'],
                    'remaining': limit['max_requests'] - requests
                }
                
            return status
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            return {}

    async def reset(self, identifier: str = None):
        """Resetar contadores e bloqueios"""
        try:
            if identifier:
                if identifier in self._counters:
                    del self._counters[identifier]
                if identifier in self._blocked:
                    del self._blocked[identifier]
            else:
                self._counters.clear()
                self._blocked.clear()
                
            self.logger.logger.info(
                f"Contadores resetados: {identifier or 'todos'}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar: {e}")