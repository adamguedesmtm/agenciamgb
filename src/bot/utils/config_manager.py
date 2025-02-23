"""
Configuration Manager
Author: adamguedesmtm
Created: 2025-02-21 13:49:37
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import os
from .logger import Logger

class ConfigManager:
    def __init__(self):
        self.logger = Logger('config_manager')
        self.config_dir = Path('/opt/cs2server/config')
        self.config_file = self.config_dir / 'config.json'
        self.defaults = self._get_defaults()
        self.config = {}
        self.load_config()

    def _get_defaults(self) -> Dict:
        """Configurações padrão"""
        return {
            'servers': {
                'competitive': {
                    'host': 'localhost',
                    'port': 27015,
                    'rcon_password': '',
                    'server_password': '',
                    'maps': [
                        'de_dust2', 'de_mirage', 'de_inferno',
                        'de_overpass', 'de_ancient', 'de_anubis'
                    ]
                },
                'wingman': {
                    'host': 'localhost',
                    'port': 27016,
                    'rcon_password': '',
                    'server_password': '',
                    'maps': [
                        'de_lake', 'de_shortdust', 'de_vertigo'
                    ]
                },
                'retake': {
                    'host': 'localhost',
                    'port': 27017,
                    'rcon_password': '',
                    'server_password': '',
                    'maps': [
                        'de_dust2', 'de_mirage', 'de_inferno'
                    ]
                }
            },
            'queue': {
                'competitive': {
                    'min_players': 10,
                    'max_players': 10,
                    'timeout': 300
                },
                'wingman': {
                    'min_players': 4,
                    'max_players': 4,
                    'timeout': 180
                },
                'retake': {
                    'min_players': 6,
                    'max_players': 10,
                    'timeout': 120
                }
            },
            'matchzy': {
                'api_key': '',
                'api_url': 'http://localhost:8080'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'cs2bot',
                'user': 'cs2bot',
                'password': ''
            },
            'discord': {
                'prefix': '!',
                'admin_role': 'Admin',
                'channels': {
                    'notifications': '',
                    'commands': '',
                    'admin': ''
                }
            },
            'duckdns': {
                'enabled': False,
                'domain': '',
                'token': ''
            },
            'upnp': {
                'enabled': False
            }
        }

    def load_config(self):
        """Carregar configurações do arquivo"""
        try:
            if not self.config_file.exists():
                self.config = self.defaults
                self.save_config()
                return

            with open(self.config_file, 'r') as f:
                self.config = json.load(f)

            # Atualizar com valores padrão faltantes
            self._update_missing_defaults(self.config, self.defaults)

        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar config: {e}")
            self.config = self.defaults

    def _update_missing_defaults(self, config: Dict, defaults: Dict):
        """Atualizar configurações faltantes com valores padrão"""
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self._update_missing_defaults(config[key], value)

    def save_config(self):
        """Salvar configurações no arquivo"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.logger.info("Configurações salvas com sucesso")
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Obter valor de configuração"""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Definir valor de configuração"""
        try:
            keys = key.split('.')
            target = self.config
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self.save_config()
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir config: {e}")
            return False