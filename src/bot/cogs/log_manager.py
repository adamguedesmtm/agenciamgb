"""
Log Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:59:51
"""

import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta
from ..utils.logger import Logger

class LogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('log_manager')
        self.log_dir = "/opt/cs2server/logs"
        self.log_types = {
            'cs2': f"{self.log_dir}/cs2",
            'bot': f"{self.log_dir}/bot",
            'system': f"{self.log_dir}/system",
            'matchzy': f"{self.log_dir}/matchzy"
        }

    @commands.command(name='logs')
    @commands.has_role('Admin')
    async def view_logs(self, ctx, log_type: str = 'cs2', lines: int = 20):
        """Ver logs do servidor"""
        if log_type not in self.log_types:
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.log_types.keys())}"
            )
            return

        try:
            logs = await self._get_recent_logs(log_type, lines)
            
            if not logs:
                await ctx.send("❌ Nenhum log encontrado!")
                return

            # Dividir logs em chunks para não exceder limite do Discord
            chunks = [logs[i:i + 1900] for i in range(0, len(logs), 1900)]
            
            for chunk in chunks:
                await ctx.send(f"```\n{chunk}\n```")
                
            self.logger.logger.info(
                f"Logs {log_type} visualizados por {ctx.author}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao visualizar logs: {e}")
            await ctx.send("❌ Erro ao obter logs")

    @commands.command(name='errorlogs')
    @commands.has_role('Admin')
    async def view_error_logs(self, ctx, log_type: str = 'cs2', hours: int = 24):
        """Ver logs de erro"""
        if log_type not in self.log_types:
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.log_types.keys())}"
            )
            return

        try:
            errors = await self._get_error_logs(log_type, hours)
            
            if not errors:
                await ctx.send("✅ Nenhum erro encontrado!")
                return

            embed = discord.Embed(
                title=f"⚠️ Logs de Erro - {log_type}",
                description=f"Últimas {hours} horas",
                color=0xff0000
            )

            # Agrupar erros similares
            error_groups = {}
            for error in errors:
                if error['message'] in error_groups:
                    error_groups[error['message']]['count'] += 1
                    error_groups[error['message']]['times'].append(error['time'])
                else:
                    error_groups[error['message']] = {
                        'count': 1,
                        'times': [error['time']]
                    }

            for message, data in error_groups.items():
                embed.add_field(
                    name=f"Erro (x{data['count']})",
                    value=f"```{message}```\nÚltima ocorrência: {data['times'][-1]}",
                    inline=False
                )

            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao visualizar logs de erro: {e}")
            await ctx.send("❌ Erro ao obter logs de erro")

    @commands.command(name='clearlogs')
    @commands.has_role('Admin')
    async def clear_logs(self, ctx, log_type: str = 'all', days: int = 30):
        """Limpar logs antigos"""
        if log_type not in self.log_types and log_type != 'all':
            await ctx.send(
                f"❌ Tipo inválido! Tipos: {', '.join(self.log_types.keys() + ['all'])}"
            )
            return

        try:
            message = await ctx.send("🔄 Limpando logs...")
            
            if log_type == 'all':
                types_to_clear = self.log_types.keys()
            else:
                types_to_clear = [log_type]

            total_cleared = 0
            for ltype in types_to_clear:
                cleared = await self._clear_old_logs(ltype, days)
                total_cleared += cleared
                await message.edit(
                    content=f"🔄 Limpando {ltype}... ({cleared} arquivos removidos)"
                )

            await message.edit(
                content=f"✅ {total_cleared} arquivos de log removidos!"
            )
            self.logger.logger.info(
                f"Logs limpos por {ctx.author}: {total_cleared} arquivos"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar logs: {e}")
            await ctx.send("❌ Erro ao limpar logs")

    async def _get_recent_logs(self, log_type: str, lines: int):
        """Obter logs recentes"""
        try:
            log_file = self._get_latest_log_file(log_type)
            if not log_file:
                return None

            # Usar tail para obter últimas linhas
            cmd = f"tail -n {lines} {log_file}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            return stdout.decode()
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter logs recentes: {e}")
            return None

    async def _get_error_logs(self, log_type: str, hours: int):
        """Obter logs de erro"""
        try:
            log_file = self._get_latest_log_file(log_type)
            if not log_file:
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            errors = []

            # Procurar por erros no arquivo de log
            cmd = f"grep -i 'error\\|exception' {log_file}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            for line in stdout.decode().splitlines():
                try:
                    # Parsing simplificado, ajustar conforme formato real dos logs
                    time_str = line[:19]  # Assumindo formato "YYYY-MM-DD HH:MM:SS"
                    log_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    
                    if log_time >= cutoff_time:
                        errors.append({
                            'time': time_str,
                            'message': line[20:]
                        })
                except:
                    continue

            return errors
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter logs de erro: {e}")
            return []

    async def _clear_old_logs(self, log_type: str, days: int):
        """Limpar logs antigos"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            log_dir = self.log_types[log_type]
            count = 0

            for file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, file)
                if os.path.getctime(file_path) < cutoff_time.timestamp():
                    os.remove(file_path)
                    count += 1

            return count
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar logs antigos: {e}")
            return 0

    def _get_latest_log_file(self, log_type: str):
        """Obter arquivo de log mais recente"""
        try:
            log_dir = self.log_types[log_type]
            files = os.listdir(log_dir)
            
            if not files:
                return None

            return os.path.join(
                log_dir,
                max(files, key=lambda x: os.path.getctime(
                    os.path.join(log_dir, x)
                ))
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter arquivo de log: {e}")
            return None

def setup(bot):
    bot.add_cog(LogManager(bot))