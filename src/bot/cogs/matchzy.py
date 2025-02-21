"""
Matchzy Cog - Handles CS2 match configuration and management
Author: adamguedesmtm
Created: 2025-02-21 14:35:45
"""

import discord
from discord.ext import commands
from typing import Optional
from ..utils.matchzy_manager import MatchzyManager
from ..utils.stats_manager import StatsManager

class Matchzy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.matchzy = MatchzyManager(
            logger=bot.logger,
            metrics=bot.metrics,
            stats_manager=bot.stats_manager
        )

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_match(self, ctx, match_type: str):
        """Configurar nova partida"""
        try:
            if match_type not in ['competitive', 'wingman', 'practice']:
                await ctx.send("❌ Tipo de partida inválido! Use: competitive, wingman ou practice")
                return

            config = await self.matchzy.setup_match(match_type)
            
            if config.get('error'):
                await ctx.send(f"❌ {config['message']}")
                return
            
            embed = discord.Embed(
                title="🎮 Match Setup",
                description="Configuração da partida:",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Tipo", value=match_type, inline=True)
            embed.add_field(name="IP", value=config['ip'], inline=True)
            embed.add_field(name="Porta", value=config['port'], inline=True)
            embed.add_field(name="GOTV", value=config['gotv'], inline=True)
            embed.add_field(name="Connect", value=f"```{config['connect_cmd']}```", inline=False)
            embed.add_field(
                name="Comandos In-Game (CS2)",
                value="```\n!ready - Marcar como pronto\n!unready - Desmarcar pronto\n!pause - Pausar partida\n!unpause - Despausar partida\n!tech - Pause técnico\n!score - Ver placar```",
                inline=False
            )
            
            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao configurar match: {e}")
            await ctx.send("❌ Ocorreu um erro ao configurar a partida!")

    @commands.command(name="status")
    async def server_status(self, ctx):
        """Ver status do servidor"""
        try:
            status = await self.matchzy.get_server_status()
            
            if status.get('error'):
                await ctx.send(f"❌ {status['message']}")
                return
                
            if not status['active']:
                await ctx.send("📊 Nenhum servidor ativo no momento!")
                return

            embed = discord.Embed(
                title="📊 Status do Servidor",
                color=discord.Color.blue()
            )
            
            # Info do servidor
            server_info = status['server_info']
            embed.add_field(
                name="Servidor",
                value=f"IP: {server_info['ip']}\nPorta: {server_info['port']}\nTipo: {server_info['match_type']}",
                inline=False
            )
            
            # Estado da partida
            match_state = status['match_state']
            state_str = "🔄 Warmup" if match_state['warmup'] else "▶️ Em andamento" if match_state['active'] else "⏸️ Aguardando"
            if match_state['paused']:
                state_str = "⏸️ Pausado"
                
            embed.add_field(name="Estado", value=state_str, inline=True)
            embed.add_field(name="Mapa", value=match_state['map'] or "Não definido", inline=True)
            embed.add_field(name="Uptime", value=match_state['uptime'], inline=True)
            
            if match_state['active']:
                embed.add_field(
                    name="Score",
                    value=f"CT {match_state['score_ct']} - {match_state['score_t']} T\nRound: {match_state['round']}",
                    inline=False
                )
            
            # Times
            teams = status['teams']
            embed.add_field(
                name="Jogadores",
                value=f"CT: {teams['CT']}\nT: {teams['T']}\nSpec: {teams['SPEC']}",
                inline=False
            )
            
            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao mostrar status: {e}")
            await ctx.send("❌ Ocorreu um erro ao verificar status!")

    @commands.command(name="forceend")
    @commands.has_permissions(administrator=True)
    async def force_end(self, ctx):
        """Forçar encerramento do servidor"""
        try:
            success = await self.matchzy.force_end_server()
            if success:
                await ctx.send("✅ Servidor encerrado!")
            else:
                await ctx.send("❌ Nenhum servidor ativo para encerrar!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao encerrar servidor: {e}")
            await ctx.send("❌ Ocorreu um erro ao encerrar o servidor!")

    @commands.command(name="map")
    @commands.has_permissions(administrator=True)
    async def change_map(self, ctx, map_name: str):
        """Mudar mapa do servidor"""
        try:
            success = await self.matchzy.change_map(map_name)
            if success:
                await ctx.send(f"🗺️ Mapa alterado para {map_name}!")
            else:
                await ctx.send("❌ Mapa inválido ou erro ao mudar!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao mudar mapa: {e}")
            await ctx.send("❌ Ocorreu um erro ao mudar o mapa!")

    @setup_match.error
    @force_end.error
    @change_map.error
    async def admin_command_error(self, ctx, error):
        """Handler para erros em comandos administrativos"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")
        else:
            self.bot.logger.error(f"Erro em comando admin: {error}")
            await ctx.send("❌ Ocorreu um erro ao executar o comando!")

async def setup(bot):
    await bot.add_cog(Matchzy(bot))