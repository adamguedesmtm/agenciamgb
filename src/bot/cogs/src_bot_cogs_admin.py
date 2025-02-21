from discord.ext import commands
import discord

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearqueue(self, ctx, queue_type):
        """Limpar fila específica"""
        # Implementar lógica
        pass

async def setup(bot):
    await bot.add_cog(Admin(bot))