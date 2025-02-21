"""
Match Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:42:31
"""

import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime
from ..utils.logger import Logger

class MatchManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('match_manager')
        self.matches = {}
        self.match_config = self._load_match_config()

    def _load_match_config(self):
        """Carregar configuração de partidas"""
        try:
            with open('/opt/cs2server/config/match_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar config de partidas: {e}")
            return {
                'maps': ['de_mirage', 'de_dust2', 'de_inferno'],
                'max_rounds': 30,
                'warmup_time': 60,
                'knife_round': True
            }

    @commands.command(name='creatematch')
    @commands.has_role('Admin')
    async def create_match(self, ctx, team1: str, team2: str):
        """Criar uma nova partida"""
        try:
            match_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            match_data = {
                'id': match_id,
                'team1': team1,
                'team2': team2,
                'status': 'setup',
                'score': {'team1': 0, 'team2': 0},
                'players': {'team1': [], 'team2': []},
                'maps': [],
                'current_map': None,
                'created_by': ctx.author.id,
                'created_at': datetime.utcnow().isoformat()
            }

            self.matches[match_id] = match_data
            
            embed = self._create_match_embed(match_data)
            await ctx.send(embed=embed)
            
            self.logger.logger.info(
                f"Partida {match_id} criada por {ctx.author}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar partida: {e}")
            await ctx.send("❌ Erro ao criar partida")

    @commands.command(name='addplayer')
    @commands.has_role('Admin')
    async def add_player(self, ctx, match_id: str, team: str, steam_id: str):
        """Adicionar jogador a uma equipe"""
        try:
            if match_id not in self.matches:
                await ctx.send("❌ Partida não encontrada!")
                return

            if team not in ['team1', 'team2']:
                await ctx.send("❌ Equipe inválida! Use 'team1' ou 'team2'")
                return

            match = self.matches[match_id]
            match['players'][team].append(steam_id)
            
            await ctx.send(f"✅ Jogador adicionado à {team}!")
            self.logger.logger.info(
                f"Jogador {steam_id} adicionado à {team} na partida {match_id}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar jogador: {e}")
            await ctx.send("❌ Erro ao adicionar jogador")

    @commands.command(name='startmatch')
    @commands.has_role('Admin')
    async def start_match(self, ctx, match_id: str):
        """Iniciar uma partida"""
        try:
            if match_id not in self.matches:
                await ctx.send("❌ Partida não encontrada!")
                return

            match = self.matches[match_id]
            
            # Verificar times completos
            if len(match['players']['team1']) != 5 or len(match['players']['team2']) != 5:
                await ctx.send("❌ Ambos os times precisam ter 5 jogadores!")
                return

            # Configurar servidor
            await self._configure_match_server(match)
            
            # Atualizar status
            match['status'] = 'live'
            match['started_at'] = datetime.utcnow().isoformat()
            
            embed = self._create_match_embed(match)
            await ctx.send(embed=embed)
            
            self.logger.logger.info(f"Partida {match_id} iniciada por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar partida: {e}")
            await ctx.send("❌ Erro ao iniciar partida")

    def _create_match_embed(self, match):
        """Criar embed com informações da partida"""
        embed = discord.Embed(
            title=f"🏆 Partida {match['id']}",
            description=f"Status: {match['status']}",
            color=0x00ff00
        )

        embed.add_field(
            name=match['team1'],
            value=f"Score: {match['score']['team1']}\n"
                  f"Players: {len(match['players']['team1'])}/5",
            inline=True
        )

        embed.add_field(
            name=match['team2'],
            value=f"Score: {match['score']['team2']}\n"
                  f"Players: {len(match['players']['team2'])}/5",
            inline=True
        )

        if match['current_map']:
            embed.add_field(
                name="Mapa Atual",
                value=match['current_map'],
                inline=False
            )

        return embed

    async def _configure_match_server(self, match):
        """Configurar servidor para a partida"""
        try:
            # Configurar RCON
            commands = [
                f'mp_teamname_1 "{match["team1"]}"',
                f'mp_teamname_2 "{match["team2"]}"',
                f'mp_maxrounds "{self.match_config["max_rounds"]}"',
                f'mp_warmuptime "{self.match_config["warmup_time"]}"',
                'mp_warmup_start',
                'mp_restartgame 1'
            ]

            for cmd in commands:
                await self._execute_rcon(cmd)
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao configurar servidor: {e}")
            raise

    async def _execute_rcon(self, command):
        """Executar comando RCON"""
        # Implementar lógica real de RCON
        pass

def setup(bot):
    bot.add_cog(MatchManager(bot))