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
            return await self.start_service(name)
        except Exception as e:
            self.logger.logger.error(f"Erro ao reiniciar serviço: {e}")
            return False

    async def start_all(self) -> Dict[str, bool]:
        """Iniciar todos os serviços na ordem correta"""
        try:
            results = {}
            for name in self._startup_order:
                results[name] = await self.start_service(name)
            return results
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar todos os serviços: {e}")
            return {}

    async def stop_all(self) -> Dict[str, bool]:
        """Parar todos os serviços na ordem reversa"""
        try:
            results = {}
            for name in reversed(self._startup_order):
                results[name] = await self.stop_service(name)
            return results
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar todos os serviços: {e}")
            return {}

    def _update_startup_order(self):
        """Atualizar ordem de inicialização baseado em dependências"""
        try:
            # Algoritmo de ordenação topológica
            visited = set()
            temp = set()
            order = []

            def visit(name):
                if name in temp:
                    raise ValueError(f"Dependência cíclica detectada: {name}")
                if name not in visited:
                    temp.add(name)
                    for dep in self._dependencies.get(name, []):
                        visit(dep)
                    temp.remove(name)
                    visited.add(name)
                    order.append(name)

            for name in self._services:
                if name not in visited:
                    visit(name)

            self._startup_order = order
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar ordem de inicialização: {e}")
            raise

    async def get_service_status(self, name: str) -> Optional[Dict]:
        """Obter status do serviço"""
        try:
            if name not in self._services:
                return None

            service = self._services[name]
            return {
                'name': name,
                'running': service.running,
                'start_time': service.start_time,
                'stop_time': service.stop_time,
                'uptime': (datetime.now() - service.start_time).total_seconds() if service.running else 0,
                'error': service.error,
                'retries': service.retries,
                'dependencies': self._dependencies.get(name, [])
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status do serviço: {e}")
            return None

    async def get_all_status(self) -> Dict[str, Dict]:
        """Obter status de todos os serviços"""
        try:
            return {
                name: await self.get_service_status(name)
                for name in self._services
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status de todos os serviços: {e}")
            return {}

    def get_startup_order(self) -> List[str]:
        """Obter ordem de inicialização dos serviços"""
        return self._startup_order.copy()

    async def add_dependency(self, service: str, depends_on: str):
        """Adicionar dependência entre serviços"""
        try:
            if service not in self._services:
                raise ValueError(f"Serviço {service} não encontrado")
            if depends_on not in self._services:
                raise ValueError(f"Serviço dependente {depends_on} não encontrado")

            if service not in self._dependencies:
                self._dependencies[service] = []
            
            if depends_on not in self._dependencies[service]:
                self._dependencies[service].append(depends_on)
                
            # Atualizar ordem de inicialização
            self._update_startup_order()
            
            self.logger.logger.info(
                f"Dependência adicionada: {service} -> {depends_on}"
            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar dependência: {e}")
            raise

    async def remove_dependency(self, service: str, depends_on: str):
        """Remover dependência entre serviços"""
        try:
            if service in self._dependencies:
                self._dependencies[service].remove(depends_on)
                if not self._dependencies[service]:
                    del self._dependencies[service]
                    
                # Atualizar ordem de inicialização
                self._update_startup_order()
                
                self.logger.logger.info(
                    f"Dependência removida: {service} -> {depends_on}"
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover dependência: {e}")