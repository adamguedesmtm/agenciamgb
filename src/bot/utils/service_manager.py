"""
Service Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:17:07
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from .logger import Logger

class Service:
    def __init__(self, name: str, start_func: Callable, stop_func: Callable):
        self.name = name
        self.start_func = start_func
        self.stop_func = stop_func
        self.running = False
        self.start_time = None
        self.stop_time = None
        self.error = None
        self.retries = 0
        self.max_retries = 3

class ServiceManager:
    def __init__(self):
        self.logger = Logger('service_manager')
        self._services: Dict[str, Service] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._startup_order: List[str] = []

    async def register_service(self, 
                             name: str, 
                             start_func: Callable,
                             stop_func: Callable,
                             dependencies: List[str] = None):
        """Registrar novo serviço"""
        try:
            if name in self._services:
                raise ValueError(f"Serviço {name} já registrado")

            service = Service(name, start_func, stop_func)
            self._services[name] = service
            self._locks[name] = asyncio.Lock()
            
            if dependencies:
                self._dependencies[name] = dependencies
                
            # Atualizar ordem de inicialização
            self._update_startup_order()
            
            self.logger.logger.info(f"Serviço {name} registrado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar serviço: {e}")
            raise

    async def start_service(self, name: str) -> bool:
        """Iniciar serviço"""
        try:
            if name not in self._services:
                raise ValueError(f"Serviço {name} não encontrado")

            service = self._services[name]
            
            # Verificar dependências
            if name in self._dependencies:
                for dep in self._dependencies[name]:
                    if not self._services[dep].running:
                        raise ValueError(
                            f"Dependência {dep} não está rodando"
                        )

            async with self._locks[name]:
                if service.running:
                    return True

                try:
                    await service.start_func()
                    service.running = True
                    service.start_time = datetime.now()
                    service.error = None
                    service.retries = 0
                    
                    self.logger.logger.info(f"Serviço {name} iniciado")
                    return True
                    
                except Exception as e:
                    service.error = str(e)
                    service.retries += 1
                    
                    if service.retries < service.max_retries:
                        self.logger.logger.warning(
                            f"Tentando reiniciar serviço {name}: {e}"
                        )
                        await asyncio.sleep(2 ** service.retries)  # Backoff
                        return await self.start_service(name)
                    else:
                        self.logger.logger.error(
                            f"Erro ao iniciar serviço {name}: {e}"
                        )
                        return False
                        
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar serviço: {e}")
            return False

    async def stop_service(self, name: str) -> bool:
        """Parar serviço"""
        try:
            if name not in self._services:
                raise ValueError(f"Serviço {name} não encontrado")

            service = self._services[name]
            
            # Verificar dependentes
            for dep_name, deps in self._dependencies.items():
                if name in deps and self._services[dep_name].running:
                    await self.stop_service(dep_name)

            async with self._locks[name]:
                if not service.running:
                    return True

                try:
                    await service.stop_func()
                    service.running = False
                    service.stop_time = datetime.now()
                    
                    self.logger.logger.info(f"Serviço {name} parado")
                    return True
                    
                except Exception as e:
                    service.error = str(e)
                    self.logger.logger.error(
                        f"Erro ao parar serviço {name}: {e}"
                    )
                    return False
                    
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar serviço: {e}")
            return False

    async def restart_service(self, name: str) -> bool:
        """Reiniciar serviço"""
        try:
            await self.stop_service(name)
            await asyncio.sleep(1)  # Pequeno delay entre stop e start
            return await self.