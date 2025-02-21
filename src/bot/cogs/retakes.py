"""
Retakes Match Manager
Author: adamguedesmtm
Created: 2025-02-21 13:45:00
"""

import discord
from discord.ext import commands
import asyncio

class Retakes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.min_players = 6  # Mínimo de jogadores para retake

    @commands.command()
    async def queueretake(self, ctx):
        """Entrar na fila retake"""
        try:
            # Verificar se jogador já está em fila
            if self.bot.queue.is_in_queue(ctx.author.id):
                await ctx.send(f"❌ {ctx.author.mention} você já está em uma fila!")
                return

            # Adicionar à fila
            position = await self.bot.queue.add_player(
                ctx.author.id,
                'retake',
                ctx.author.name
            )

            await ctx.send(
                f"✅ {ctx.author.mention} entrou na fila retake! (Posição: {position})"
            )

            # Verificar se podemos iniciar
            if await self.bot.queue.check_ready('retake'):
                await self.start_retake(ctx)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao entrar na fila retake: {e}")
            await ctx.send("❌ Erro ao entrar na fila!")

    @commands.command()
    async def leaveretake(self, ctx):
        """Sair da fila retake"""
        try:
            if await self.bot.queue.remove_player(ctx.author.id, 'retake'):
                await ctx.send(f"✅ {ctx.author.mention} saiu da fila retake!")
            else:
                await ctx.send(f"❌ {ctx.author.mention} você não está na fila!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao sair da fila retake: {e}")
            await ctx.send("❌ Erro ao sair da fila!")

    @commands.command()
    async def retakestatus(self, ctx):
        """Ver status da fila retake"""
        try:
            queue_info = await self.bot.queue.get_queue_info('retake')
            
            embed = discord.Embed(
                title="📊 Status Retake",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Jogadores na Fila",
                value=f"{len(queue_info['players'])}/{self.min_players}+",
                inline=False
            )
            
            if queue_info['players']:
                players_list = "\n".join([
                    f"{idx+1}. {player['name']}"
                    for idx, player in enumerate(queue_info['players'])
                ])
                embed.add_field(
                    name="Lista de Jogadores",
                    value=players_list,
                    inline=False
                )
            else:
                embed.add_field(
                    name="Lista de Jogadores",
                    value="Nenhum jogador na fila",
                    inline=False
                )
            
            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao mostrar status retake: {e}")
            await ctx.send("❌ Erro ao mostrar status!")

    async def start_retake(self, ctx):
        """Iniciar servidor retake"""
        try:
            queue_info = await self.bot.queue.get_queue_info('retake')
            players = queue_info['players']

            # Configurar servidor retake
            server_info = await self.bot.retake.setup_server(len(players))
            
            if not server_info:
                raise Exception("Falha ao configurar servidor")

            # Enviar informações aos jogadores
            embed = discord.Embed(
                title="🎮 Servidor Retake Pronto!",
                description="Conecte-se ao servidor para jogar!",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Servidor",
                value=f"`connect {server_info['ip']}:{server_info['port']}; password {server_info['password']}`",
                inline=False
            )

            embed.add_field(
                name="Jogadores",
                value="\n".join([p['name'] for p in players]),
                inline=False
            )

            await ctx.send(embed=embed)

            # Remover jogadores da fila
            for player in players:
                await self.bot.queue.remove_player(player['id'], 'retake')

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao iniciar retake: {e}")
            await ctx.send("❌ Erro ao iniciar servidor retake!")

async def setup(bot):
    await bot.add_cog(Retakes(bot))