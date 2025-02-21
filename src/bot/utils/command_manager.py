"""
Command Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:30:48
"""

import inspect
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from .logger import Logger
from .permission_manager import PermissionManager

class Command:
    def __init__(self, 
                 name: str,
                 handler: Callable,
                 description: str = "",
                 permission: str = None,
                 aliases: List[str] = None,
                 cooldown: int = 0):
        self.name = name
        self.handler = handler
        self.description = description
        self.permission = permission
        self.aliases = aliases or []
        self.cooldown = cooldown
        self.last_use = {}  # user_id -> timestamp
        self.usage_count = 0
        self.enabled = True

class CommandManager:
    def __init__(self, permission_manager: PermissionManager):
        self.logger = Logger('command_manager')
        self.permissions = permission_manager
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}
        self._groups: Dict[str, List[str]] = {}

    def register_command(self,
                        name: str,
                        handler: Callable,
                        description: str = "",
                        permission: str = None,
                        aliases: List[str] = None,
                        cooldown: int = 0,
                        group: str = None) -> bool:
        """Registrar novo comando"""
        try:
            if name in self._commands:
                raise ValueError(f"Comando {name} já registrado")

            command = Command(
                name,
                handler,
                description,
                permission,
                aliases,
                cooldown
            )
            
            self._commands[name] = command
            
            # Registrar aliases
            if aliases:
                for alias in aliases:
                    if alias in self._aliases:
                        self.logger.logger.warning(
                            f"Alias {alias} já existe, sobrescrevendo"
                        )
                    self._aliases[alias] = name

            # Adicionar ao grupo
            if group:
                if group not in self._groups:
                    self._groups[group] = []
                self._groups[group].append(name)

            self.logger.logger.info(f"Comando {name} registrado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar comando: {e}")
            return False

    async def execute_command(self,
                            name: str,
                            user_id: str,
                            *args,
                            **kwargs) -> Any:
        """Executar comando"""
        try:
            # Verificar alias
            if name in self._aliases:
                name = self._aliases[name]

            if name not in self._commands:
                raise ValueError(f"Comando {name} não encontrado")

            command = self._commands[name]
            
            if not command.enabled:
                raise ValueError(f"Comando {name} está desabilitado")

            # Verificar permissão
            if command.permission:
                has_perm = await self.permissions.has_permission(
                    user_id,
                    command.permission
                )
                if not has_perm:
                    raise PermissionError(
                        f"Sem permissão para executar {name}"
                    )

            # Verificar cooldown
            now = datetime.utcnow().timestamp()
            if (command.cooldown > 0 and
                user_id in command.last_use and
                now - command.last_use[user_id] < command.cooldown):
                    remaining = int(
                        command.cooldown - (now - command.last_use[user_id])
                    )
                    raise ValueError(
                        f"Aguarde {remaining}s para usar {name} novamente"
                    )

            # Executar comando
            result = command.handler(*args, **kwargs)
            if inspect.iscoroutine(result):
                result = await result

            # Atualizar estatísticas
            command.last_use[user_id] = now
            command.usage_count += 1

            return result

        except Exception as e:
            self.logger.logger.error(f"Erro ao executar comando {name}: {e}")
            raise

    def unregister_command(self, name: str) -> bool:
        """Remover registro de comando"""
        try:
            if name not in self._commands:
                return False

            command = self._commands[name]
            
            # Remover aliases
            for alias, cmd in list(self._aliases.items()):
                if cmd == name:
                    del self._aliases[alias]

            # Remover de grupos
            for group in self._groups.values():
                if name in group:
                    group.remove(name)

            del self._commands[name]
            self.logger.logger.info(f"Comando {name} removido")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover comando: {e}")
            return False

    def get_command_info(self, name: str) -> Optional[Dict]:
        """Obter informações do comando"""
        try:
            # Verificar alias
            if name in self._aliases:
                name = self._aliases[name]

            if name not in self._commands:
                return None

            command = self._commands[name]
            return {
                'name': command.name,
                'description': command.description,
                'permission': command.permission,
                'aliases': command.aliases,
                'cooldown': command.cooldown,
                'usage_count': command.usage_count,
                'enabled': command.enabled,
                'groups': [
                    group for group, cmds in self._groups.items()
                    if name in cmds
                ]
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do comando: {e}")
            return None

    def list_commands(self, group: str = None) -> List[Dict]:
        """Listar comandos"""
        try:
            if group:
                if group not in self._groups:
                    return []
                commands = [
                    self._commands[name]
                    for name in self._groups[group]
                ]
            else:
                commands = self._commands.values()

            return [
                {
                    'name': cmd.name,
                    'description': cmd.description,
                    'permission': cmd.permission,
                    'aliases': cmd.aliases,
                    'usage_count': cmd.usage_count,
                    'enabled': cmd.enabled
                }
                for cmd in commands
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar comandos: {e}")
            return []

    def enable_command(self, name: str) -> bool:
        """Habilitar comando"""
        try:
            if name not in self._commands:
                return False

            self._commands[name].enabled = True
            self.logger.logger.info(f"Comando {name} habilitado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao habilitar comando: {e}")
            return False

    def disable_command(self, name: str) -> bool:
        """Desabilitar comando"""
        try:
            if name not in self._commands:
                return False

            self._commands[name].enabled = False
            self.logger.logger.info(f"Comando {name} desabilitado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao desabilitar comando: {e}")
            return False

    def update_command(self,
                      name: str,
                      description: str = None,
                      permission: str = None,
                      aliases: List[str] = None,
                      cooldown: int = None) -> bool:
        """Atualizar configuração do comando"""
        try:
            if name not in self._commands:
                return False

            command = self._commands[name]
            
            if description is not None:
                command.description = description
                
            if permission is not None:
                command.permission = permission
                
            if aliases is not None:
                # Remover aliases antigos
                for alias in command.aliases:
                    if alias in self._aliases:
                        del self._aliases[alias]
                        
                # Adicionar novos aliases
                command.aliases = aliases
                for alias in aliases:
                    self._aliases[alias] = name
                    
            if cooldown is not None:
                command.cooldown = cooldown

            self.logger.logger.info(f"Comando {name} atualizado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar comando: {e}")
            return False

    def get_command_usage(self, name: str) -> Dict:
        """Obter estatísticas de uso do comando"""
        try:
            if name not in self._commands:
                return {}

            command = self._commands[name]
            return {
                'total_uses': command.usage_count,
                'last_uses': {
                    user_id: timestamp
                    for user_id, timestamp in command.last_use.items()
                }
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter uso do comando: {e}")
            return {}

    def reset_cooldown(self, name: str, user_id: str = None) -> bool:
        """Resetar cooldown do comando"""
        try:
            if name not in self._commands:
                return False

            command = self._commands[name]
            
            if user_id:
                if user_id in command.last_use:
                    del command.last_use[user_id]
            else:
                command.last_use.clear()
                
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar cooldown: {e}")
            return False

    def get_groups(self) -> Dict[str, List[str]]:
        """Obter grupos de comandos"""
        return self._groups.copy()