"""
Channel Manager - Discord Channel Management System
Author: adamguedesmtm
Created: 2025-02-21 14:59:00
"""

import discord
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from .logger import Logger

class ChannelManager:
    def __init__(self, bot, logger: Optional[Logger] = None):
        self.bot = bot
        self.logger = logger or Logger('channel_manager')
        
        # Canais principais
        self.channels = {
            'notifications': None,     # Canal para notificações do servidor
            'commands': None,          # Canal para comandos do bot
            'competitive_voice': None, # Canal de voz 5v5
            'wingman_voice': None,     # Canal de voz 2v2
            'retake_voice': None      # Canal de voz retakes
        }
        
        # Canais temporários ativos (apenas para competitivo e wingman)
        self.temp_channels: Dict[str, Dict] = {}

    async def setup_channels(self, guild: discord.Guild, channel_ids: Dict[str, int]) -> bool:
        """Configurar canais principais"""
        try:
            for channel_type, channel_id in channel_ids.items():
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        self.channels[channel_type] = channel
                    else:
                        self.logger.error(f"Canal não encontrado: {channel_type} - {channel_id}")
                        return False
            return True
        except Exception as e:
            self.logger.error(f"Erro ao configurar canais: {e}")
            return False

    async def create_team_channels(self, guild: discord.Guild, match_id: str, match_type: str) -> Tuple[Dict[str, discord.TextChannel], Exception]:
        """Criar canais temporários para as equipes"""
        try:
            # Verificar se é um modo válido para canais temporários
            if match_type not in ['competitive', 'wingman']:
                return {}, None

            # Criar categoria para os canais
            category_name = f"Match-{match_id} [0-0]"
            category = await guild.create_category(category_name)
            
            # Criar canais para cada equipe
            team_channels = {}
            team_names = ["Team-CT [0]", "Team-T [0]"]
            
            for team_name in team_names:
                # Canal de texto da equipe
                text_channel = await category.create_text_channel(
                    team_name.lower().replace(' ', '-'),
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True)
                    }
                )
                team_channels[team_name] = text_channel

            # Guardar referência dos canais temporários
            self.temp_channels[match_id] = {
                'category': category,
                'channels': team_channels,
                'match_type': match_type
            }
            
            return team_channels, None

        except Exception as e:
            self.logger.error(f"Erro ao criar canais de equipe: {e}")
            return {}, e

    async def update_score(self, match_id: str, ct_score: int, t_score: int) -> bool:
        """Atualizar placar nos nomes dos canais"""
        try:
            if match_id not in self.temp_channels:
                return False

            match_data = self.temp_channels[match_id]
            category = match_data['category']
            channels = match_data['channels']

            # Atualizar nome da categoria
            await category.edit(name=f"Match-{match_id} [{ct_score}-{t_score}]")

            # Atualizar nomes dos canais
            for channel_name, channel in channels.items():
                if "CT" in channel_name:
                    await channel.edit(name=f"team-ct-[{ct_score}]")
                elif "T" in channel_name:
                    await channel.edit(name=f"team-t-[{t_score}]")

            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar placar: {e}")
            return False

    async def delete_team_channels(self, match_id: str) -> bool:
        """Deletar canais temporários de uma partida"""
        try:
            if match_id not in self.temp_channels:
                return False

            match_data = self.temp_channels[match_id]
            
            # Deletar canais
            for channel in match_data['channels'].values():
                await channel.delete()

            # Deletar categoria
            await match_data['category'].delete()

            del self.temp_channels[match_id]
            return True

        except Exception as e:
            self.logger.error(f"Erro ao deletar canais de equipe: {e}")
            return False

    async def update_team_permissions(self, match_id: str, team_name: str, members: List[discord.Member]) -> bool:
        """Atualizar permissões dos membros no canal da equipe"""
        try:
            if match_id not in self.temp_channels:
                return False

            channels = self.temp_channels[match_id]['channels']
            channel = None
            
            # Encontrar canal correto
            for chan_name, chan in channels.items():
                if team_name.upper() in chan_name.upper():
                    channel = chan
                    break

            if not channel:
                return False

            # Atualizar permissões
            for member in members:
                await channel.set_permissions(member, read_messages=True, send_messages=True)

            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar permissões: {e}")
            return False

    def get_channel(self, channel_type: str) -> Optional[discord.TextChannel]:
        """Obter canal pelo tipo"""
        return self.channels.get(channel_type)

    def get_team_channels(self, match_id: str) -> Dict[str, discord.TextChannel]:
        """Obter canais de uma partida específica"""
        return self.temp_channels.get(match_id, {}).get('channels', {})

    def get_voice_channel(self, match_type: str) -> Optional[discord.VoiceChannel]:
        """Obter canal de voz para um tipo específico de partida"""
        if match_type == 'competitive':
            return self.channels.get('competitive_voice')
        elif match_type == 'wingman':
                        return self.channels.get('wingman_voice')
        elif match_type == 'practice':
            return self.channels.get('retake_voice')
        return None

    async def move_players_to_voice(self, match_id: str, members: List[discord.Member]) -> bool:
        """Mover jogadores para o canal de voz apropriado"""
        try:
            if match_id not in self.temp_channels:
                return False

            match_type = self.temp_channels[match_id]['match_type']
            voice_channel = self.get_voice_channel(match_type)

            if not voice_channel:
                return False

            # Mover cada jogador
            for member in members:
                if member.voice:
                    try:
                        await member.move_to(voice_channel)
                    except Exception as e:
                        self.logger.error(f"Erro ao mover jogador {member.name}: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Erro ao mover jogadores: {e}")
            return False