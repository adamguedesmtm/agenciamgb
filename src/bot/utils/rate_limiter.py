"""
Rate Limiter for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:18:55
"""

import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, List
from .logger import Logger

class RateLimiter:
    def __init__(self):
        self.logger = Logger('rate_limiter')
        self._limits: Dict[str, Dict] = {}
        self._requests: Dict[str, List] = defaultdict(list)
        self._cleanup_task = None

    async def start(self):
        """Iniciar limpeza automática"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Parar limpeza automática"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def add_limit(self, name: str, requests: int, period: int):
        """
        Adicionar novo limite
        requests: número máximo de requisições
        period: período em segundos
        """
        self._limits[name] = {
            'requests': requests,
            'period': period
        }

    async def acquire(self, name: str, key: str) -> bool:
        """
        Tentar adquirir permissão
        Retorna False se o limite foi excedido
        """
        try:
            if name not in self._limits:
                self.logger.logger.warning(f"Limite '{name}' não definido")
                return True

            limit = self._limits[name]
            now = datetime.now()
            
            # Limpar requisições antigas
            await self._cleanup_requests(name, key, now)
            
            # Verificar limite
            if len(self._requests[f"{name}:{key}"]) >= limit['requests']:
                return False

            # Adicionar nova requisição
            self._requests[f"{name}:{key}"].append(now)
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar rate limit: {e}")
            return True

    async def get_remaining(self, name: str, key: str) -> Optional[int]:
        """Obter número de requisições restantes"""
        try:
            if name not in self._limits:
                return None

            limit = self._limits[name]
            now = datetime.now()
            
            # Limpar requisições antigas
            await self._cleanup_requests(name, key, now)
            
            current = len(self._requests[f"{name}:{key}"])
            return limit['requests'] - current
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter requisições restantes: {e}")
            return None

    async def get_reset_time(self, name: str, key: str) -> Optional[datetime]:
        """Obter tempo para reset do limite"""
        try:
            if name not in self._limits:
                return None

            requests = self._requests[f"{name}:{key}"]
            if not requests:
                return datetime.now()

            limit = self._limits[name]
            oldest = min(requests)
            return oldest + timedelta(seconds=limit['period'])
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter tempo de reset: {e}")
            return None

    async def _cleanup_requests(self, name: str, key: str, now: datetime):
        """Limpar requisições expiradas"""
        try:
            if name not in self._limits:
                return

            limit = self._limits[name]
            cutoff = now - timedelta(seconds=limit['period'])
            
            self._requests[f"{name}:{key}"] = [
                req for req in self._requests[f"{name}:{key}"]
                if req > cutoff
            ]
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar requisições: {e}")

    async def _cleanup_loop(self):
        """Loop de limpeza automática"""
        try:
            while True:
                now = datetime.now()
                
                # Limpar todas as requisições expiradas
                for name in self._limits:
                    for key in list(self._requests.keys()):
                        if key.startswith(f"{name}:"):
                            await self._cleanup_requests(name, key.split(':')[1], now)
                            
                            # Remover chaves vazias
                            if not self._requests[key]:
                                del self._requests[key]
                
                await asyncio.sleep(60)  # Executar a cada minuto
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.logger.error(f"Erro no loop de limpeza: {e}")

    def get_limits(self) -> Dict[str, Dict]:
        """Obter todos os limites configurados"""
        return self._limits.copy()

    async def reset(self, name: str, key: str):
        """Resetar contador para um limite específico"""
        try:
            if f"{name}:{key}" in self._requests:
                del self._requests[f"{name}:{key}"]
        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar limite: {e}")

    async def reset_all(self):
        """Resetar todos os contadores"""
        try:
            self._requests.clear()
        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar todos os limites: {e}")