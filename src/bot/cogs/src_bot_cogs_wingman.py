from discord.ext import commands
import discord

class Wingman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def queue2v2(self, ctx):
        """Entrar na fila 2v2"""
        # Implementar lógica
        pass

async def setup(bot):
    await bot.add_cog(Wingman(bot))