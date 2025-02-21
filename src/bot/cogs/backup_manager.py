"""
Backup Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:48:00
"""

import discord
from discord.ext import commands
import os
import asyncio
import shutil
from datetime import datetime
from ..utils.logger import Logger

class BackupManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('backup_manager')
        self.backup_dir = "/opt/cs2server/backups"
        self.backup_types = ['configs', 'database', 'demos']

    @commands.command(name='backup')
    @commands.has_role('Admin')
    async def create_backup(self, ctx, backup_type: str = 'all'):
        """Criar backup do servidor"""
        if backup_type not in self.backup_types + ['all']:
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.backup_types + ['all'])}"
            )
            return

        try:
            message = await ctx.send("🔄 Iniciando backup...")
            
            if backup_type == 'all':
                types_to_backup = self.backup_types
            else:
                types_to_backup = [backup_type]

            results = {}
            for btype in types_to_backup:
                success = await self._create_backup(btype)
                results[btype] = success
                await message.edit(
                    content=f"🔄 Backup em progresso...\n{btype}: "
                           f"{'✅' if success else '❌'}"
                )

            # Resumo final
            summary = "\n".join(
                f"{btype}: {'✅' if success else '❌'}"
                for btype, success in results.items()
            )
            
            embed = discord.Embed(
                title="📦 Resumo do Backup",
                description=summary,
                color=0x00ff00 if all(results.values()) else 0xff0000
            )
            
            await message.edit(content=None, embed=embed)
            self.logger.logger.info(
                f"Backup {backup_type} criado por {ctx.author}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar backup: {e}")
            await ctx.send("❌ Erro ao criar backup")

    @commands.command(name='listbackups')
    @commands.has_role('Admin')
    async def list_backups(self, ctx, backup_type: str = 'all'):
        """Listar backups disponíveis"""
        if backup_type not in self.backup_types + ['all']:
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.backup_types + ['all'])}"
            )
            return

        try:
            embed = discord.Embed(
                title="📦 Backups Disponíveis",
                color=0x00ff00
            )

            if backup_type == 'all':
                types_to_list = self.backup_types
            else:
                types_to_list = [backup_type]

            for btype in types_to_list:
                backups = await self._list_backups(btype)
                if backups:
                    value = "\n".join(
                        f"{b['date']} ({b['size']}MB)"
                        for b in backups[:5]
                    )
                    if len(backups) > 5:
                        value += f"\n... e mais {len(backups) - 5}"
                else:
                    value = "Nenhum backup encontrado"
                    
                embed.add_field(
                    name=f"{btype.capitalize()}",
                    value=value,
                    inline=False
                )

            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar backups: {e}")
            await ctx.send("❌ Erro ao listar backups")

    @commands.command(name='restore')
    @commands.has_role('Admin')
    async def restore_backup(self, ctx, backup_type: str, date: str):
        """Restaurar um backup"""
        if backup_type not in self.backup_types:
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.backup_types)}"
            )
            return

        try:
            message = await ctx.send("🔄 Iniciando restauração...")
            
            # Confirmar restauração
            await message.edit(
                content="⚠️ Isso irá sobrescrever os dados atuais. Continuar? "
                        "(sim/não)"
            )
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                response = await self.bot.wait_for('message', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await message.edit(content="❌ Tempo esgotado!")
                return

            if response.content.lower() != 'sim':
                await message.edit(content="❌ Restauração cancelada!")
                return

            # Realizar restauração
            success = await self._restore_backup(backup_type, date)
            
            if success:
                await message.edit(
                    content=f"✅ Backup {backup_type} de {date} restaurado!"
                )
                self.logger.logger.info(
                    f"Backup {backup_type} de {date} restaurado por {ctx.author}"
                )
            else:
                await message.edit(content="❌ Erro ao restaurar backup!")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar backup: {e}")
            await ctx.send("❌ Erro ao restaurar backup")

    async def _create_backup(self, backup_type):
        """Criar um backup específico"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self.backup_dir, 
                backup_type, 
                f"{backup_type}_{timestamp}.tar.gz"
            )

            if backup_type == 'configs':
                source = "/opt/cs2server/cs2/cfg"
            elif backup_type == 'database':
                # Executar dump do banco
                await self._create_db_dump(backup_path)
                return True
            elif backup_type == 'demos':
                source = "/opt/cs2server/demos/processed"

            # Criar arquivo tar.gz
            shutil.make_archive(
                backup_path[:-7],  # Remover .tar.gz
                'gztar',
                source
            )

            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar {backup_type} backup: {e}")
            return False

    async def _list_backups(self, backup_type):
        """Listar backups de um tipo específico"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_type)
            backups = []
            
            for file in os.listdir(backup_path):
                if file.endswith('.tar.gz'):
                    path = os.path.join(backup_path, file)
                    size = os.path.getsize(path) / (1024 * 1024)  # MB
                    date = datetime.fromtimestamp(
                        os.path.getctime(path)
                    ).strftime('%Y-%m-%d %H:%M')
                    
                    backups.append({
                        'file': file,
                        'size': f"{size:.1f}",
                        'date': date
                    })
                    
            return sorted(backups, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar backups: {e}")
            return []

    async def _restore_backup(self, backup_type, date):
        """Restaurar um backup específico"""
        try:
            backup_file = None
            backup_path = os.path.join(self.backup_dir, backup_type)
            
            # Encontrar arquivo de backup
            for file in os.listdir(backup_path):
                if date in file:
                    backup_file = os.path.join(backup_path, file)
                    break

            if not backup_file:
                return False

            if backup_type == 'configs':
                target = "/opt/cs2server/cs2/cfg"
            elif backup_type == 'database':
                # Restaurar dump do banco
                return await self._restore_db_dump(backup_file)
            elif backup_type == 'demos':
                target = "/opt/cs2server/demos/processed"

            # Extrair arquivo
            shutil.unpack_archive(backup_file, target)
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar backup: {e}")
            return False

    async def _create_db_dump(self, output_path):
        """Criar dump do banco de dados"""
        try:
            cmd = (
                f"PGPASSWORD={os.getenv('DB_PASSWORD')} pg_dump "
                f"-U {os.getenv('DB_USER')} "
                f"-d {os.getenv('DB_NAME')} "
                f"-f {output_path}"
            )
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erro no dump: {stderr.decode()}")
                
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar dump do banco: {e}")
            return False

    async def _restore_db_dump(self, dump_file):
        """Restaurar dump do banco de dados"""
        try:
            # Dropar conexões existentes
            drop_cmd = (
                f"PGPASSWORD={os.getenv('DB_PASSWORD')} psql "
                f"-U {os.getenv('DB_USER')} "
                f"-d {os.getenv('DB_NAME')} "
                "-c 'SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                f"WHERE datname = ''{os.getenv('DB_NAME')}'' "
                "AND pid <> pg_backend_pid();'"
            )
            
            await asyncio.create_subprocess_shell(drop_cmd)

            # Restaurar dump
            cmd = (
                f"PGPASSWORD={os.getenv('DB_PASSWORD')} psql "
                f"-U {os.getenv('DB_USER')} "
                f"-d {os.getenv('DB_NAME')} "
                f"-f {dump_file}"
            )
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Erro na restauração: {stderr.decode()}")
                
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao restaurar dump do banco: {e}")
            return False

def setup(bot):
    bot.add_cog(BackupManager(bot))