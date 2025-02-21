"""
Configuration Cache for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:25:22
"""

from typing import Any, Dict, Optional
import json
from pathlib import Path
import asyncio
from .logger import Logger
from .cache_manager import CacheManager

class ConfigCache:
    def __init__(self, cache_manager: CacheManager):
        self.logger = Logger('config_cache')
        self.cache = cache_manager
        self._config_dir = Path('/opt/cs2server/config')
        self._config_file = self._config_dir / 'cache_config.json'
        self._default_ttl = 3600  # 1 hora
        self._initialized = False

    async def initialize(self):
        """Inicializar cache de configurações"""
        try:
            if self._initialized:
                return

            # Criar diretório se não existir
            self._config_dir.mkdir(parents=True, exist_ok=True)

            # Carregar configurações do arquivo
            if self._config_file.exists():
                await self._load_config()

            self._initialized = True
            self.logger.logger.info("Config cache inicializado")

        except Exception as e:
            self.logger.logger.error(f"Erro ao inicializar config cache: {e}")
            raise

    async def _load_config(self):
        """Carregar configurações do arquivo"""
        try:
            with open(self._config_file, 'r') as f:
                config = json.load(f)

            # Carregar configurações no cache
            for key, data in config.items():
                await self.cache.set(
                    f"config:{key}",
                    data['value'],
                    ttl=data.get('ttl', self._default_ttl)
                )

        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar config: {e}")

    async def _save_config(self):
        """Salvar configurações em arquivo"""
        try:
            config = {}
            for key in await self.list_keys():
                value = await self.get(key)
                if value is not None:
                    config[key] = {
                        'value': value,
                        'ttl': self._default_ttl
                    }

            with open(self._config_file, 'w') as f:
                json.dump(config, f, indent=4)

        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar config: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Obter valor da configuração"""
        try:
            return await self.cache.get(f"config:{key}", default)
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter config: {e}")
            return default

    async def set(self, 
                  key: str,
                  value: Any,
                  ttl: int = None,
                  persist: bool = True) -> bool:
        """
        Definir valor da configuração
        persist: Se True, salva em arquivo
        """
        try:
            success = await self.cache.set(
                f"config:{key}",
                value,
                ttl or self._default_ttl
            )
            
            if success and persist:
                await self._save_config()
                
            return success

        except Exception as e:
            self.logger.logger.error(f"Erro ao definir config: {e}")
            return False

    async def delete(self, key: str, persist: bool = True) -> bool:
        """Deletar configuração"""
        try:
            success = await self.cache.delete(f"config:{key}")
            
            if success and persist:
                await self._save_config()
                
            return success

        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar config: {e}")
            return False

    async def list_keys(self) -> list:
        """Listar todas as chaves de configuração"""
        try:
            stats = await self.cache.get_stats()
            return [
                k.replace('config:', '')
                for k in stats['access_stats'].keys()
                if k.startswith('config:')
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar configs: {e}")
            return []

    async def clear(self, persist: bool = True) -> bool:
        """Limpar todas as configurações"""
        try:
            keys = await self.list_keys()
            for key in keys:
                await self.delete(key, persist=False)
                
            if persist:
                await self._save_config()
                
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar configs: {e}")
            return False

    async def refresh(self, key: str, ttl: int = None) -> bool:
        """Atualizar TTL da configuração"""
        try:
            return await self.cache.extend_ttl(
                f"config:{key}",
                ttl or self._default_ttl
            )

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar TTL: {e}")
            return False

    async def bulk_set(self, 
                      configs: Dict[str, Any],
                      ttl: int = None,
                      persist: bool = True) -> bool:
        """Definir múltiplas configurações"""
        try:
            success = True
            for key, value in configs.items():
                if not await self.set(key, value, ttl, persist=False):
                    success = False
                    
            if success and persist:
                await self._save_config()
                
            return success

        except Exception as e:
            self.logger.logger.error(f"Erro ao definir configs em massa: {e}")
            return False

    async def get_all(self) -> Dict[str, Any]:
        """Obter todas as configurações"""
        try:
            result = {}
            for key in await self.list_keys():
                value = await self.get(key)
                if value is not None:
                    result[key] = value
            return result

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter todas as configs: {e}")
            return {}