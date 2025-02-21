"""
Error Handler
Author: adamguedesmtm
Created: 2025-02-21
"""

import traceback
from discord.ext import commands
import os

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Comando não encontrado!")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão!")
        else:
            error_trace = ''.join(
                traceback.format_exception(
                    type(error), 
                    error, 
                    error.__traceback__
                )
            )
            self.bot.logger.logger.error(f"Erro não tratado: {error_trace}")
            
            # Notificar canal admin
            admin_channel = self.bot.get_channel(
                int(os.getenv('CHANNEL_ADMIN'))
            )
            if admin_channel:
                await admin_channel.send(
                    f"⚠️ **Erro não tratado**\n```{error}```"
                )