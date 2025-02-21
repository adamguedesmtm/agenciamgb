"""
Admin Commands for CS2 Bot
Author: adamguedesmtm
Created: 2025-02-21 03:37:32
"""

import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
from ..utils.logger import Logger

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('admin_commands')
        self.admin_role_id = int(os.getenv('ADMIN_ROLE_ID'))

    def cog_check(self, ctx):
        """Verificar se o usuário tem permissão de admin"""
        return discord.utils.get(ctx.author.roles, id=self.admin_role_id) is not None

    @commands.command(name='restart')
    async def restart_server(self, ctx, service: str = 'all'):
        """Reiniciar serviços do servidor"""
        valid_services = ['cs2', 'bot', 'matchzy', 'all']
        
        if service not in valid_services:
            await ctx.send(f"❌ Serviço inválido. Use: {', '.join(valid_services)}")
            return

        try:
            message = await ctx.send(f"🔄 Reiniciando {service}...")
            
            if service == 'all':
                services = ['cs2server', 'cs2bot', 'matchzy']
            else:
                services = [f"{service}server" if service == 'cs2' else service]

            for srv in services:
                await self._restart_service(srv)
                await message.edit(content=f"✅ {srv} reiniciado!")
                await asyncio.sleep(1)

            self.logger.logger.info(f"Serviços reiniciados por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao reiniciar serviços: {e}")
            await ctx.send(f"❌ Erro ao reiniciar: {str(e)}")

    @commands.command(name='status')
    async def server_status(self, ctx):
        """Mostrar status detalhado do servidor"""
        try:
            embed = discord.Embed(
                title="📊 Status Detalhado do Servidor",
                description=f"Gerado em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                color=0x00ff00
            )

            # Status do Sistema
            system_stats = await self._get_system_stats()
            embed.add_field(
                name="💻 Sistema",
                value=f"CPU: {system_stats['cpu']}%\n"
                      f"RAM: {system_stats['memory']}%\n"
                      f"Disco: {system_stats['disk']}%\n"
                      f"Uptime: {system_stats['uptime']}",
                inline=False
            )

            # Status dos Serviços
            services_status = await self._get_services_status()
            embed.add_field(
                name="🔧 Serviços",
                value="\n".join(f"{name}: {'🟢' if status else '🔴'}" 
                               for name, status in services_status.items()),
                inline=False
            )

            # Status do Servidor CS2
            cs2_status = await self._get_cs2_status()
            embed.add_field(
                name="🎮 Servidor CS2",
                value=f"Players: {cs2_status['players']}/10\n"
                      f"Mapa: {cs2_status['map']}\n"
                      f"IP: {os.getenv('SERVER_IP')}:{os.getenv('SERVER_PORT')}",
                inline=False
            )

            await ctx.send(embed=embed)
            self.logger.logger.info(f"Status solicitado por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            await ctx.send(f"❌ Erro ao obter status: {str(e)}")

    @commands.command(name='ban')
    async def ban_player(self, ctx, steam_id: str, *, reason: str = "Sem motivo"):
        """Banir jogador do servidor"""
        try:
            # Validar Steam ID
            if not self._validate_steam_id(steam_id):
                await ctx.send("❌ Steam ID inválido!")
                return

            # Executar ban
            ban_command = f'sm_ban "{steam_id}" 0 "{reason}"'
            await self._execute_rcon(ban_command)

            # Registrar ban no banco de dados
            await self._register_ban(steam_id, reason, ctx.author.id)

            await ctx.send(f"✅ Jogador {steam_id} banido!\nMotivo: {reason}")
            self.logger.logger.info(f"Jogador {steam_id} banido por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao banir jogador: {e}")
            await ctx.send(f"❌ Erro ao banir jogador: {str(e)}")

    @commands.command(name='unban')
    async def unban_player(self, ctx, steam_id: str):
        """Desbanir jogador do servidor"""
        try:
            # Validar Steam ID
            if not self._validate_steam_id(steam_id):
                await ctx.send("❌ Steam ID inválido!")
                return

            # Executar unban
            unban_command = f'sm_unban "{steam_id}"'
            await self._execute_rcon(unban_command)

            # Atualizar banco de dados
            await self._remove_ban(steam_id)

            await ctx.send(f"✅ Jogador {steam_id} desbanido!")
            self.logger.logger.info(f"Jogador {steam_id} desbanido por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao desbanir jogador: {e}")
            await ctx.send(f"❌ Erro ao desbanir jogador: {str(e)}")

    async def _restart_service(self, service):
        """Reiniciar um serviço específico"""
        process = await asyncio.create_subprocess_shell(
            f'systemctl restart {service}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0

    async def _get_system_stats(self):
        """Obter estatísticas do sistema"""
        # Implementar lógica real
        return {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'uptime': '0h 0m'
        }

    async def _get_services_status(self):
        """Obter status dos serviços"""
        # Implementar lógica real
        return {
            'CS2': True,
            'Bot': True,
            'Matchzy': True
        }

    async def _get_cs2_status(self):
        """Obter status do servidor CS2"""
        # Implementar lógica real
        return {
            'players': 0,
            'map': 'unknown'
        }

    def _validate_steam_id(self, steam_id):
        """Validar formato do Steam ID"""
        import re
        pattern = r'^STEAM_[0-5]:[0-1]:\d+$'
        return bool(re.match(pattern, steam_id))

    async def _execute_rcon(self, command):
        """Executar comando RCON"""
        # Implementar lógica real
        pass

    async def _register_ban(self, steam_id, reason, admin_id):
        """Registrar ban no banco de dados"""
        # Implementar lógica real
        pass

    async def _remove_ban(self, steam_id):
        """Remover ban do banco de dados"""
        # Implementar lógica real
        pass

def setup(bot):
    bot.add_cog(AdminCommands(bot))