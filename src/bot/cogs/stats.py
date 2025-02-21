"""
Stats Command Manager
Author: adamguedesmtm
Created: 2025-02-21 13:47:53
"""

import discord
from discord.ext import commands
from typing import Optional

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, member: Optional[discord.Member] = None):
        """Ver estatísticas de um jogador"""
        try:
            # Se membro não especificado, usar o autor
            member = member or ctx.author
            
            # Gerar player card
            card_file = await self.bot.player_card.generate(
                member.id,
                member.name,
                member.avatar.url if member.avatar else None
            )

            if not card_file:
                raise Exception("Falha ao gerar player card")

            # Enviar card
            await ctx.send(
                f"📊 Estatísticas de {member.mention}",
                file=discord.File(card_file)
            )

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao mostrar stats: {e}")
            await ctx.send("❌ Erro ao mostrar estatísticas!")

    @commands.command()
    async def rank(self, ctx):
        """Ver ranking dos jogadores"""
        try:
            # Obter top 10 jogadores
            top_players = await self.bot.player_card.get_top_players(10)

            embed = discord.Embed(
                title="🏆 Top 10 Jogadores",
                color=discord.Color.gold()
            )

            for idx, player in enumerate(top_players, 1):
                # Emoji para posições
                position = {
                    1: "🥇",
                    2: "🥈",
                    3: "🥉"
                }.get(idx, f"{idx}.")

                embed.add_field(
                    name=f"{position} {player['name']}",
                    value=f"Rating: {player['rating']:.2f}\n"
                          f"K/D: {player['kd']:.2f}\n"
                          f"HS%: {player['hs_percent']}%",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao mostrar ranking: {e}")
            await ctx.send("❌ Erro ao mostrar ranking!")

    @commands.command()
    async def matches(self, ctx, member: Optional[discord.Member] = None):
        """Ver últimas partidas de um jogador"""
        try:
            member = member or ctx.author
            
            # Obter últimas 5 partidas
            matches = await self.bot.player_card.get_recent_matches(member.id, 5)

            embed = discord.Embed(
                title=f"📜 Últimas Partidas de {member.name}",
                color=discord.Color.blue()
            )

            for match in matches:
                result = "✅ Vitória" if match['won'] else "❌ Derrota"
                score = f"{match['team_score']} x {match['enemy_score']}"
                
                embed.add_field(
                    name=f"{match['map']} - {result}",
                    value=f"Score: {score}\n"
                          f"K/D/A: {match['kills']}/{match['deaths']}/{match['assists']}\n"
                          f"Rating: {match['rating']:.2f}",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao mostrar partidas: {e}")
            await ctx.send("❌ Erro ao mostrar partidas!")

async def setup(bot):
    await bot.add_cog(Stats(bot))