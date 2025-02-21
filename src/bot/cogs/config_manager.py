"""
Configuration Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:17:58
"""

from typing import Dict, Any
import json
import os

class ConfigManager:
    def __init__(self, config_path: str = "/opt/cs2server/config.json"):
        self.config_path = config_path
        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carregar configuração do arquivo"""
        if not os.path.exists(self.config_path):
            return self._create_default_config()
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Criar configuração padrão"""
        default_config = {
            'servers': {
                'competitive': {
                    'port': 27015,
                    'rcon_password': 'your_rcon_password',
                    'hostname': 'CS2 Competitive Server',
                    'maxplayers': 12
                },
                'wingman': {
                    'port': 27016,
                    'rcon_password': 'your_rcon_password',
                    'hostname': 'CS2 Wingman Server',
                    'maxplayers': 4
                },
                'retake': {
                    'port': 27017,
                    'rcon_password': 'your_rcon_password',
                    'hostname': 'CS2 Retake Server',
                    'maxplayers': 10
                }
            },
            'discord': {
                'token': 'your_discord_token',
                'channel_id': 'your_channel_id'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'cs2bot',
                'user': 'cs2bot',
                'password': 'your_db_password'
            }
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            
        return default_config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obter valor de configuração
        
        Args:
            key: Chave da configuração (usa pontos para níveis)
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou default
        """
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        """
        Definir valor de configuração
        
        Args:
            key: Chave da configuração
            value: Novo valor
            
        Returns:
            True se salvo com sucesso
        """
        try:
            keys = key.split('.')
            config = self._config
            
            # Navegar até o último nível
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # Definir valor
            config[keys[-1]] = value
            
            # Salvar arquivo
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
                
            return True
            
        except Exception as e:
            print(f"Erro ao definir config: {e}")
            return False