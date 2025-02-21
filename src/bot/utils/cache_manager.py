"""
Cache Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:05:50
"""

import time
from typing import Any, Dict, Optional, Set
from datetime import datetime, timedelta
import asyncio
from .logger import Logger

class CacheManager:
    def __init__(self):
        self.logger = Logger('cache_manager')
        self._cache: Dict[str, Dict] = {}
        self._expiry_times: Dict[str, float] = {}
        self._cleanup_task = None
        self._tags: Dict[str, Set[str]] = {}
        self._tag_keys: Dict[str, Set[str]] = {}

    async def start(self):
        """Iniciar gerenciador de cache"""
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.logger.info("Cache manager iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar cache manager: {e}")

    async def stop(self):
        """Parar gerenciador de cache"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            self.logger.logger.info("Cache manager parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar cache manager: {e}")

    async def set(self, 
                 key: str, 
                 value: Any, 
                 ttl: int = None,
                 tags: Set[str] = None) -> bool:
        """
        Definir valor no cache
        key: Chave do cache
        value: Valor a ser armazenado
        ttl: Tempo de vida em segundos
        tags: Tags para categorização
        """
        try:
            now = time.time()
            
            self._cache[key] = {
                'value': value,
                'created_at': now,
                'accessed_at': now,
                'access_count': 0
            }
            
            if ttl:
                self._expiry_times[key] = now + ttl
                
            if tags:
                self._tag_keys[key] = tags
                for tag in tags:
                    if tag not in self._tags:
                        self._tags[tag] = set()
                    self._tags[tag].add(key)
                    
            self.logger.logger.debug(f"Valor definido no cache: {key}")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao definir cache: {e}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """Obter valor do cache"""
        try:
            if key not in self._cache:
                return default
                
            # Verificar expiração
            if self._is_expired(key):
                await self.delete(key)
                return default
                
            # Atualizar estatísticas
            now = time.time()
            self._cache[key]['accessed_at'] = now
            self._cache[key]['access_count'] += 1
            
            return self._cache[key]['value']

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter cache: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """Deletar valor do cache"""
        try:
            if key in self._cache:
                del self._cache[key]
                if key in self._expiry_times:
                    del self._expiry_times[key]
                    
                # Remover das tags
                if key in self._tag_keys:
                    for tag in self._tag_keys[key]:
                        if tag in self._tags:
                            self._tags[tag].remove(key)
                            if not self._tags[tag]:
                                del self._tags[tag]
                    del self._tag_keys[key]
                    
                self.logger.logger.debug(f"Cache deletado: {key}")
                return True
            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar cache: {e}")
            return False

    def _is_expired(self, key: str) -> bool:
        """Verificar se cache expirou"""
        try:
            if key not in self._expiry_times:
                return False
            return time.time() >= self._expiry_times[key]
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar expiração: {e}")
            return True

    async def _cleanup_loop(self):
        """Loop de limpeza de cache expirado"""
        try:
            while True:
                try:
                    # Limpar itens expirados
                    for key in list(self._cache.keys()):
                        if self._is_expired(key):
                            await self.delete(key)
                            
                    await asyncio.sleep(60)  # Executar a cada minuto
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no cleanup: {e}")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            pass

    async def clear(self):
        """Limpar todo o cache"""
        try:
            self._cache.clear()
            self._expiry_times.clear()
            self._tags.clear()
            self._tag_keys.clear()
            self.logger.logger.info("Cache limpo")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar cache: {e}")

    async def clear_tag(self, tag: str) -> int:
        """Limpar cache por tag"""
        try:
            if tag not in self._tags:
                return 0
                
            keys = self._tags[tag].copy()
            count = 0
            
            for key in keys:
                if await self.delete(key):
                    count += 1
                    
            return count

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar tag: {e}")
            return 0

    async def get_stats(self) -> Dict:
        """Obter estatísticas do cache"""
        try:
            now = time.time()
            stats = {
                'total_items': len(self._cache),
                'expired_items': sum(
                    1 for k in self._cache if self._is_expired(k)
                ),
                'total_tags': len(self._tags),
                'memory_usage': self._estimate_memory_usage(),
                'tag_stats': {
                    tag: len(keys)
                    for tag, keys in self._tags.items()
                },
                'access_stats': {
                    key: {
                        'count': data['access_count'],
                        'last_access': now - data['accessed_at']
                    }
                    for key, data in self._cache.items()
                }
            }
            
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def _estimate_memory_usage(self) -> int:
        """Estimar uso de memória do cache"""
        try:
            import sys
            return sum(
                sys.getsizeof(str(k)) + sys.getsizeof(v['value'])
                for k, v in self._cache.items()
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao estimar memória: {e}")
            return 0

    async def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """Obter todos os valores de uma tag"""
        try:
            if tag not in self._tags:
                return {}
                
            result = {}
            for key in self._tags[tag]:
                value = await self.get(key)
                if value is not None:
                    result[key] = value
                    
            return result

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter por tag: {e}")
            return {}

    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """Estender tempo de vida do cache"""
        try:
            if key not in self._cache:
                return False
                
            self._expiry_times[key] = time.time() + ttl
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao estender TTL: {e}")
            return False