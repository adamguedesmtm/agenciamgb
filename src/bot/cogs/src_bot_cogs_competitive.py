from discord.ext import commands
import discord

class Competitive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def queue5v5(self, ctx):
        """Entrar na fila 5v5"""
        # Implementar lógica
        pass

async def setup(bot):
    await bot.add_cog(Competitive(bot))