"""
Update Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:32:22
"""

import os
import sys
import aiohttp
import subprocess
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from .logger import Logger
from .backup_manager import BackupManager

class UpdateManager:
    def __init__(self, backup_manager: BackupManager):
        self.logger = Logger('update_manager')
        self.backup_manager = backup_manager
        self._update_lock = asyncio.Lock()
        self._checking = False
        self._updating = False
        self._last_check = None
        self._current_version = None
        self._latest_version = None

    async def check_updates(self) -> Dict:
        """Verificar atualizações disponíveis"""
        try:
            if self._checking:
                return {'status': 'checking'}

            self._checking = True
            try:
                # Obter versão atual
                current = await self._get_current_version()
                if not current:
                    raise ValueError("Não foi possível determinar versão atual")

                # Verificar última versão
                latest = await self._get_latest_version()
                if not latest:
                    raise ValueError("Não foi possível obter última versão")

                self._current_version = current
                self._latest_version = latest
                self._last_check = datetime.now()

                return {
                    'current_version': current,
                    'latest_version': latest,
                    'update_available': latest > current,
                    'last_check': self._last_check.isoformat()
                }

            finally:
                self._checking = False

        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar atualizações: {e}")
            return {'error': str(e)}

    async def update_server(self, backup: bool = True) -> Dict:
        """Atualizar servidor"""
        try:
            if self._updating:
                return {'status': 'updating'}

            async with self._update_lock:
                self._updating = True
                try:
                    # Verificar atualizações primeiro
                    check_result = await self.check_updates()
                    if 'error' in check_result:
                        raise ValueError(check_result['error'])

                    if not check_result['update_available']:
                        return {'status': 'latest'}

                    # Criar backup se solicitado
                    if backup:
                        backup_path = await self.backup_manager.create_backup('pre_update')
                        if not backup_path:
                            raise ValueError("Falha ao criar backup")

                    # Parar servidor
                    if not await self._stop_server():
                        raise ValueError("Falha ao parar servidor")

                    # Baixar e aplicar atualização
                    if not await self._download_update():
                        raise ValueError("Falha ao baixar atualização")

                    if not await self._apply_update():
                        raise ValueError("Falha ao aplicar atualização")

                    # Iniciar servidor
                    if not await self._start_server():
                        raise ValueError("Falha ao iniciar servidor")

                    # Verificar nova versão
                    new_version = await self._get_current_version()

                    return {
                        'status': 'success',
                        'old_version': self._current_version,
                        'new_version': new_version,
                        'backup_path': backup_path if backup else None
                    }

                finally:
                    self._updating = False

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar servidor: {e}")
            return {'error': str(e)}

    async def _get_current_version(self) -> Optional[str]:
        """Obter versão atual do servidor"""
        try:
            # Implementar lógica específica para obter versão
            result = subprocess.run(
                ['steamcmd', '+app_info_print', '730'],
                capture_output=True,
                text=True
            )
            
            # Parsear saída para obter versão
            # Este é um exemplo simplificado
            version = "1.0.0"  # Substituir com parsing real
            return version

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter versão atual: {e}")
            return None

    async def _get_latest_version(self) -> Optional[str]:
        """Obter última versão disponível"""
        try:
            async with aiohttp.ClientSession() as session:
                # URL da API do Steam para CS2
                url = "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/"
                params = {
                    'appid': '730',
                    'version': '0'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['response']['required_version']
                        
            return None

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter última versão: {e}")
            return None

    async def _stop_server(self) -> bool:
        """Parar servidor CS2"""
        try:
            # Implementar lógica de parada do servidor
            subprocess.run(['systemctl', 'stop', 'cs2server'], check=True)
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao parar servidor: {e}")
            return False

    async def _download_update(self) -> bool:
        """Baixar atualização"""
        try:
            # Usar SteamCMD para baixar atualização
            result = subprocess.run([
                'steamcmd',
                '+login', 'anonymous',
                '+app_update', '730',
                '+quit'
            ], check=True)
            
            return result.returncode == 0

        except Exception as e:
            self.logger.logger.error(f"Erro ao baixar atualização: {e}")
            return False

    async def _apply_update(self) -> bool:
        """Aplicar atualização"""
        try:
            # Implementar lógica de aplicação da atualização
            # Por exemplo, copiar arquivos, atualizar configs, etc.
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao aplicar atualização: {e}")
            return False

    async def _start_server(self) -> bool:
        """Iniciar servidor CS2"""
        try:
            # Implementar lógica de início do servidor
            subprocess.run(['systemctl', 'start', 'cs2server'], check=True)
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar servidor: {e}")
            return False

    async def get_update_status(self) -> Dict:
        """Obter status da atualização"""
        return {
            'checking': self._checking,
            'updating': self._updating,
            'current_version': self._current_version,
            'latest_version': self._latest_version,
            'last_check': self._last_check.isoformat() if self._last_check else None
        }

    async def rollback_update(self, backup_path: str) -> bool:
        """Reverter para versão anterior usando backup"""
        try:
            if not await self.backup_manager.verify_backup(backup_path):
                raise ValueError("Backup inválido ou corrompido")

            # Parar servidor
            if not await self._stop_server():
                raise ValueError("Falha ao parar servidor")

            # Restaurar backup
            if not await self.backup_manager.restore_backup(backup_path):
                raise ValueError("Falha ao restaurar backup")

            # Iniciar servidor
            if not await self._start_server():
                raise ValueError("Falha ao iniciar servidor")

            self.logger.logger.info(f"Rollback concluído usando {backup_path}")
            