"""
Configuration Validator
Author: adamguedesmtm
Created: 2025-02-21 03:33:26
"""

import os
import json
import yaml
from pathlib import Path
from .logger import Logger

class ConfigValidator:
    def __init__(self):
        self.logger = Logger('config_validator')
        self.config_dir = Path('/opt/cs2server/config')
        self.schemas_dir = self.config_dir / 'schemas'

    async def validate_all_configs(self):
        try:
            results = {
                'valid': [],
                'invalid': [],
                'errors': []
            }

            # Validar configurações do CS2
            cs2_result = await self._validate_cs2_configs()
            results.update(cs2_result)

            # Validar configurações do Bot
            bot_result = await self._validate_bot_configs()
            results.update(bot_result)

            # Validar configurações do Matchzy
            matchzy_result = await self._validate_matchzy_configs()
            results.update(matchzy_result)

            return results

        except Exception as e:
            self.logger.logger.error(f"Erro ao validar configurações: {e}")
            return None

    async def _validate_cs2_configs(self):
        cs2_configs = {
            'server.cfg': {
                'required_vars': [
                    'hostname',
                    'sv_setsteamaccount',
                    'rcon_password'
                ]
            },
            'admins.cfg': {
                'format': r'STEAM_[0-5]:[0-1]:\d+'
            }
        }

        results = []
        for config, rules in cs2_configs.items():
            config_path = self.config_dir / 'cs2' / config
            if not config_path.exists():
                results.append({
                    'file': config,
                    'valid': False,
                    'error': 'Arquivo não encontrado'
                })
                continue

            with open(config_path, 'r') as f:
                content = f.read()

            # Validar variáveis obrigatórias
            if 'required_vars' in rules:
                for var in rules['required_vars']:
                    if var not in content:
                        results.append({
                            'file': config,
                            'valid': False,
                            'error': f'Variável {var} não encontrada'
                        })

            # Validar formato
            if 'format' in rules:
                import re
                if not re.search(rules['format'], content):
                    results.append({
                        'file': config,
                        'valid': False,
                        'error': 'Formato inválido'
                    })

        return results

    async def _validate_bot_configs(self):
        env_file = self.config_dir / '.env'
        required_vars = [
            'BOT_TOKEN',
            'CHANNEL_ADMIN',
            'CHANNEL_STATUS',
            'DB_USER',
            'DB_PASSWORD'
        ]

        results = []
        if not env_file.exists():
            results.append({
                'file': '.env',
                'valid': False,
                'error': 'Arquivo não encontrado'
            })
            return results

        with open(env_file, 'r') as f:
            content = f.read()

        for var in required_vars:
            if var not in content:
                results.append({
                    'file': '.env',
                    'valid': False,
                    'error': f'Variável {var} não encontrada'
                })

        return results

    async def _validate_matchzy_configs(self):
        matchzy_config = self.config_dir / 'matchzy' / 'config.json'
        
        results = []
        if not matchzy_config.exists():
            results.append({
                'file': 'config.json',
                'valid': False,
                'error': 'Arquivo não encontrado'
            })
            return results

        try:
            with open(matchzy_config, 'r') as f:
                config = json.load(f)

            required_keys = [
                'api_key',
                'server_ip',
                'server_port',
                'rcon_password'
            ]

            for key in required_keys:
                if key not in config:
                    results.append({
                        'file': 'config.json',
                        'valid': False,
                        'error': f'Chave {key} não encontrada'
                    })

        except json.JSONDecodeError:
            results.append({
                'file': 'config.json',
                'valid': False,
                'error': 'JSON inválido'
            })

        return results