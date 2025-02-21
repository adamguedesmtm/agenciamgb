"""
Stats Cog - Handles player statistics and roles
Author: adamguedesmtm
Created: 2025-02-21 14:18:04
"""

import discord
from discord.ext import commands, tasks
from typing import Optional
import io
from ..utils.stats_manager import StatsManager
from ..utils.role_system import RoleSystem
from ..utils.player_card import PlayerCard

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_manager = bot.stats_manager
        self.role_system = RoleSystem(self.stats_manager, bot.logger, bot.metrics)
        self.player_card = PlayerCard(logger=bot.logger, metrics=bot.metrics)
        
        # Iniciar task de atualização periódica
        self.update_roles.start()

    def cog_unload(self):
        self.update_roles.cancel()

    @tasks.loop(minutes=30)
    async def update_roles(self):
        """Atualizar roles periodicamente"""
        try:
            for guild in self.bot.guilds:
                await self.role_system.update_roles(guild)
        except Exception as e:
            self.bot.logger.error(f"Erro na atualização periódica de roles: {e}")

    @commands.command(name="stats")
    async def show_stats(self, ctx, member: Optional[discord.Member] = None):
        """Mostrar estatísticas de um jogador"""
        try:
            member = member or ctx.author
            stats = await self.stats_manager.get_player_stats(member.id)
            
            if not stats:
                await ctx.send("❌ Jogador não tem estatísticas registradas!")
                return

            # Gerar card
            card_buffer = await self.player_card.generate(
                member.id,
                member.name,
                member.avatar.url if member.avatar else None
            )

            if card_buffer:
                await ctx.send(
                    f"📊 Estatísticas de {member.mention}",
                    file=discord.File(card_buffer, "stats.png")
                )
            else:
                await ctx.send("❌ Erro ao gerar card de estatísticas!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar stats: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar estatísticas!")

    @commands.command(name="rank")
    async def show_rank(self, ctx, stat_type: str = "rating"):
        """Mostrar ranking dos jogadores"""
        try:
            rankings = await self.stats_manager.get_rankings(stat_type, limit=10)
            
            if not rankings:
                await ctx.send(f"❌ Nenhum ranking encontrado para {stat_type}!")
                return

            embed = discord.Embed(
                title=f"🏆 Top 10 - {stat_type.title()}",
                color=discord.Color.gold()
            )

            for i, rank in enumerate(rankings, 1):
                player = ctx.guild.get_member(rank['player_id'])
                if player:
                    embed.add_field(
                        name=f"#{i} {player.name}",
                        value=f"**{stat_type.title()}:** {rank['value']:.2f}\n"
                              f"**Jogos:** {rank.get('games', 0)}",
                        inline=False
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar ranking: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar ranking!")

    @commands.command(name="roles")
    async def show_roles(self, ctx, member: Optional[discord.Member] = None):
        """Mostrar roles de um jogador"""
        try:
            member = member or ctx.author
            roles = [r for r in member.roles if r.name in self.role_system.generic_roles 
                    or r.name in self.role_system.unique_roles]
            
            if not roles:
                await ctx.send(f"{member.mention} não tem roles especiais!")
                return

            embed = discord.Embed(
                title=f"🎭 Roles de {member.name}",
                color=member.color
            )

            # Agrupar roles por tipo
            unique_roles = [r for r in roles if r.name in self.role_system.unique_roles]
            generic_roles = [r for r in roles if r.name in self.role_system.generic_roles]

            if unique_roles:
                embed.add_field(
                    name="🏆 Roles Únicas",
                    value="\n".join(f"• {r.name}" for r in unique_roles),
                    inline=False
                )

            if generic_roles:
                embed.add_field(
                    name="📈 Roles de Progresso",
                    value="\n".join(f"• {r.name}" for r in generic_roles),
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar roles: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar roles!")

    @commands.command(name="leaderboard", aliases=["lb"])
    async def show_leaderboard(self, ctx):
        """Mostrar leaderboard geral"""
        try:
            stats = await self.stats_manager.get_leaderboard()
            
            embed = discord.Embed(
                title="🏆 Leaderboard",
                color=discord.Color.gold()
            )

            for category, top_players in stats.items():
                value = "\n".join(
                    f"**{i}.** {ctx.guild.get_member(p['id']).name}: {p['value']:.2f}"
                    for i, p in enumerate(top_players[:3], 1)
                    if ctx.guild.get_member(p['id'])
                )
                if value:
                    embed.add_field(
                        name=category.title(),
                        value=value,
                        inline=True
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar leaderboard: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar leaderboard!")

async def setup(bot):
    await bot.add_cog(Stats(bot))