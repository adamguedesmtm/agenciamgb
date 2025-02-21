"""
Plugin Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:33:26
"""

import os
import json
import shutil
import requests
from pathlib import Path
from .logger import Logger

class PluginManager:
    def __init__(self):
        self.logger = Logger('plugin_manager')
        self.plugins_dir = Path('/opt/cs2server/cs2/plugins')
        self.config_dir = Path('/opt/cs2server/config/plugins')
        self.plugins_db = self.config_dir / 'plugins.json'

        # Criar diretórios necessários
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar banco de dados de plugins
        if not self.plugins_db.exists():
            self._create_plugins_db()

    def _create_plugins_db(self):
        initial_db = {
            'installed': {},
            'available': {},
            'last_update': None
        }
        self._save_plugins_db(initial_db)

    def _save_plugins_db(self, data):
        with open(self.plugins_db, 'w') as f:
            json.dump(data, f, indent=4)

    def _load_plugins_db(self):
        with open(self.plugins_db, 'r') as f:
            return json.load(f)

    async def install_plugin(self, plugin_name, version='latest'):
        try:
            db = self._load_plugins_db()
            
            if plugin_name in db['installed']:
                self.logger.logger.warning(f"Plugin {plugin_name} já está instalado")
                return False

            # Download do plugin
            plugin_url = f"https://api.github.com/repos/{plugin_name}/releases/{version}"
            response = requests.get(plugin_url)
            
            if response.status_code != 200:
                self.logger.logger.error(f"Erro ao baixar plugin {plugin_name}")
                return False

            # Instalar plugin
            plugin_data = response.json()
            assets_url = plugin_data['assets'][0]['browser_download_url']
            
            # Download e extração
            plugin_file = self.plugins_dir / f"{plugin_name}.zip"
            with open(plugin_file, 'wb') as f:
                f.write(requests.get(assets_url).content)

            # Extrair plugin
            shutil.unpack_archive(plugin_file, self.plugins_dir / plugin_name)
            plugin_file.unlink()

            # Atualizar banco de dados
            db['installed'][plugin_name] = {
                'version': plugin_data['tag_name'],
                'installed_at': datetime.utcnow().isoformat(),
                'config_file': str(self.config_dir / f"{plugin_name}.cfg")
            }
            self._save_plugins_db(db)

            self.logger.logger.info(f"Plugin {plugin_name} instalado com sucesso")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao instalar plugin {plugin_name}: {e}")
            return False

    async def remove_plugin(self, plugin_name):
        try:
            db = self._load_plugins_db()
            
            if plugin_name not in db['installed']:
                self.logger.logger.warning(f"Plugin {plugin_name} não está instalado")
                return False

            # Remover arquivos
            plugin_dir = self.plugins_dir / plugin_name
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            # Remover configuração
            config_file = Path(db['installed'][plugin_name]['config_file'])
            if config_file.exists():
                config_file.unlink()

            # Atualizar banco de dados
            del db['installed'][plugin_name]
            self._save_plugins_db(db)

            self.logger.logger.info(f"Plugin {plugin_name} removido com sucesso")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover plugin {plugin_name}: {e}")
            return False

    async def update_plugin(self, plugin_name):
        try:
            db = self._load_plugins_db()
            
            if plugin_name not in db['installed']:
                self.logger.logger.warning(f"Plugin {plugin_name} não está instalado")
                return False

            # Backup da configuração atual
            config_file = Path(db['installed'][plugin_name]['config_file'])
            if config_file.exists():
                backup_file = config_file.with_suffix('.bak')
                shutil.copy2(config_file, backup_file)

            # Remover versão atual
            await self.remove_plugin(plugin_name)

            # Instalar nova versão
            success = await self.install_plugin(plugin_name)

            if success:
                # Restaurar configuração
                if backup_file.exists():
                    shutil.move(backup_file, config_file)
                
                self.logger.logger.info(f"Plugin {plugin_name} atualizado com sucesso")
                return True
            else:
                self.logger.logger.error(f"Falha ao atualizar plugin {plugin_name}")
                return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar plugin {plugin_name}: {e}")
            return False