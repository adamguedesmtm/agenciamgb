"""
CS2 Event Manager
Author: adamguedesmtm
Created: 2025-02-21 04:08:49
"""

import discord
from discord.ext import commands
import asyncio
import re
from datetime import datetime
from ..utils.logger import Logger

class CS2EventManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('cs2_event_manager')
        self.event_patterns = {
            'kill': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: "(.+)<\d+><STEAM_\d:\d:\d+>" \[(.+)\] killed "(.+)<\d+><STEAM_\d:\d:\d+>" \[(.+)\]',
            'round_start': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: World triggered "Round_Start"',
            'round_end': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: Team "(CT|TERRORIST)" triggered "Round_Win"',
            'match_start': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: World triggered "Match_Start"',
            'match_end': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: Game Over:',
            'player_connect': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: "(.+)<\d+><STEAM_\d:\d:\d+>" connected',
            'player_disconnect': r'^L \d+/\d+/\d+ - \d+:\d+:\d+: "(.+)<\d+><STEAM_\d:\d:\d+>" disconnected'
        }
        self.current_match = None
        self.round_stats = {}
        self.match_stats = {}

    async def start_event_monitoring(self):
        """Iniciar monitoramento de eventos"""
        try:
            while True:
                await self._process_new_events()
                await asyncio.sleep(1)
        except Exception as e:
            self.logger.logger.error(f"Erro no monitoramento de eventos: {e}")

    async def _process_new_events(self):
        """Processar novos eventos do log"""
        try:
            new_events = await self._read_new_events()
            for event in new_events:
                event_type = self._identify_event_type(event)
                if event_type:
                    await self._handle_event(event_type, event)
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar eventos: {e}")

    async def _read_new_events(self):
        """Ler novos eventos do arquivo de log"""
        try:
            with open("/opt/cs2server/logs/cs2/console.log", "r") as f:
                # Usar seek para ler apenas novos eventos
                f.seek(self._get_last_position())
                new_lines = f.readlines()
                self._save_last_position(f.tell())
                return new_lines
        except Exception as e:
            self.logger.logger.error(f"Erro ao ler eventos: {e}")
            return []

    def _identify_event_type(self, event_line):
        """Identificar tipo de evento"""
        for event_type, pattern in self.event_patterns.items():
            if re.match(pattern, event_line):
                return event_type
        return None

    async def _handle_event(self, event_type, event_data):
        """Manipular evento específico"""
        try:
            if event_type == 'kill':
                await self._handle_kill_event(event_data)
            elif event_type == 'round_start':
                await self._handle_round_start()
            elif event_type == 'round_end':
                await self._handle_round_end(event_data)
            elif event_type == 'match_start':
                await self._handle_match_start()
            elif event_type == 'match_end':
                await self._handle_match_end()
            elif event_type == 'player_connect':
                await self._handle_player_connect(event_data)
            elif event_type == 'player_disconnect':
                await self._handle_player_disconnect(event_data)
        except Exception as e:
            self.logger.logger.error(f"Erro ao manipular evento {event_type}: {e}")

    async def _handle_kill_event(self, event_data):
        """Processar evento de kill"""
        try:
            match = re.match(self.event_patterns['kill'], event_data)
            if match:
                killer, weapon, victim, hitbox = match.groups()
                
                # Atualizar estatísticas
                if self.current_match:
                    if killer not in self.match_stats:
                        self.match_stats[killer] = {'kills': 0, 'deaths': 0}
                    if victim not in self.match_stats:
                        self.match_stats[victim] = {'kills': 0, 'deaths': 0}
                        
                    self.match_stats[killer]['kills'] += 1
                    self.match_stats[victim]['deaths'] += 1
                    
                    # Notificar canal de eventos se for headshot
                    if hitbox == "head":
                        channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
                        if channel:
                            await channel.send(
                                f"🎯 **Headshot!** {killer} → {victim} com {weapon}"
                            )
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar kill: {e}")

    async def _handle_round_start(self):
        """Processar início de round"""
        try:
            self.round_stats = {
                'start_time': datetime.now(),
                'kills': [],
                'events': []
            }
            
            # Notificar canal de eventos
            channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
            if channel and self.current_match:
                await channel.send("🔄 Novo round iniciado!")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar início de round: {e}")

    async def _handle_round_end(self, event_data):
        """Processar fim de round"""
        try:
            match = re.match(self.event_patterns['round_end'], event_data)
            if match:
                winner_team = match.group(1)
                
                # Atualizar estatísticas
                if self.current_match:
                    self.current_match['rounds'] += 1
                    if winner_team == "CT":
                        self.current_match['score_ct'] += 1
                    else:
                        self.current_match['score_t'] += 1
                    
                    # Notificar canal de eventos
                    channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
                    if channel:
                        await channel.send(
                            f"🏁 Round terminado!\n"
                            f"Vencedor: {winner_team}\n"
                            f"Placar: CT {self.current_match['score_ct']} x "
                            f"{self.current_match['score_t']} T"
                        )
                        
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar fim de round: {e}")

    async def _handle_match_start(self):
        """Processar início de partida"""
        try:
            self.current_match = {
                'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'start_time': datetime.now(),
                'rounds': 0,
                'score_ct': 0,
                'score_t': 0,
                'players': {},
                'events': []
            }
            
            # Notificar canal de eventos
            channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
            if channel:
                await channel.send("🎮 **Nova partida iniciada!**")
                
            self.logger.logger.info(f"Nova partida iniciada: {self.current_match['id']}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar início de partida: {e}")

    async def _handle_match_end(self):
        """Processar fim de partida"""
        try:
            if self.current_match:
                self.current_match['end_time'] = datetime.now()
                
                # Criar resumo da partida
                duration = self.current_match['end_time'] - self.current_match['start_time']
                
                embed = discord.Embed(
                    title="🏁 Partida Finalizada",
                    description=f"Duração: {duration.total_seconds() // 60:.0f} minutos",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="Placar Final",
                    value=f"CT {self.current_match['score_ct']} x "
                          f"{self.current_match['score_t']} T",
                    inline=False
                )
                
                # Top 3 jogadores
                top_players = sorted(
                    self.match_stats.items(),
                    key=lambda x: x[1]['kills'],
                    reverse=True
                )[:3]
                
                embed.add_field(
                    name="Top Jogadores",
                    value="\n".join([
                        f"{i+1}. {player} - {stats['kills']} kills"
                        for i, (player, stats) in enumerate(top_players)
                    ]),
                    inline=False
                )
                
                # Enviar resumo
                channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
                if channel:
                    await channel.send(embed=embed)
                
                # Salvar estatísticas
                await self._save_match_stats()
                
                # Limpar dados
                self.current_match = None
                self.match_stats = {}
                
            self.logger.logger.info("Partida finalizada")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar fim de partida: {e}")

    async def _handle_player_connect(self, event_data):
        """Processar conexão de jogador"""
        try:
            match = re.match(self.event_patterns['player_connect'], event_data)
            if match:
                player_name = match.group(1)
                
                if self.current_match:
                    self.current_match['players'][player_name] = {
                        'connect_time': datetime.now(),
                        'team': None
                    }
                
                channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
                if channel:
                    await channel.send(f"👋 {player_name} entrou no servidor!")
                    
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar conexão de jogador: {e}")

    async def _handle_player_disconnect(self, event_data):
        """Processar desconexão de jogador"""
        try:
            match = re.match(self.event_patterns['player_disconnect'], event_data)
            if match:
                player_name = match.group(1)
                
                if self.current_match and player_name in self.current_match['players']:
                    del self.current_match['players'][player_name]
                
                channel = self.bot.get_channel(int(os.getenv('CHANNEL_EVENTS')))
                if channel:
                    await channel.send(f"👋 {player_name} saiu do servidor!")
                    
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar desconexão de jogador: {e}")

    async def _save_match_stats(self):
        """Salvar estatísticas da partida"""
        try:
            if not self.current_match:
                return

            # Salvar no banco de dados
            query = """
                INSERT INTO match_stats 
                (match_id, start_time, end_time, score_ct, score_t, stats_data)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            
            await self.bot.db.pool.execute(
                query,
                self.current_match['id'],
                self.current_match['start_time'],
                self.current_match['end_time'],
                self.current_match['score_ct'],
                self.current_match['score_t'],
                json.dumps(self.match_stats)
            )
            
            self.logger.logger.info(
                f"Estatísticas da partida {self.current_match['id']} salvas"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar estatísticas: {e}")

    def _get_last_position(self):
        """Obter última posição lida do arquivo de log"""
        try:
            with open("/opt/cs2server/config/log_position", "r") as f:
                return int(f.read().strip())
        except:
            return 0

    def _save_last_position(self, position):
        """Salvar última posição lida do arquivo de log"""
        try:
            with open("/opt/cs2server/config/log_position", "w") as f:
                f.write(str(position))
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar posição do log: {e}")

def setup(bot):
    bot.add_cog(CS2EventManager(bot))