"""
Matchzy Cog - CS2 Match Management System
Author: adamguedesmtm
Created: 2025-02-21 15:01:11
"""

import discord
from discord.ext import commands
from typing import Optional, Dict
from datetime import datetime
import asyncio
from ..utils.matchzy_manager import MatchzyManager
from ..utils.channel_manager import ChannelManager

class Matchzy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.matchzy = MatchzyManager(
            logger=bot.logger,
            metrics=bot.metrics,
            stats_manager=bot.stats_manager
        )
        self.channel_manager = ChannelManager(bot, bot.logger)
        self.match_setup_votes = {}

    @commands.command(name="retakes")
    async def setup_retakes(self, ctx):
        """Configurar servidor de retakes"""
        try:
            # Verificar se os canais estão configurados
            if not self.channel_manager.get_channel('commands'):
                await ctx.send("❌ Canais não configurados! Administrador deve usar !setchannels primeiro")
                return

            # Configurar servidor de retakes
            config = await self.matchzy.setup_match('practice')
            
            if config.get('error'):
                await ctx.send(f"❌ {config['message']}")
                return

            # Criar embed de confirmação
            embed = discord.Embed(
                title="🎮 Servidor de Retakes",
                description="Servidor configurado com sucesso!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="IP", value=config['ip'], inline=True)
            embed.add_field(name="Porta", value=config['port'], inline=True)
            embed.add_field(name="GOTV", value=config['gotv'], inline=True)
            embed.add_field(name="Connect", value=f"```{config['connect_cmd']}```", inline=False)
            
            voice_channel = self.channel_manager.get_channel('retake_voice')
            if voice_channel:
                embed.add_field(
                    name="Canal de Voz",
                    value=voice_channel.mention,
                    inline=False
                )

            embed.add_field(
                name="Comandos In-Game (CS2)",
                value="```\n!r - Entrar como T\n!ct - Entrar como CT"
                      "\n!spec - Entrar como Spectator\n!score - Ver placar```",
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao configurar retakes: {e}")
            await ctx.send("❌ Ocorreu um erro ao configurar o servidor de retakes!")

    @commands.command(name="pick")
    async def pick_match(self, ctx):
        """Iniciar processo de seleção de partida competitiva"""
        try:
            # Verificar se os canais estão configurados
            if not self.channel_manager.get_channel('commands'):
                await ctx.send("❌ Canais não configurados! Administrador deve usar !setchannels primeiro")
                return

            # Verificar se já existe uma votação ativa
            if ctx.author.id in self.match_setup_votes:
                await ctx.send("❌ Você já tem uma seleção de partida em andamento!")
                return

            # Verificar se o autor está em um canal de voz
            if not ctx.author.voice:
                await ctx.send("❌ Você precisa estar em um canal de voz para iniciar uma partida!")
                return

            # Verificar se é o canal correto
            current_channel = ctx.author.voice.channel
            valid_channels = [
                self.channel_manager.get_channel('competitive_voice'),
                self.channel_manager.get_channel('wingman_voice')
            ]

            if current_channel not in valid_channels:
                channels_mention = " ou ".join([c.mention for c in valid_channels if c])
                await ctx.send(f"❌ Você precisa estar em um dos canais dedicados: {channels_mention}")
                return

            # Determinar tipo de partida baseado no canal
            match_type = 'competitive' if current_channel == self.channel_manager.get_channel('competitive_voice') else 'wingman'

            # Verificar número de jogadores
            required = 10 if match_type == 'competitive' else 4
            current = len(current_channel.members)
            
            if current < required:
                await ctx.send(f"❌ Número insuficiente de jogadores! Necessário: {required}, Atual: {current}")
                return

            # Criar embed para votação
            embed = discord.Embed(
                title="🎮 Seleção de Partida",
                description=f"Reagir para escolher o formato:\n\n"
                           f"🎯 - Melhor de 1 (BO1)\n"
                           f"🏆 - Melhor de 3 (BO3)\n\n"
                           f"Tipo: {match_type.capitalize()}\n"
                           f"Jogadores: {current}/{required}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )

            embed.set_footer(text=f"Iniciado por {ctx.author.display_name}")

            # Enviar mensagem e adicionar reações
            message = await ctx.send(embed=embed)
            await message.add_reaction("🎯")  # BO1
            if match_type == 'competitive':  # BO3 apenas para competitivo
                await message.add_reaction("🏆")  # BO3

            # Guardar informações da votação
            self.match_setup_votes[ctx.author.id] = {
                'message_id': message.id,
                'match_type': match_type,
                'channel': current_channel,
                'timestamp': datetime.utcnow()
            }

            # Iniciar timeout da votação
            self.bot.loop.create_task(self._handle_vote_timeout(ctx.author.id, message))

        except Exception as e:
            self.bot.logger.error(f"Erro ao iniciar seleção: {e}")
            await ctx.send("❌ Ocorreu um erro ao iniciar a seleção!")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Manipular reações para seleção de formato"""
        try:
            # Ignorar reações do bot
            if user.bot:
                return

            # Procurar votação ativa com esta mensagem
            vote_info = None
            vote_author = None
            for author_id, info in self.match_setup_votes.items():
                if info['message_id'] == reaction.message.id:
                    vote_info = info
                    vote_author = author_id
                    break

            if not vote_info:
                return

            # Verificar se o usuário que reagiu é o mesmo que iniciou
            if user.id != vote_author:
                await reaction.remove(user)
                return

            # Processar seleção
            is_bo3 = False
            if str(reaction.emoji) == "🎯":  # BO1
                is_bo3 = False
            elif str(reaction.emoji) == "🏆" and vote_info['match_type'] == 'competitive':  # BO3
                is_bo3 = True
            else:
                return

            # Remover votação
            del self.match_setup_votes[vote_author]

            # Configurar partida
            await self._setup_match(reaction.message, vote_info['match_type'], is_bo3, vote_info['channel'])

        except Exception as e:
            self.bot.logger.error(f"Erro ao processar reação: {e}")

    async def _handle_vote_timeout(self, author_id: int, message: discord.Message):
        """Manipular timeout da votação"""
        await asyncio.sleep(60)  # 1 minuto para escolher
        if author_id in self.match_setup_votes:
            del self.match_setup_votes[author_id]
            try:
                embed = message.embeds[0]
                embed.description += "\n\n⏰ Tempo esgotado!"
                embed.color = discord.Color.red()
                await message.edit(embed=embed)
            except:
                pass

    async def _setup_match(self, message: discord.Message, match_type: str, is_bo3: bool, voice_channel: discord.VoiceChannel):
        """Configurar partida após seleção"""
        try:
            # Atualizar embed para mostrar seleção
            embed = message.embeds[0]
            embed.description += f"\n\n✅ Formato selecionado: {'BO3' if is_bo3 else 'BO1'}"
            embed.color = discord.Color.green()
            await message.edit(embed=embed)

            # Configurar partida
            config = await self.matchzy.setup_match(match_type, is_bo3)
            
            if config.get('error'):
                await message.channel.send(f"❌ {config['message']}")
                return

            # Criar canais para as equipes
            team_channels = {}
            if match_type != 'practice':
                team_channels, error = await self.channel_manager.create_team_channels(
                    message.guild, config['match_id'], match_type
                )
                if error:
                    await message.channel.send("⚠️ Aviso: Não foi possível criar canais de equipe")

            # Registrar callbacks para movimentação de jogadores
            await self.matchzy.register_callbacks(
                on_knife_round_start=self._handle_knife_round_start,
                on_warmup_end=self._handle_warmup_end if is_bo3 else None
            )

            # Criar embed de confirmação
            result_embed = discord.Embed(
                title="🎮 Partida Configurada",
                description=f"Tipo: {match_type.capitalize()}\nFormato: {'BO3' if is_bo3 else 'BO1'}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            result_embed.add_field(name="IP", value=config['ip'], inline=True)
            result_embed.add_field(name="Porta", value=config['port'], inline=True)
            result_embed.add_field(name="GOTV", value=config['gotv'], inline=True)
            result_embed.add_field(name="Connect", value=f"```{config['connect_cmd']}```", inline=False)

            if team_channels:
                result_embed.add_field(
                    name="Canais de Equipe",
                    value="\n".join(f"{name}: {channel.mention}" 
                                  for name, channel in team_channels.items()),
                    inline=False
                )

            result_embed.add_field(
                name="Canal de Voz",
                value=voice_channel.mention,
                inline=False
            )

            result_embed.add_field(
                name="Comandos In-Game (CS2)",
                value="```\n!ready - Marcar como pronto\n!unready - Desmarcar pronto"
                      "\n!pause - Pausar partida\n!unpause - Despausar partida"
                      "\n!tech - Pause técnico\n!score - Ver placar```",
                inline=False
            )

            await message.channel.send(embed=result_embed)

        except Exception as e:
            self.bot.logger.error(f"Erro ao configurar partida: {e}")
            await message.channel.send("❌ Ocorreu um erro ao configurar a partida!")

    async def _handle_knife_round_start(self, match_id: str):
        """Manipular início da round de faca"""
        try:
            if match_id not in self.channel_manager.temp_channels:
                return

            # Obter todos os jogadores nos times
            all_players = []
            for team_name, players in self.matchzy.teams.items():
                if team_name in ['CT', 'T']:
                    for player_id in players:
                        member = self.bot.get_guild(self.bot.guilds[0].id).get_member(player_id)
                        if member:
                            all_players.append(member)

            # Mover jogadores para o canal apropriado
            await self.channel_manager.move_players_to_voice(match_id, all_players)

            # Notificar nos canais
            team_channels = self.channel_manager.get_team_channels(match_id)
            for channel in team_channels.values():
                await channel.send("🔪 Round de faca iniciando! Todos os jogadores foram movidos para o canal de voz.")

        except Exception as e:
            self.bot.logger.error(f"Erro ao manipular início da knife round: {e}")

    async def _handle_warmup_end(self, match_id: str):
        """Manipular fim do warmup (BO3)"""
        try:
            # Esperar 5 segundos
            await asyncio.sleep(5)

            if match_id not in self.channel_manager.temp_channels:
                return

            # Obter todos os jogadores nos times
            all_players = []
            for team_name, players in self.matchzy.teams.items():
                if team_name in ['CT', 'T']:
                    for player_id in players:
                        member = self.bot.get_guild(self.bot.guilds[0].id).get_member(player_id)
                        if member:
                            all_players.append(member)

            # Mover jogadores para o canal apropriado
            await self.channel_manager.move_players_to_voice(match_id, all_players)

            # Notificar nos canais
            team_channels = self.channel_manager.get_team_channels(match_id)
            map_number = self.matchzy.bo3_state['current_map'] + 1
            for channel in team_channels.values():
                                await channel.send(f"🎮 Mapa {map_number} do BO3 iniciando! Todos os jogadores foram movidos para o canal de voz.")

        except Exception as e:
            self.bot.logger.error(f"Erro ao manipular fim do warmup: {e}")

    @commands.command(name="setchannels")
    @commands.has_permissions(administrator=True)
    async def set_channels(self, ctx, 
                          notifications: discord.TextChannel,
                          commands: discord.TextChannel,
                          competitive: discord.VoiceChannel,
                          wingman: discord.VoiceChannel,
                          retake: discord.VoiceChannel):
        """Configurar todos os canais do sistema"""
        try:
            channels = {
                'notifications': notifications.id,
                'commands': commands.id,
                'competitive_voice': competitive.id,
                'wingman_voice': wingman.id,
                'retake_voice': retake.id
            }

            success = await self.channel_manager.setup_channels(ctx.guild, channels)
            
            if success:
                # Atualizar monitor com canal de notificações
                self.matchzy.monitor.notification_channel_id = notifications.id
                self.matchzy.monitor.bot = self.bot

                embed = discord.Embed(
                    title="✅ Canais Configurados",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Canais de Texto",
                    value=f"Notificações: {notifications.mention}\n"
                          f"Comandos: {commands.mention}",
                    inline=False
                )
                
                embed.add_field(
                    name="Canais de Voz",
                    value=f"Competitivo 5v5: {competitive.mention}\n"
                          f"Wingman 2v2: {wingman.mention}\n"
                          f"Retake: {retake.mention}",
                    inline=False
                )

                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Erro ao configurar canais!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao configurar canais: {e}")
            await ctx.send("❌ Erro ao configurar canais!")

    @commands.command(name="score")
    @commands.has_permissions(administrator=True)
    async def update_score(self, ctx, ct_score: int, t_score: int):
        """Atualizar placar nos canais"""
        try:
            # Atualizar placar em todos os canais ativos
            for match_id in self.channel_manager.temp_channels:
                await self.channel_manager.update_score(match_id, ct_score, t_score)
            await ctx.send(f"✅ Placar atualizado: CT {ct_score} - {t_score} T")
        except Exception as e:
            self.bot.logger.error(f"Erro ao atualizar placar: {e}")
            await ctx.send("❌ Erro ao atualizar placar!")

    @commands.command(name="endmatch")
    @commands.has_permissions(administrator=True)
    async def end_match(self, ctx):
        """Finalizar partida e limpar canais"""
        try:
            success = await self.matchzy.end_match()
            if success:
                # Encontrar e deletar canais da partida
                for match_id in list(self.channel_manager.temp_channels.keys()):
                    await self.channel_manager.delete_team_channels(match_id)
                await ctx.send("✅ Partida finalizada e canais limpos!")
            else:
                await ctx.send("❌ Erro ao finalizar partida!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao finalizar match: {e}")
            await ctx.send("❌ Ocorreu um erro ao finalizar a partida!")

    @setup_retakes.error
    @pick_match.error
    @set_channels.error
    @update_score.error
    @end_match.error
    async def command_error(self, ctx, error):
        """Handler para erros em comandos"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")
        else:
            self.bot.logger.error(f"Erro em comando: {error}")
            await ctx.send("❌ Ocorreu um erro ao executar o comando!")

async def setup(bot):
    await bot.add_cog(Matchzy(bot))