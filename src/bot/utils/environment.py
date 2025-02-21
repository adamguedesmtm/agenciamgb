"""
Environment Configuration Manager
Author: adamguedesmtm
Created: 2025-02-21 04:25:18
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from .logger import Logger

class Environment:
    def __init__(self):
        self.logger = Logger('environment')
        self.env_file = Path('/opt/cs2server/config/.env')
        self.config_dir = Path('/opt/cs2server/config')
        
        # Carregar variáveis de ambiente
        self._load_env()
        
    def _load_env(self):
        """Carregar variáveis de ambiente"""
        try:
            if not self.env_file.exists():
                self._create_default_env()
                
            load_dotenv(self.env_file)
            self.logger.logger.info("Variáveis de ambiente carregadas")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar variáveis de ambiente: {e}")
            raise

    def _create_default_env(self):
        """Criar arquivo .env padrão"""
        try:
            default_env = {
                'BOT_TOKEN': 'your_bot_token_here',
                'CHANNEL_ADMIN': 'channel_id_here',
                'CHANNEL_STATUS': 'channel_id_here',
                'CHANNEL_EVENTS': 'channel_id_here',
                'DB_USER': 'cs2server',
                'DB_PASSWORD': 'your_password_here',
                'DB_NAME': 'cs2server',
                'DB_HOST': 'localhost',
                'DB_PORT': '5432',
                'SERVER_IP': 'your_server_ip',
                'SERVER_PORT': '27015',
                'RCON_PASSWORD': 'your_rcon_password',
                'STEAM_API_KEY': 'your_steam_api_key',
                'ADMIN_ROLE_ID': 'role_id_here',
                'DEBUG_MODE': 'False'
            }
            
            env_content = '\n'.join(f'{k}={v}' for k, v in default_env.items())
            
            self.env_file.parent.mkdir(parents=True, exist_ok=True)
            self.env_file.write_text(env_content)
            
            self.logger.logger.info("Arquivo .env padrão criado")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar arquivo .env: {e}")
            raise

    def get_required_env(self, var_name: str) -> str:
        """Obter variável de ambiente obrigatória"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Variável de ambiente {var_name} não definida")
        return value

    def get_optional_env(self, var_name: str, default: str = None) -> str:
        """Obter variável de ambiente opcional"""
        return os.getenv(var_name, default)

    def update_env(self, updates: dict):
        """Atualizar variáveis de ambiente"""
        try:
            # Ler conteúdo atual
            current_env = {}
            if self.env_file.exists():
                content = self.env_file.read_text()
                for line in content.splitlines():
                    if '=' in line:
                        key, value = line.split('=', 1)
                        current_env[key.strip()] = value.strip()

            # Atualizar com novos valores
            current_env.update(updates)

            # Salvar arquivo atualizado
            env_content = '\n'.join(f'{k}={v}' for k, v in current_env.items())
            self.env_file.write_text(env_content)

            # Recarregar variáveis
            load_dotenv(self.env_file, override=True)
            
            self.logger.logger.info("Variáveis de ambiente atualizadas")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar variáveis de ambiente: {e}")
            raise

    def validate_env(self) -> bool:
        """Validar variáveis de ambiente necessárias"""
        required_vars = [
            'BOT_TOKEN',
            'CHANNEL_ADMIN',
            'DB_USER',
            'DB_PASSWORD',
            'SERVER_IP',
            'RCON_PASSWORD'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.logger.logger.error(
                f"Variáveis de ambiente faltando: {', '.join(missing_vars)}"
            )
            return False

        return True

    def export_config(self, file_path: str):
        """Exportar configuração atual"""
        try:
            config = {
                'env': {},
                'server': self._load_server_config(),
                'bot': self._load_bot_config()
            }

            # Adicionar variáveis de ambiente (exceto senhas)
            sensitive_vars = {'BOT_TOKEN', 'DB_PASSWORD', 'RCON_PASSWORD', 'STEAM_API_KEY'}
            for key, value in os.environ.items():
                if key.startswith(('BOT_', 'DB_', 'SERVER_', 'CHANNEL_')):
                    if key not in sensitive_vars:
                        config['env'][key] = value

            with open(file_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.logger.logger.info(f"Configuração exportada para {file_path}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao exportar configuração: {e}")
            raise

    def _load_server_config(self) -> dict:
        """Carregar configuração do servidor"""
        try:
            config_file = self.config_dir / 'server_config.json'
            if config_file.exists():
                return json.loads(config_file.read_text())
            return {}
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar config do servidor: {e}")
            return {}

    def _load_bot_config(self) -> dict:
        """Carregar configuração do bot"""
        try:
            config_file = self.config_dir / 'bot_config.json'
            if config_file.exists():
                return json.loads(config_file.read_text())
            return {}
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar config do bot: {e}")
            return {}