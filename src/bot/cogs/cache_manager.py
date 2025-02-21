"""
Cache Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:18:55
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from .logger import Logger

class CacheManager:
    def __init__(self):
        self.logger = Logger('cache_manager')
        self._cache = {}
        self._timeouts = {}
        self._locks = {}

    async def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        try:
            if key in self._cache:
                # Verificar timeout
                if self._is_expired(key):
                    await self.delete(key)
                    return None
                return self._cache[key]
            return None
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter do cache: {e}")
            return None

    async def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """
        Definir valor no cache
        timeout: tempo em segundos (padrão: 5 minutos)
        """
        try:
            async with self._get_lock(key):
                self._cache[key] = value
                self._timeouts[key] = datetime.now() + timedelta(seconds=timeout)
                return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Deletar valor do cache"""
        try:
            async with self._get_lock(key):
                if key in self._cache:
                    del self._cache[key]
                if key in self._timeouts:
                    del self._timeouts[key]
                return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar do cache: {e}")
            return False

    async def clear(self) -> bool:
        """Limpar todo o cache"""
        try:
            self._cache.clear()
            self._timeouts.clear()
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar cache: {e}")
            return False

    async def get_or_set(self, key: str, func, timeout: int = 300) -> Any:
        """
        Obter valor do cache ou executar função para definir
        func: função assíncrona que retorna o valor
        """
        try:
            value = await self.get(key)
            if value is None:
                value = await func()
                await self.set(key, value, timeout)
            return value
        except Exception as e:
            self.logger.logger.error(f"Erro em get_or_set: {e}")
            return None

    def _is_expired(self, key: str) -> bool:
        """Verificar se o cache expirou"""
        if key in self._timeouts:
            return datetime.now() > self._timeouts[key]
        return True

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Obter lock para operações concorrentes"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def start_cleanup(self):
        """Iniciar limpeza automática de cache expirado"""
        try:
            while True:
                await self._cleanup_expired()
                await asyncio.sleep(60)  # Executar a cada minuto
        except Exception as e:
            self.logger.logger.error(f"Erro na limpeza do cache: {e}")

    async def _cleanup_expired(self):
        """Limpar itens expirados do cache"""
        try:
            expired_keys = [
                key for key in self._cache.keys()
                if self._is_expired(key)
            ]
            for key in expired_keys:
                await self.delete(key)
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar itens expirados: {e}")

    async def get_stats(self) -> dict:
        """Obter estatísticas do cache"""
        try:
            total_items = len(self._cache)
            expired_items = len([
                key for key in self._cache.keys()
                if self._is_expired(key)
            ])
            
            return {
                'total_items': total_items,
                'expired_items': expired_items,
                'active_items': total_items - expired_items,
                'memory_usage': self._get_memory_usage()
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def _get_memory_usage(self) -> int:
        """Calcular uso aproximado de memória"""
        try:
            import sys
            return sum(
                sys.getsizeof(value)
                for value in self._cache.values()
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao calcular uso de memória: {e}")
            return 0

    async def export_cache(self, file_path: str) -> bool:
        """Exportar cache para arquivo"""
        try:
            cache_data = {
                'data': self._cache,
                'timeouts': {
                    k: v.isoformat()
                    for k, v in self._timeouts.items()
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(cache_data, f)
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao exportar cache: {e}")
            return False

    async def import_cache(self, file_path: str) -> bool:
        """Importar cache de arquivo"""
        try:
            with open(file_path, 'r') as f:
                cache_data = json.load(f)
                
            self._cache = cache_data['data']
            self._timeouts = {
                k: datetime.fromisoformat(v)
                for k, v in cache_data['timeouts'].items()
            }
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao importar cache: {e}")
            return False