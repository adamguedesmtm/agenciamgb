from discord.ext import commands
import discord

class Retakes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def queueretake(self, ctx):
        """Entrar na fila retake"""
        # Implementar lógica
        pass

async def setup(bot):
    await bot.add_cog(Retakes(bot))