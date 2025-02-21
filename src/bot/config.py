"""
Configuration Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 12:13:05
"""

import os
from pathlib import Path
from typing import Dict, Any
import json
import yaml

# Diretório base do projeto
BASE_DIR = Path('/opt/cs2server')

# Diretórios principais
CONFIG_DIR = BASE_DIR / 'config'
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
CACHE_DIR = BASE_DIR / 'cache'
TEMP_DIR = BASE_DIR / 'temp'

# Arquivo de configuração principal
CONFIG_FILE = CONFIG_DIR / 'config.yaml'

# Configurações padrão
DEFAULT_CONFIG = {
    # Configurações do Servidor
    'server': {
        'host': '0.0.0.0',
        'port': 27015,
        'max_players': 64,
        'tickrate': 128,
        'map_rotation': True,
        'default_map': 'de_dust2',
    },
    
    # Configurações do Bot
    'bot': {
        'name': 'CS2Bot',
        'prefix': '!',
        'language': 'pt_BR',
        'timezone': 'America/Sao_Paulo',
        'max_memory': '2G',
        'debug_mode': False,
    },
    
    # Configurações de API
    'api': {
        'enabled': True,
        'port': 8080,
        'cors_origins': ['*'],
        'rate_limit': {
            'enabled': True,
            'requests_per_minute': 60
        },
        'timeout': 30,
    },
    
    # Configurações de Database
    'database': {
        'type': 'sqlite',
        'path': str(DATA_DIR / 'database.db'),
        'backup_enabled': True,
        'backup_interval': 86400,  # 24 horas
        'max_connections': 10,
    },
    
    # Configurações de Cache
    'cache': {
        'type': 'redis',
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'ttl': 3600,
    },
    
    # Configurações de Logging
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'file_enabled': True,
        'console_enabled': True,
        'max_size': '10MB',
        'backup_count': 5,
    },
    
    # Configurações de Métricas
    'metrics': {
        'enabled': True,
        'collection_interval': 60,
        'retention_days': 30,
        'prometheus_enabled': True,
        'prometheus_port': 9090,
    },
    
    # Configurações de Segurança
    'security': {
        'admin_steam_ids': [],
        'banned_steam_ids': [],
        'password_required': False,
        'server_password': '',
        'rcon_password': '',
        'ssl_enabled': False,
        'ssl_cert': '',
        'ssl_key': '',
    },
    
    # Configurações de Plugin
    'plugins': {
        'enabled': True,
        'auto_load': True,
        'reload_on_change': True,
        'disabled_plugins': [],
    },
    
    # Configurações de Notificação
    'notifications': {
        'enabled': True,
        'discord_webhook': '',
        'telegram_token': '',
        'email': {
            'enabled': False,
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_pass': '',
            'from_address': '',
        },
    },
    
    # Configurações de Jobs
    'jobs': {
        'enabled': True,
        'max_concurrent': 5,
        'max_retries': 3,
        'retry_delay': 60,
    },
    
    # Configurações de Estado
    'state': {
        'persistence_enabled': True,
        'save_interval': 300,
        'max_history': 1000,
    },
    
    # Configurações de Performance
    'performance': {
        'thread_pool_size': 4,
        'process_pool_size': 2,
        'io_pool_size': 4,
        'max_memory_percent': 80,
        'gc_interval': 3600,
    }
}

class Config:
    """Gerenciador de Configurações"""
    
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self._load_config()
        self._validate_paths()

    def _load_config(self):
        """Carregar configurações do arquivo"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(user_config)
        except Exception as e:
            print(f"Erro ao carregar config: {e}")

    def _merge_config(self, user_config: Dict):
        """Mesclar configurações do usuário"""
        def merge_dict(base: Dict, update: Dict):
            for key, value in update.items():
                if (key in base and 
                    isinstance(base[key], dict) and
                    isinstance(value, dict)):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
                    
        merge_dict(self._config, user_config)

    def _validate_paths(self):
        """Validar e criar diretórios necessários"""
        directories = [
            CONFIG_DIR,
            DATA_DIR,
            LOGS_DIR,
            CACHE_DIR,
            TEMP_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def save(self):
        """Salvar configurações em arquivo"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(
                    self._config,
                    f,
                    default_flow_style=False,
                    sort_keys=False
                )
        except Exception as e:
            print(f"Erro ao salvar config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Obter valor de configuração"""
        try:
            value = self._config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Definir valor de configuração"""
        try:
            parts = key.split('.')
            config = self._config
            
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
                
            config[parts[-1]] = value
            
        except Exception as e:
            print(f"Erro ao definir config: {e}")

    def update(self, updates: Dict):
        """Atualizar múltiplas configurações"""
        self._merge_config(updates)

    def reset(self, key: str = None):
        """Resetar configurações para padrão"""
        if key:
            try:
                parts = key.split('.')
                if len(parts) == 1:
                    self._config[key] = DEFAULT_CONFIG[key]
                else:
                    config = self._config
                    default = DEFAULT_CONFIG
                    
                    for part in parts[:-1]:
                        config = config[part]
                        default = default[part]
                        
                    config[parts[-1]] = default[parts[-1]]
                    
            except (KeyError, TypeError):
                pass
        else:
            self._config = DEFAULT_CONFIG.copy()

# Instância global de configuração
config = Config()