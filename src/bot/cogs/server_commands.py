"""
Server Commands for CS2 Bot
Author: adamguedesmtm
Created: 2025-02-21 03:42:31
"""

import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime
from ..utils.logger import Logger

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('server_commands')

    @commands.command(name='players')
    async def list_players(self, ctx):
        """Listar jogadores no servidor"""
        try:
            players = await self._get_players()
            
            embed = discord.Embed(
                title="👥 Jogadores Online",
                description=f"Total: {len(players)}",
                color=0x00ff00
            )

            for player in players:
                embed.add_field(
                    name=player['name'],
                    value=f"Score: {player['score']}\n"
                          f"Time: {player['time']}\n"
                          f"Ping: {player['ping']}ms",
                    inline=True
                )

            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar jogadores: {e}")
            await ctx.send("❌ Erro ao obter lista de jogadores")

    @commands.command(name='map')
    async def change_map(self, ctx, map_name: str):
        """Mudar mapa do servidor"""
        valid_maps = ['de_mirage', 'de_dust2', 'de_inferno', 'de_nuke', 
                     'de_overpass', 'de_ancient', 'de_anubis']
        
        if map_name not in valid_maps:
            await ctx.send(f"❌ Mapa inválido! Mapas disponíveis: {', '.join(valid_maps)}")
            return

        try:
            await self._execute_rcon(f'map {map_name}')
            await ctx.send(f"✅ Mudando para {map_name}...")
            self.logger.logger.info(f"Mapa alterado para {map_name} por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao mudar mapa: {e}")
            await ctx.send("❌ Erro ao mudar mapa")

    @commands.command(name='rcon')
    @commands.has_role('Admin')
    async def rcon_command(self, ctx, *, command: str):
        """Executar comando RCON"""
        try:
            result = await self._execute_rcon(command)
            await ctx.send(f"```\n{result}\n```")
            self.logger.logger.info(f"Comando RCON executado por {ctx.author}: {command}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar RCON: {e}")
            await ctx.send("❌ Erro ao executar comando RCON")

    @commands.command(name='kick')
    @commands.has_role('Admin')
    async def kick_player(self, ctx, player: str, *, reason: str = "Sem motivo"):
        """Kickar jogador do servidor"""
        try:
            await self._execute_rcon(f'kick "{player}" "{reason}"')
            await ctx.send(f"✅ Jogador {player} kickado!\nMotivo: {reason}")
            self.logger.logger.info(f"Jogador {player} kickado por {ctx.author}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao kickar jogador: {e}")
            await ctx.send("❌ Erro ao kickar jogador")

    @commands.command(name='msg')
    @commands.has_role('Admin')
    async def server_message(self, ctx, *, message: str):
        """Enviar mensagem para o servidor"""
        try:
            await self._execute_rcon(f'say "{message}"')
            await ctx.send("✅ Mensagem enviada!")
            self.logger.logger.info(f"Mensagem enviada por {ctx.author}: {message}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao enviar mensagem: {e}")
            await ctx.send("❌ Erro ao enviar mensagem")

    async def _get_players(self):
        """Obter lista de jogadores"""
        try:
            response = await self._execute_rcon('status')
            players = []
            
            for line in response.splitlines():
                if 'STEAM_' in line:
                    parts = line.split()
                    players.append({
                        'name': parts[2],
                        'score': parts[3],
                        'time': parts[4],
                        'ping': parts[5],
                        'steam_id': parts[1]
                    })
                    
            return players
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter jogadores: {e}")
            return []

    async def _execute_rcon(self, command):
        """Executar comando RCON"""
        try:
            process = await asyncio.create_subprocess_shell(
                f'rcon -H {os.getenv("SERVER_IP")} -p {os.getenv("SERVER_PORT")} '
                f'-P {os.getenv("RCON_PASSWORD")} "{command}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stderr:
                raise Exception(stderr.decode())
                
            return stdout.decode()
            
        except Exception as e:
            self.logger.logger.error(f"Erro RCON: {e}")
            raise

def setup(bot):
    bot.add_cog(ServerCommands(bot))