"""
Plugin Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:43:01
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
from .logger import Logger

class Plugin:
    def __init__(self, name: str, module: Any):
        self.name = name
        self.module = module
        self.enabled = False
        self.config = {}
        self.dependencies = []
        self.version = getattr(module, '__version__', '0.1.0')
        self.author = getattr(module, '__author__', 'Unknown')
        self.description = getattr(module, '__description__', '')

class PluginManager:
    def __init__(self):
        self.logger = Logger('plugin_manager')
        self.plugins_dir = Path('/opt/cs2server/plugins')
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[callable]] = {}

    async def load_plugins(self):
        """Carregar todos os plugins disponíveis"""
        try:
            # Adicionar diretório de plugins ao PATH
            sys.path.append(str(self.plugins_dir))

            # Procurar por arquivos Python
            for file in self.plugins_dir.glob('*.py'):
                if file.stem.startswith('_'):
                    continue

                try:
                    # Importar módulo
                    module = importlib.import_module(file.stem)
                    
                    # Verificar interface necessária
                    if not hasattr(module, 'setup') or not hasattr(module, 'teardown'):
                        continue

                    # Criar instância do plugin
                    plugin = Plugin(file.stem, module)
                    
                    # Carregar metadados
                    if hasattr(module, 'PLUGIN_CONFIG'):
                        plugin.config = module.PLUGIN_CONFIG
                    if hasattr(module, 'PLUGIN_DEPENDENCIES'):
                        plugin.dependencies = module.PLUGIN_DEPENDENCIES

                    self._plugins[plugin.name] = plugin
                    self.logger.logger.info(f"Plugin {plugin.name} carregado")

                except Exception as e:
                    self.logger.logger.error(f"Erro ao carregar plugin {file.stem}: {e}")

        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar plugins: {e}")

    async def enable_plugin(self, name: str) -> bool:
        """Habilitar plugin específico"""
        try:
            if name not in self._plugins:
                raise ValueError(f"Plugin {name} não encontrado")

            plugin = self._plugins[name]
            
            # Verificar dependências
            for dep in plugin.dependencies:
                if dep not in self._plugins or not self._plugins[dep].enabled:
                    raise ValueError(f"Dependência não satisfeita: {dep}")

            # Chamar setup do plugin
            if not plugin.enabled:
                await plugin.module.setup(plugin.config)
                plugin.enabled = True
                
                # Registrar hooks
                self._register_plugin_hooks(plugin)
                
                self.logger.logger.info(f"Plugin {name} habilitado")
            
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao habilitar plugin {name}: {e}")
            return False

    async def disable_plugin(self, name: str) -> bool:
        """Desabilitar plugin específico"""
        try:
            if name not in self._plugins:
                raise ValueError(f"Plugin {name} não encontrado")

            plugin = self._plugins[name]
            
            # Verificar plugins dependentes
            for other in self._plugins.values():
                if name in other.dependencies and other.enabled:
                    await self.disable_plugin(other.name)

            # Chamar teardown do plugin
            if plugin.enabled:
                await plugin.module.teardown()
                plugin.enabled = False
                
                # Remover hooks
                self._unregister_plugin_hooks(plugin)
                
                self.logger.logger.info(f"Plugin {name} desabilitado")
            
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao desabilitar plugin {name}: {e}")
            return False

    def _register_plugin_hooks(self, plugin: Plugin):
        """Registrar hooks do plugin"""
        try:
            for name, member in inspect.getmembers(plugin.module):
                if hasattr(member, '_hook'):
                    hook_name = getattr(member, '_hook')
                    if hook_name not in self._hooks:
                        self._hooks[hook_name] = []
                    self._hooks[hook_name].append(member)

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar hooks: {e}")

    def _unregister_plugin_hooks(self, plugin: Plugin):
        """Remover hooks do plugin"""
        try:
            for hook_name in list(self._hooks.keys()):
                self._hooks[hook_name] = [
                    h for h in self._hooks[hook_name]
                    if h.__module__ != plugin.module.__name__
                ]
                if not self._hooks[hook_name]:
                    del self._hooks[hook_name]

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover hooks: {e}")

    async def call_hook(self, hook_name: str, *args, **kwargs):
        """Chamar hooks registrados"""
        try:
            if hook_name in self._hooks:
                results = []
                for hook in self._hooks[hook_name]:
                    try:
                        result = hook(*args, **kwargs)
                        if inspect.iscoroutine(result):
                            result = await result
                        results.append(result)
                    except Exception as e:
                        self.logger.logger.error(f"Erro ao executar hook: {e}")
                return results
            return []

        except Exception as e:
            self.logger.logger.error(f"Erro ao chamar hooks: {e}")
            return []

    async def reload_plugin(self, name: str) -> bool:
        """Recarregar plugin específico"""
        try:
            if name not in self._plugins:
                raise ValueError(f"Plugin {name} não encontrado")

            # Desabilitar primeiro
            was_enabled = self._plugins[name].enabled
            if was_enabled:
                await self.disable_plugin(name)

            # Recarregar módulo
            module = importlib.reload(self._plugins[name].module)
            
            # Recriar plugin
            plugin = Plugin(name, module)
            if hasattr(module, 'PLUGIN_CONFIG'):
                plugin.config = module.PLUGIN_CONFIG
            if hasattr(module, 'PLUGIN_DEPENDENCIES'):
                plugin.dependencies = module.PLUGIN_DEPENDENCIES

            self._plugins[name] = plugin

            # Reabilitar se necessário
            if was_enabled:
                await self.enable_plugin(name)

            self.logger.logger.info(f"Plugin {name} recarregado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao recarregar plugin {name}: {e}")
            return False

    def get_plugin_info(self, name: str) -> Optional[Dict]:
        """Obter informações do plugin"""
        try:
            if name not in self._plugins:
                return None

            plugin = self._plugins[name]
            return {
                'name': plugin.name,
                'enabled': plugin.enabled,
                'version': plugin.version,
                'author': plugin.author,
                'description': plugin.description,
                'dependencies': plugin.dependencies,
                'config': plugin.config
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do plugin: {e}")
            return None

    def list_plugins(self) -> List[Dict]:
        """Listar todos os plugins"""
        try:
            return [
                self.get_plugin_info(name)
                for name in self._plugins
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar plugins: {e}")
            return []

    async def update_plugin_config(self, name: str, config: Dict) -> bool:
        """Atualizar configuração do plugin"""
        try:
            if name not in self._plugins:
                raise ValueError(f"Plugin {name} não encontrado")

            plugin = self._plugins[name]
            
            # Mesclar configurações
            plugin.config.update(config)
            
            # Se plugin está ativo, recarregar
            if plugin.enabled:
                await self.reload_plugin(name)
            
            self.logger.logger.info(f"Configuração do plugin {name} atualizada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar config do plugin: {e}")
            return False