"""
Backup Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:32:22
"""

import os
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
from .logger import Logger

class BackupManager:
    def __init__(self):
        self.logger = Logger('backup_manager')
        self.backup_dir = Path('/opt/cs2server/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 10
        self._backup_lock = asyncio.Lock()

    async def create_backup(self, name: str = None) -> Optional[str]:
        """Criar novo backup"""
        try:
            async with self._backup_lock:
                # Gerar nome do backup
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{name}_{timestamp}" if name else timestamp
                backup_path = self.backup_dir / f"{backup_name}.tar.gz"

                # Diretórios para backup
                dirs_to_backup = [
                    '/opt/cs2server/config',
                    '/opt/cs2server/data',
                    '/opt/cs2server/logs'
                ]

                # Criar arquivo tar.gz
                with tarfile.open(backup_path, 'w:gz') as tar:
                    for dir_path in dirs_to_backup:
                        dir_path = Path(dir_path)
                        if dir_path.exists():
                            tar.add(
                                dir_path,
                                arcname=dir_path.name
                            )

                # Limpar backups antigos
                await self._cleanup_old_backups()

                self.logger.logger.info(f"Backup criado: {backup_path}")
                return str(backup_path)

        except Exception as e:
            self.logger.logger.error(f"Erro ao criar backup: {e}")
            return None

    async def restore_backup(self, backup_path: str) -> bool:
        """Restaurar backup"""
        try:
            async with self._backup_lock:
                backup_path = Path(backup_path)
                if not backup_path.exists():
                    raise FileNotFoundError(f"Backup não encontrado: {backup_path}")

                # Criar backup antes de restaurar
                await self.create_backup('pre_restore')

                # Diretórios de destino
                restore_dirs = [
                    '/opt/cs2server/config',
                    '/opt/cs2server/data',
                    '/opt/cs2server/logs'
                ]

                # Limpar diretórios de destino
                for dir_path in restore_dirs:
                    dir_path = Path(dir_path)
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                    dir_path.mkdir(parents=True)

                # Extrair backup
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall('/opt/cs2server')

                self.logger.logger.info(f"Backup restaurado: {backup_path}")
                return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar backup: {e}")
            return False

    async def list_backups(self) -> List[Dict]:
        """Listar backups disponíveis"""
        try:
            backups = []
            for file in self.backup_dir.glob('*.tar.gz'):
                try:
                    stats = file.stat()
                    backups.append({
                        'name': file.stem,
                        'path': str(file),
                        'size': stats.st_size,
                        'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
                except Exception as e:
                    self.logger.logger.error(f"Erro ao ler backup {file}: {e}")

            return sorted(
                backups,
                key=lambda x: x['created'],
                reverse=True
            )

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar backups: {e}")
            return []

    async def delete_backup(self, backup_path: str) -> bool:
        """Deletar backup específico"""
        try:
            async with self._backup_lock:
                backup_path = Path(backup_path)
                if backup_path.exists():
                    backup_path.unlink()
                    self.logger.logger.info(f"Backup deletado: {backup_path}")
                    return True
                return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar backup: {e}")
            return False

    async def _cleanup_old_backups(self):
        """Limpar backups antigos mantendo apenas max_backups"""
        try:
            backups = await self.list_backups()
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    await self.delete_backup(backup['path'])

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar backups antigos: {e}")

    async def verify_backup(self, backup_path: str) -> bool:
        """Verificar integridade do backup"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return False

            # Tentar abrir e listar conteúdo
            with tarfile.open(backup_path, 'r:gz') as tar:
                try:
                    tar.getmembers()
                    return True
                except Exception:
                    return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar backup: {e}")
            return False

    async def get_backup_info(self, backup_path: str) -> Optional[Dict]:
        """Obter informações detalhadas do backup"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return None

            stats = backup_path.stat()
            
            # Contar arquivos e tamanho total
            with tarfile.open(backup_path, 'r:gz') as tar:
                members = tar.getmembers()
                total_files = len(members)
                total_size = sum(m.size for m in members)

            return {
                'name': backup_path.stem,
                'path': str(backup_path),
                'size': stats.st_size,
                'compressed_ratio': stats.st_size / total_size if total_size > 0 else 0,
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'total_files': total_files,
                'total_size': total_size
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do backup: {e}")
            return None

    async def schedule_backup(self, interval: int):
        """Agendar backup automático"""
        try:
            while True:
                await self.create_backup('scheduled')
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.logger.error(f"Erro no backup agendado: {e}")