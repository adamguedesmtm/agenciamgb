"""
Demo Cog - Handles CS:GO demo processing and analysis
Author: adamguedesmtm
Created: 2025-02-21 14:18:04
"""

import discord
from discord.ext import commands, tasks
from typing import Optional
from ..utils.demo_manager import DemoManager

class Demo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.demo_manager = DemoManager(
            logger=bot.logger,
            metrics=bot.metrics,
            stats_manager=bot.stats_manager
        )
        
        # Iniciar processador de demos
        self.start_processor.start()

    def cog_unload(self):
        self.start_processor.cancel()

    @tasks.loop(seconds=1)
    async def start_processor(self):
        """Iniciar processador de demos"""
        await self.demo_manager.start_processor()

    @commands.command(name="demo")
    @commands.has_permissions(administrator=True)
    async def process_demo(self, ctx, match_id: str):
        """Processar demo manualmente"""
        try:
            success = await self.demo_manager.queue_demo(
                match_id,
                f"/opt/cs2server/demos/{match_id}.dem"
            )
            
            if success:
                await ctx.send(f"✅ Demo {match_id} adicionada à fila de processamento!")
            else:
                await ctx.send("❌ Erro ao adicionar demo à fila!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao processar demo: {e}")
            await ctx.send("❌ Ocorreu um erro ao processar demo!")

    @commands.command(name="demostatus")
    async def demo_status(self, ctx):
        """Ver status do processamento de demos"""
        try:
            queue_size = self.demo_manager.processing_queue.qsize()
            is_processing = self.demo_manager.is_processing

            embed = discord.Embed(
                title="📊 Status do Processador de Demos",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Status",
                value="🟢 Ativo" if is_processing else "🔴 Inativo",
                inline=True
            )
            
            embed.add_field(
                name="Demos na Fila",
                value=str(queue_size),
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar status de demos: {e}")
            await ctx.send("❌ Ocorreu um erro ao verificar status!")

async def setup(bot):
    await bot.add_cog(Demo(bot))