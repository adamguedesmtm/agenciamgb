"""
Update Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:53:43
"""

import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
from ..utils.logger import Logger

class UpdateManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('update_manager')
        self.steamcmd_path = "/opt/cs2server/steamcmd/steamcmd.sh"
        self.cs2_path = "/opt/cs2server/cs2"
        self.update_in_progress = False

    @commands.command(name='update')
    @commands.has_role('Admin')
    async def update_server(self, ctx, force: bool = False):
        """Atualizar servidor CS2"""
        if self.update_in_progress:
            await ctx.send("❌ Já existe uma atualização em andamento!")
            return

        try:
            self.update_in_progress = True
            message = await ctx.send("🔄 Verificando atualizações...")

            # Verificar se há atualização disponível
            if not force and not await self._check_update_available():
                await message.edit(content="✅ Servidor já está atualizado!")
                self.update_in_progress = False
                return

            # Backup antes da atualização
            await message.edit(content="📦 Criando backup...")
            if not await self._create_backup():
                await message.edit(
                    content="❌ Erro ao criar backup! Atualização cancelada."
                )
                self.update_in_progress = False
                return

            # Parar servidor
            await message.edit(content="🛑 Parando servidor...")
            await self._stop_server()

            # Atualizar
            await message.edit(content="🔄 Atualizando servidor...")
            success = await self._update_server()

            if success:
                # Iniciar servidor
                await message.edit(content="▶️ Iniciando servidor...")
                await self._start_server()
                
                await message.edit(
                    content="✅ Servidor atualizado e reiniciado com sucesso!"
                )
                self.logger.logger.info(f"Servidor atualizado por {ctx.author}")
            else:
                # Restaurar backup em caso de falha
                await message.edit(content="⚠️ Erro na atualização! Restaurando backup...")
                await self._restore_backup()
                await self._start_server()
                
                await message.edit(
                    content="❌ Erro na atualização! Backup restaurado."
                )
                
        except Exception as e:
            self.logger.logger.error(f"Erro na atualização: {e}")
            await ctx.send(f"❌ Erro durante a atualização: {str(e)}")
            
        finally:
            self.update_in_progress = False

    async def _check_update_available(self):
        """Verificar se há atualização disponível"""
        try:
            cmd = f"{self.steamcmd_path} +force_install_dir {self.cs2_path} +login anonymous +app_update 730 validate +quit"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode()
            
            return "Already up to date" not in output
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar atualizações: {e}")
            return False

    async def _create_backup(self):
        """Criar backup antes da atualização"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"/opt/cs2server/backups/pre_update_{timestamp}"
            
            # Backup das configurações
            shutil.copytree(
                f"{self.cs2_path}/game/csgo/cfg",
                f"{backup_path}/cfg"
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar backup: {e}")
            return False

    async def _stop_server(self):
        """Parar servidor CS2"""
        try:
            process = await asyncio.create_subprocess_shell(
                "systemctl stop cs2server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            await asyncio.sleep(5)  # Aguardar servidor parar
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar servidor: {e}")
            raise

    async def _update_server(self):
        """Atualizar servidor CS2"""
        try:
            cmd = f"{self.steamcmd_path} +force_install_dir {self.cs2_path} +login anonymous +app_update 730 validate +quit"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return process.returncode == 0
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar servidor: {e}")
            return False

    async def _start_server(self):
        """Iniciar servidor CS2"""
        try:
            process = await asyncio.create_subprocess_shell(
                "systemctl start cs2server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            await asyncio.sleep(10)  # Aguardar servidor iniciar
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar servidor: {e}")
            raise

    async def _restore_backup(self):
        """Restaurar backup em caso de falha"""
        try:
            # Encontrar backup mais recente
            backup_dir = "/opt/cs2server/backups"
            backups = sorted(
                [d for d in os.listdir(backup_dir) if d.startswith('pre_update_')],
                reverse=True
            )
            
            if not backups:
                raise Exception("Nenhum backup encontrado")

            latest_backup = os.path.join(backup_dir, backups[0])
            
            # Restaurar configurações
            shutil.rmtree(f"{self.cs2_path}/game/csgo/cfg")
            shutil.copytree(
                f"{latest_backup}/cfg",
                f"{self.cs2_path}/game/csgo/cfg"
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar backup: {e}")
            return False

def setup(bot):
    bot.add_cog(UpdateManager(bot))