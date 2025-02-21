"""
Configuration Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:17:07
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from .logger import Logger
from .state_manager import StateManager

class ConfigManager:
    def __init__(self, state_manager: StateManager):
        self.logger = Logger('config_manager')
        self.state_manager = state_manager
        self.config_dir = Path('/opt/cs2server/config')
        self.config_file = self.config_dir / 'server_config.json'
        self._config = {}
        self._defaults = self._get_defaults()
        
        # Criar diretório se não existir
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _get_defaults(self) -> Dict:
        """Obter configurações padrão"""
        return {
            'server': {
                'name': 'CS2 Server',
                'tickrate': 128,
                'maxplayers': 16,
                'map': 'de_dust2',
                'gamemode': 'competitive',
                'password': '',
                'rcon_password': os.getenv('RCON_PASSWORD', ''),
                'sv_lan': 0
            },
            'matchmaking': {
                'enabled': True,
                'min_players': 10,
                'warmup_time': 60,
                'match_time': 1800,
                'knife_round': True
            },
            'admins': {
                'super_admin': os.getenv('ADMIN_STEAM_ID', ''),
                'admin_group': 'admin',
                'mod_group': 'mod'
            },
            'plugins': {
                'enabled': True,
                'auto_update': True,
                'blocked_plugins': []
            },
            'logging': {
                'level': 'INFO',
                'file_size': 10485760,  # 10MB
                'backup_count': 5,
                'log_chat': True,
                'log_kills': True,
                'log_damage': True
            },
            'discord': {
                'enabled': True,
                'bot_token': os.getenv('BOT_TOKEN', ''),
                'channel_admin': os.getenv('CHANNEL_ADMIN', ''),
                'channel_status': os.getenv('CHANNEL_STATUS', ''),
                'channel_events': os.getenv('CHANNEL_EVENTS', '')
            }
        }

    async def load(self):
        """Carregar configurações"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Mesclar com padrões
                self._config = self._merge_configs(self._defaults, loaded_config)
            else:
                # Usar padrões se arquivo não existe
                self._config = self._defaults.copy()
                await self.save()
                
            # Atualizar estado
            await self.state_manager.set_state('config', self._config)
            
            self.logger.logger.info("Configurações carregadas")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar configurações: {e}")
            return False

    async def save(self):
        """Salvar configurações"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
                
            # Atualizar estado
            await self.state_manager.set_state('config', self._config)
            
            self.logger.logger.info("Configurações salvas")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar configurações: {e}")
            return False

    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Mesclar configurações customizadas com padrões"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result

    async def get(self, path: str, default: Any = None) -> Any:
        """
        Obter valor de configuração por caminho
        Ex: server.name, matchmaking.enabled
        """
        try:
            current = self._config
            for key in path.split('.'):
                if key not in current:
                    return default
                current = current[key]
            return current
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter configuração: {e}")
            return default

    async def set(self, path: str, value: Any) -> bool:
        """
        Definir valor de configuração por caminho
        Ex: server.name = "New Server"
        """
        try:
            keys = path.split('.')
            current = self._config
            
            # Navegar até o penúltimo nível
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
                
            # Definir valor
            current[keys[-1]] = value
            
            # Salvar alterações
            await self.save()
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir configuração: {e}")
            return False

    async def delete(self, path: str) -> bool:
        """Deletar configuração por caminho"""
        try:
            keys = path.split('.')
            current = self._config
            
            # Navegar até o penúltimo nível
            for key in keys[:-1]:
                if key not in current:
                    return False
                current = current[key]
                
            # Deletar valor
            if keys[-1] in current:
                del current[keys[-1]]
                await self.save()
                return True
            return False
        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar configuração: {e}")
            return False

    async def reset(self, path: str = None) -> bool:
        """
        Resetar configurações para padrões
        Se path for especificado, reseta apenas aquela seção
        """
        try:
            if path:
                keys = path.split('.')
                default_value = self._defaults
                for key in keys:
                    if key not in default_value:
                        return False
                    default_value = default_value[key]
                
                await self.set(path, default_value)
            else:
                self._config = self._defaults.copy()
                await self.save()
            
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar configurações: {e}")
            return False

    async def validate(self) -> Dict[str, list]:
        """Validar configurações"""
        try:
            errors = {}
            
            # Validar servidor
            server = self._config.get('server', {})
            if not server.get('name'):
                self._add_error(errors, 'server.name', 'Nome do servidor é obrigatório')
            if not 1 <= server.get('maxplayers', 0) <= 64:
                self._add_error(errors, 'server.maxplayers', 'Máximo de jogadores deve ser entre 1 e 64')
                
            # Validar matchmaking
            mm = self._config.get('matchmaking', {})
            if mm.get('enabled'):
                if not 2 <= mm.get('min_players', 0) <= server.get('maxplayers', 16):
                    self._add_error(
                        errors,
                        'matchmaking.min_players',
                        'Mínimo de jogadores inválido'
                    )
                    
            # Validar Discord
            discord = self._config.get('discord', {})
            if discord.get('enabled'):
                if not discord.get('bot_token'):
                    self._add_error(
                        errors,
                        'discord.bot_token',
                        'Token do bot é obrigatório'
                    )
                    
            return errors
        except Exception as e:
            self.logger.logger.error(f"Erro ao validar configurações: {e}")
            return {'general': [str(e)]}

    def _add_error(self, errors: Dict[str, list], path: str, message: str):
        """Adicionar erro de validação"""
        if path not in errors:
            errors[path] = []
        errors[path].append(message)

    async def export_config(self, filename: str) -> bool:
        """Exportar configurações para arquivo"""
        try:
            # Remover senhas e tokens
            safe_config = self._config.copy()
            if 'server' in safe_config:
                safe_config['server']['password'] = '***'
                safe_config['server']['rcon_password'] = '***'
            if 'discord' in safe_config:
                safe_config['discord']['bot_token'] = '***'
                
            with open(filename, 'w') as f:
                json.dump(safe_config, f, indent=4)
                
            self.logger.logger.info(f"Configurações exportadas para {filename}")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao exportar configurações: {e}")
            return False

    async def import_config(self, filename: str) -> bool:
        """Importar configurações de arquivo"""
        try:
            with open(filename, 'r') as f:
                new_config = json.load(f)
                
            # Validar estrutura básica
            if not isinstance(new_config, dict):
                raise ValueError("Formato de configuração inválido")
                
            # Mesclar com configurações existentes
            self._config = self._merge_configs(self._config, new_config)
            
            # Validar e salvar
            errors = await self.validate()
            if not errors:
                await self.save()
                return True
            else:
                self.logger.logger.error(f"Erros de validação: {errors}")
                return False
        except Exception as e:
            self.logger.logger.error(f"Erro ao importar configurações: {e}")
            return False