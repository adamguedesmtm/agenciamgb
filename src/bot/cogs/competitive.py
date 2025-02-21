"""
Competitive Match Manager
Author: adamguedesmtm
Created: 2025-02-21 13:42:17
"""

import discord
from discord.ext import commands
from typing import Optional
import asyncio

class Competitive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ready_reactions = ['👍', '❌']

    @commands.command()
    async def queue5v5(self, ctx):
        """Entrar na fila 5v5"""
        try:
            # Verificar se jogador já está em alguma fila
            if self.bot.queue.is_in_queue(ctx.author.id):
                await ctx.send(f"❌ {ctx.author.mention} você já está em uma fila!")
                return

            # Adicionar jogador à fila
            position = await self.bot.queue.add_player(
                ctx.author.id, 
                'competitive',
                ctx.author.name
            )

            # Enviar mensagem de confirmação
            await ctx.send(
                f"✅ {ctx.author.mention} entrou na fila 5v5! (Posição: {position})"
            )

            # Verificar se há jogadores suficientes
            if await self.bot.queue.check_ready('competitive'):
                await self.start_match_vote(ctx)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao entrar na fila 5v5: {e}")
            await ctx.send("❌ Erro ao entrar na fila!")

    @commands.command()
    async def leave(self, ctx):
        """Sair da fila"""
        try:
            # Remover jogador da fila
            if await self.bot.queue.remove_player(ctx.author.id, 'competitive'):
                await ctx.send(f"✅ {ctx.author.mention} saiu da fila!")
            else:
                await ctx.send(f"❌ {ctx.author.mention} você não está em nenhuma fila!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao sair da fila: {e}")
            await ctx.send("❌ Erro ao sair da fila!")

    @commands.command()
    async def status(self, ctx):
        """Ver status das filas"""
        try:
            queue_info = await self.bot.queue.get_queue_info('competitive')
            
            embed = discord.Embed(
                title="📊 Status da Fila 5v5",
                color=discord.Color.blue()
            )
            
            # Adicionar informações da fila
            embed.add_field(
                name="Jogadores na Fila",
                value=f"{len(queue_info['players'])}/10",
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
            queue_info = await self.bot.queue.get_queue_info('competitive')
            players = queue_info['players'][:10]  # Pegar os 10 primeiros

            # Criar embed para votação
            embed = discord.Embed(
                title="🎮 Partida 5v5 Pronta!",
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
                while len(ready_players) < 10:
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
                        embed.description = f"✅ {len(ready_players)}/10 jogadores prontos!"
                        await vote_msg.edit(embed=embed)
                    elif str(reaction.emoji) == '❌':
                        # Remover jogador
                        await self.bot.queue.remove_player(user.id, 'competitive')
                        await ctx.send(f"❌ {user.mention} saiu da partida!")
                        return

                # Todos prontos - iniciar partida
                await self.start_match(ctx, players)

            except asyncio.TimeoutError:
                await ctx.send("⏰ Tempo esgotado! Partida cancelada.")
                # Limpar fila
                for player in players:
                    await self.bot.queue.remove_player(player['id'], 'competitive')

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao iniciar votação: {e}")
            await ctx.send("❌ Erro ao iniciar votação!")

    async def start_match(self, ctx, players):
        """Iniciar partida"""
        try:
            # Criar partida no matchzy
            match_id = await self.bot.matchzy.create_match(players)
            
            if not match_id:
                raise Exception("Falha ao criar partida")

            # Enviar informações do servidor
            embed = discord.Embed(
                title="🎮 Partida 5v5 Iniciada!",
                description="Conecte-se ao servidor para jogar!",
                color=discord.Color.green()
            )

            server_info = await self.bot.matchzy.get_match_info(match_id)
            
            embed.add_field(
                name="Servidor",
                value=f"`connect {server_info['ip']}:{server_info['port']}; password {server_info['password']}`",
                inline=False
            )

            await ctx.send(embed=embed)

            # Remover jogadores da fila
            for player in players:
                await self.bot.queue.remove_player(player['id'], 'competitive')

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao iniciar partida: {e}")
            await ctx.send("❌ Erro ao iniciar partida!")

async def setup(bot):
    await bot.add_cog(Competitive(bot))