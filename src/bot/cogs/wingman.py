"""
Wingman Match Manager
Author: adamguedesmtm
Created: 2025-02-21 13:42:17
"""

import discord
from discord.ext import commands
from typing import Optional
import asyncio

class Wingman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ready_reactions = ['👍', '❌']

    @commands.command()
    async def queue2v2(self, ctx):
        """Entrar na fila 2v2"""
        try:
            # Verificar se jogador já está em alguma fila
            if self.bot.queue.is_in_queue(ctx.author.id):
                await ctx.send(f"❌ {ctx.author.mention} você já está em uma fila!")
                return

            # Adicionar jogador à fila
            position = await self.bot.queue.add_player(
                ctx.author.id, 
                'wingman',
                ctx.author.name
            )

            # Enviar mensagem de confirmação
            await ctx.send(
                f"✅ {ctx.author.mention} entrou na fila 2v2! (Posição: {position})"
            )

            # Verificar se há jogadores suficientes
            if await self.bot.queue.check_ready('wingman'):
                await self.start_match_vote(ctx)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao entrar na fila 2v2: {e}")
            await ctx.send("❌ Erro ao entrar na fila!")

    @commands.command()
    async def leave2v2(self, ctx):
        """Sair da fila 2v2"""
        try:
            # Remover jogador da fila
            if await self.bot.queue.remove_player(ctx.author.id, 'wingman'):
                await ctx.send(f"✅ {ctx.author.mention} saiu da fila!")
            else:
                await ctx.send(f"❌ {ctx.author.mention} você não está na fila!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao sair da fila: {e}")
            await ctx.send("❌ Erro ao sair da fila!")

    @commands.command()
    async def wingmanstatus(self, ctx):
        """Ver status da fila 2v2"""
        try:
            queue_info = await self.bot.queue.get_queue_info('wingman')
            
            embed = discord.Embed(
                title="📊 Status da Fila 2v2",
                color=discord.Color.blue()
            )
            
            # Adicionar informações da fila
            embed.add_field(
                name="Jogadores na Fila",
                value=f"{len(queue_info['players'])}/4",
                inline=False
            )
            
            # Listar jogadores
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
            self.bot.logger.logger.error(f"Erro ao mostrar status: {e}")
            await ctx.send("❌ Erro ao mostrar status da fila!")

    async def start_match_vote(self, ctx):
        """Iniciar votação para começar partida"""
        try:
            queue_info = await self.bot.queue.get_queue_info('wingman')
            players = queue_info['players'][:4]  # Pegar os 4 primeiros

            # Criar embed para votação
            embed = discord.Embed(
                title="🎮 Partida 2v2 Pronta!",
                description="Todos os jogadores devem reagir com 👍 para começar!\nReagir com ❌ cancela sua participação.",
                color=discord.Color.green()
            )

            # Listar jogadores
            players_list = "\n".join([
                f"{idx+1}. {player['name']}"
                for idx, player in enumerate(players)
            ])
            embed.add_field(
                name="Jogadores",
                value=players_list,
                inline=False
            )

            # Enviar mensagem e adicionar reações
            vote_msg = await ctx.send(embed=embed)
            for reaction in self.ready_reactions:
                await vote_msg.add_reaction(reaction)

            # Esperar reações dos jogadores
            try:
                ready_players = set()
                while len(ready_players) < 4:
                    reaction, user = await self.bot.wait_for(
                        'reaction_add',
                        timeout=60.0,
                        check=lambda r, u: (
                            str(r.emoji) in self.ready_reactions and
                            u.id in [p['id'] for p in players] and
                            not u.bot
                        )
                    )

                    if str(reaction.emoji) == '👍':
                        ready_players.add(user.id)
                        # Atualizar embed
                        embed.description = f"✅ {len(ready_players)}/4 jogadores prontos!"
                        await vote_msg.edit(embed=embed)
                    elif str(reaction.emoji) == '❌':
                        # Remover jogador
                        await self.bot.queue.remove_player(user.id, 'wingman')
                        await ctx.send(f"❌ {user.mention} saiu da partida!")
                        return

                # Todos prontos - iniciar partida
                await self.start_match(ctx, players)

            except asyncio.TimeoutError:
                await ctx.send("⏰ Tempo esgotado! Partida cancelada.")
                # Limpar fila
                for player in players:
                    await self.bot.queue.remove_player(player['id'], 'wingman')

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao iniciar votação: {e}")
            await ctx.send("❌ Erro ao iniciar votação!")

    async def start_match(self, ctx, players):
        """Iniciar partida 2v2"""
        try:
            # Criar partida no wingman manager
            match_id = await self.bot.wingman.create_match(players)
            
            if not match_id:
                raise Exception("Falha ao criar partida")

            # Enviar informações do servidor
            embed = discord.Embed(
                title="🎮 Partida 2v2 Iniciada!",
                description="Conecte-se ao servidor para jogar!",
                color=discord.Color.green()
            )

            server_info = await self.bot.wingman.get_match_info(match_id)
            
            # Informações do servidor
            embed.add_field(
                name="Servidor",
                value=f"`connect {server_info['ip']}:{server_info['port']}; password {server_info['password']}`",
                inline=False
            )

            # Informações dos times
            team1 = players[:2]
            team2 = players[2:]

            embed.add_field(
                name="Time 1",
                value="\n".join([p['name'] for p in team1]),
                inline=True
            )

            embed.add_field(
                name="Time 2",
                value="\n".join([p['name'] for p in team2]),
                inline=True
            )

            # Informações do mapa
            embed.add_field(
                name="Mapa",
                value=server_info['map'],
                inline=False
            )

            await ctx.send(embed=embed)

            # Remover jogadores da fila
            for player in players:
                await self.bot.queue.remove_player(player['id'], 'wingman')

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao iniciar partida: {e}")
            await ctx.send("❌ Erro ao iniciar partida!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def wingmanmaps(self, ctx):
        """Ver lista de mapas disponíveis para 2v2"""
        try:
            maps = await self.bot.wingman.get_available_maps()
            
            embed = discord.Embed(
                title="🗺️ Mapas Disponíveis - 2v2",
                color=discord.Color.blue()
            )
            
            maps_list = "\n".join([f"• {map_name}" for map_name in maps])
            embed.description = maps_list
            
            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao listar mapas: {e}")
            await ctx.send("❌ Erro ao listar mapas!")

async def setup(bot):
    await bot.add_cog(Wingman(bot))