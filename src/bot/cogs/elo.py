"""
ELO Commands
Author: adamguedesmtm
Created: 2025-02-21 15:42:55
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

class EloCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def create_rank_embed(self, player_data: dict) -> discord.Embed:
        """Cria embed com informações do rank"""
        rank_info = self.bot.elo.get_rank_info(player_data["rating"])
        
        embed = discord.Embed(
            title=f"{rank_info['icon']} Rank de {player_data['name']}",
            color=discord.Color.blue()
        )
        
        # Stats gerais
        games = player_data.get("games_played", 0)
        wins = player_data.get("wins", 0)
        losses = games - wins
        win_rate = (wins / games * 100) if games > 0 else 0
        
        embed.add_field(
            name="Rank",
            value=f"{rank_info['name']} ({rank_info['rating']} pontos)",
            inline=False
        )
        
        # Barra de progresso
        progress = "▰" * (rank_info["progress"] // 10) + "▱" * (10 - rank_info["progress"] // 10)
        embed.add_field(
            name="Progresso",
            value=f"{progress} ({rank_info['progress']}%)",
            inline=False
        )
        
        if rank_info["next_rank"]:
            embed.add_field(
                name="Próximo Rank",
                value=f"{rank_info['next_rank']} ({rank_info['points_to_next']} pontos)",
                inline=False
            )
        
        # Estatísticas
        embed.add_field(
            name="Partidas",
            value=f"Total: {games}\nVitórias: {wins}\nDerrotas: {losses}\nWin Rate: {win_rate:.1f}%",
            inline=True
        )
        
        # Performance
        kd = player_data.get("kills", 0) / max(player_data.get("deaths", 1), 1)
        embed.add_field(
            name="Performance",
            value=f"K/D: {kd:.2f}\nHS%: {player_data.get('hs_percent', 0):.1f}%\nADR: {player_data.get('adr', 0):.1f}",
            inline=True
        )
        
        # Impacto
        embed.add_field(
            name="Impacto",
            value=f"Entry Kills: {player_data.get('entry_kills', 0)}\nClutches: {player_data.get('clutches', 0)}",
            inline=True
        )
        
        return embed
    
    @app_commands.command(name="rank")
    async def rank(self, interaction: discord.Interaction, steam_id: Optional[str] = None):
        """Mostra seu rank ou de outro jogador"""
        await interaction.response.defer()
        
        try:
            # Buscar dados do jogador
            if steam_id:
                player_data = self.bot.metrics.get_player_stats(steam_id)
            else:
                discord_id = str(interaction.user.id)
                steam_id = self.bot.metrics.get_steam_id(discord_id)
                if not steam_id:
                    await interaction.followup.send("❌ Vincule sua conta Steam primeiro usando `/link`")
                    return
                player_data = self.bot.metrics.get_player_stats(steam_id)
            
            if not player_data:
                await interaction.followup.send("❌ Jogador não encontrado")
                return
            
            embed = self.create_rank_embed(player_data)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao buscar rank: {str(e)}")
            await interaction.followup.send("❌ Erro ao buscar rank")
    
    @app_commands.command(name="top")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Mostra o ranking dos melhores jogadores"""
        await interaction.response.defer()
        
        try:
            # Buscar top players
            top_players = self.bot.metrics.get_top_players(page)
            
            if not top_players:
                await interaction.followup.send("❌ Nenhum jogador encontrado")
                return
            
            embed = discord.Embed(
                title="🏆 Top Players",
                color=discord.Color.gold()
            )
            
            for i, player in enumerate(top_players, (page - 1) * 10 + 1):
                rank_info = self.bot.elo.get_rank_info(player["rating"])
                win_rate = (player.get("wins", 0) / player.get("games_played", 1)) * 100
                
                embed.add_field(
                    name=f"#{i} {player['name']}",
                    value=f"{rank_info['icon']} {rank_info['name']}\n"
                          f"Rating: {player['rating']:.0f} pontos\n"
                          f"Win Rate: {win_rate:.1f}%\n"
                          f"Partidas: {player.get('games_played', 0)}",
                    inline=False
                )
            
            embed.set_footer(text=f"Página {page}")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao buscar leaderboard: {str(e)}")
            await interaction.followup.send("❌ Erro ao buscar leaderboard")
    
    @app_commands.command(name="link")
    async def link_steam(self, interaction: discord.Interaction, steam_id: str):
        """Vincula sua conta Steam ao Discord"""
        await interaction.response.defer()
        
        try:
            # Verificar se já existe vínculo
            existing_steam = self.bot.metrics.get_discord_id(steam_id)
            existing_discord = self.bot.metrics.get_steam_id(str(interaction.user.id))
            
            if existing_steam or existing_discord:
                await interaction.followup.send("❌ Esta conta Steam ou Discord já está vinculada")
                return
            
            # Vincular contas
            self.bot.metrics.link_accounts(
                steam_id=steam_id,
                discord_id=str(interaction.user.id),
                discord_name=interaction.user.name
            )
            
            embed = discord.Embed(
                title="✅ Conta vinculada com sucesso!",
                description=f"Sua conta Discord foi vinculada ao Steam ID: {steam_id}",
                color=discord.Color.green()
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao vincular conta: {str(e)}")
            await interaction.followup.send("❌ Erro ao vincular conta")

async def setup(bot):
    await bot.add_cog(EloCog(bot))