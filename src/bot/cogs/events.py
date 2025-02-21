"""
Event Handler for CS2 Bot
Author: adamguedesmtm
Created: 2025-02-21 03:37:32
"""

import discord
from discord.ext import commands
from datetime import datetime
from ..utils.logger import Logger

class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('event_handler')

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento disparado quando o bot está pronto"""
        self.logger.logger.info(f'Bot iniciado como {self.bot.user.name}')
        await self.bot.change_presence(
            activity=discord.Game(name="CS2 Server Monitor")
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handler global de erros de comandos"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Comando não encontrado!")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")
        else:
            self.logger.logger.error(f"Erro no comando {ctx.command}: {error}")
            await ctx.send(f"❌ Erro ao executar o comando: {str(error)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Evento disparado quando um membro entra no servidor"""
        welcome_channel = self.bot.get_channel(int(os.getenv('WELCOME_CHANNEL')))
        if welcome_channel:
            embed = discord.Embed(
                title="👋 Bem-vindo!",
                description=f"Olá {member.mention}! Bem-vindo ao servidor!",
                color=0x00ff00
            )
            embed.add_field(
                name="📢 Servidor CS2",
                value=f"IP: {os.getenv('SERVER_IP')}:{os.getenv('SERVER_PORT')}",
                inline=False
            )
            embed.add_field(
                name="❓ Precisa de ajuda?",
                value="Use !help para ver os comandos disponíveis",
                inline=False
            )
            await welcome_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Evento disparado quando uma mensagem é enviada"""
        # Ignorar mensagens do próprio bot
        if message.author == self.bot.user:
            return

        # Registrar mensagens do canal de admin
        if message.channel.id == int(os.getenv('CHANNEL_ADMIN')):
            self.logger.logger.info(
                f"Mensagem admin de {message.author}: {message.content}"
            )

def setup(bot):
    bot.add_cog(EventHandler(bot))