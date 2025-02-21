"""
Matchzy Manager - CS2 Match Management System
Author: adamguedesmtm
Created: 2025-02-21 14:32:47
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
import discord
from .logger import Logger
from .metrics import MetricsManager
from .stats_manager import StatsManager
from .rcon_manager import RconManager

class MatchzyManager:
    def __init__(self,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None,
                 stats_manager: Optional[StatsManager] = None):
        self.logger = logger or Logger('matchzy')
        self.metrics = metrics
        self.stats_manager = stats_manager
        self.rcon = RconManager()
        
        # Controle de servidor ativo
        self.active_server = None  # Guarda informações do servidor ativo
        self.server_lock = asyncio.Lock()  # Lock para operações no servidor
        
        # Estado do jogo
        self.match_state = {
            'active': False,
            'warmup': False,
            'paused': False,
            'map': '',
            'score_ct': 0,
            'score_t': 0,
            'round': 0,
            'tech_pause': False,
            'tech_pauses_CT': 0,
            'tech_pauses_T': 0,
            'unpause_votes': set()
        }

        # Controle de equipes
        self.teams = {
            'CT': set(),  # Set de discord_ids
            'T': set(),
            'SPEC': set()
        }
        
        # Controle de jogadores
        self.players = {}  # discord_id -> player_info
        self.ready_players = set()  # Set de discord_ids
        self.locked_teams = False  # Bloqueio de mudança de equipe

    async def setup_match(self, match_type: str) -> Dict:
        """Configurar nova partida"""
        try:
            async with self.server_lock:
                # Verificar se já existe um servidor ativo
                if self.active_server:
                    self.logger.error("Tentativa de criar servidor quando já existe um ativo")
                    return {
                        'error': True,
                        'message': 'Já existe um servidor ativo! Use !status para ver detalhes ou !forceend para encerrá-lo.'
                    }

                # Resetar estado
                self._reset_match_state()
                
                # Configurações base
                base_config = {
                    'sv_cheats': '0',
                    'mp_autokick': '0',
                    'mp_autoteambalance': '0',
                    'mp_limitteams': '0',
                    'sv_full_alltalk': '0',
                    'sv_deadtalk': '0',
                    'sv_allow_votes': '0',
                    'sv_coaching_enabled': '1',
                    'mp_match_end_restart': '1',
                    'mp_match_end_changelevel': '1',
                    'mp_match_restart_delay': '10',
                    'mp_endmatch_votenextmap': '0',
                    'mp_endmatch_votenextleveltime': '0',
                    'mp_warmuptime': '300',
                    'mp_warmup_pausetimer': '1',
                    'mp_halftime': '1',
                    'mp_team_timeout_max': '4',
                    'mp_team_timeout_time': '180'
                }

                # Configurações específicas por tipo de partida
                match_configs = {
                    'competitive': {
                        'mp_maxrounds': '30',
                        'mp_match_can_clinch': '1',
                        'mp_overtime_enable': '1',
                        'mp_overtime_maxrounds': '6',
                        'mp_overtime_startmoney': '16000',
                        'mp_roundtime': '1.92',
                        'mp_roundtime_defuse': '1.92',
                        'mp_round_restart_delay': '7',
                        'mp_freezetime': '15',
                        'mp_buytime': '20',
                        'mp_c4timer': '40'
                    },
                    'wingman': {
                        'mp_maxrounds': '16',
                        'mp_match_can_clinch': '1',
                        'mp_overtime_enable': '0',
                        'mp_roundtime': '1.92',
                        'mp_roundtime_defuse': '1.92',
                        'mp_round_restart_delay': '5',
                        'mp_freezetime': '10',
                        'mp_buytime': '15',
                        'mp_c4timer': '40'
                    },
                    'practice': {
                        'mp_maxrounds': '999',
                        'mp_match_can_clinch': '0',
                        'mp_overtime_enable': '0',
                        'mp_roundtime': '60',
                        'mp_roundtime_defuse': '60',
                        'mp_round_restart_delay': '3',
                        'mp_freezetime': '2',
                        'mp_buytime': '3600',
                        'mp_c4timer': '40',
                        'sv_cheats': '1',
                        'sv_infinite_ammo': '1',
                        'mp_warmup_pausetimer': '0'
                    }
                }

                # Aplicar configurações base
                for cvar, value in base_config.items():
                    await self.rcon.execute(f'{cvar} {value}')

                # Aplicar configurações específicas
                config = match_configs.get(match_type, match_configs['competitive'])
                for cvar, value in config.items():
                    await self.rcon.execute(f'{cvar} {value}')

                # Iniciar warmup
                self.match_state['warmup'] = True
                await self.rcon.execute('mp_warmup_start')
                await self.setup_cs2_listeners()

                # Registrar servidor ativo
                server_info = {
                    'ip': await self.rcon.get_server_ip(),
                    'port': await self.rcon.get_server_port(),
                    'gotv': await self.rcon.get_gotv_port(),
                    'match_type': match_type,
                    'start_time': datetime.utcnow(),
                    'connect_cmd': await self.rcon.get_connect_command()
                }
                
                self.active_server = server_info

                if self.metrics:
                    await self.metrics.record_player_stat('matches_setup', match_type)

                return {
                    'success': True,
                    **server_info
                }

        except Exception as e:
            self.logger.error(f"Erro ao configurar partida: {e}")
            return {
                'error': True,
                'message': f'Erro ao configurar servidor: {str(e)}'
            }

    async def process_cs2_command(self, steam_id: str, command: str) -> bool:
        """Processar comandos vindos do servidor CS2"""
        try:
            # Encontrar discord_id do jogador pelo steam_id
            discord_id = None
            for pid, pinfo in self.players.items():
                if pinfo['steam_id'] == steam_id:
                    discord_id = pid
                    break

            if not discord_id:
                return False

            command = command.lower()
            player_team = self.players[discord_id]['team']
            player_name = self.players[discord_id]['name']

            match command:
                case "!ready":
                    if self.match_state['active']:
                        await self.rcon.execute('say "Partida já está em andamento!"')
                        return False
                    if discord_id in self.ready_players:
                        await self.rcon.execute(f'say "{player_name} já está pronto!"')
                        return False
                    self.ready_players.add(discord_id)
                    self.players[discord_id]['ready'] = True
                    await self.rcon.execute(f'say "{player_name} está pronto! ({len(self.ready_players)}/{len(self.players)} prontos)"')
                    
                    # Verificar se todos estão prontos
                    if self._all_players_ready() and self._are_teams_balanced():
                        await self.start_match()
                    return True

                case "!unready":
                    if self.match_state['active']:
                        return False
                    if discord_id not in self.ready_players:
                        await self.rcon.execute(f'say "{player_name} não estava pronto!"')
                        return False
                    self.ready_players.discard(discord_id)
                    self.players[discord_id]['ready'] = False
                    await self.rcon.execute(f'say "{player_name} não está mais pronto! ({len(self.ready_players)}/{len(self.players)} prontos)"')
                    return True

                case "!pause":
                    if not self.match_state['active']:
                        return False
                    if self.match_state['paused']:
                        await self.rcon.execute('say "Partida já está pausada!"')
                        return False
                    await self.rcon.execute('mp_pause_match')
                    self.match_state['paused'] = True
                    await self.rcon.execute(f'say "Partida pausada por {player_name}"')
                    return True

                case "!tech":
                    if not self.match_state['active'] or self.match_state['paused']:
                        return False
                    if self.match_state[f'tech_pauses_{player_team}'] >= 4:
                        await self.rcon.execute(f'say "Time {player_team} não tem mais pauses técnicos!"')
                        return False
                    await self.rcon.execute('mp_pause_match')
                    self.match_state['paused'] = True
                    self.match_state['tech_pause'] = True
                    self.match_state[f'tech_pauses_{player_team}'] += 1
                    await self.rcon.execute(f'say "Pause técnico por {player_name} ({self.match_state[f"tech_pauses_{player_team}"]}/4 restantes)"')
                    asyncio.create_task(self._tech_pause_timer())
                    return True

                case "!unpause":
                    if not self.match_state['active'] or not self.match_state['paused']:
                        return False
                    if self.match_state['tech_pause']:
                        await self.rcon.execute('say "Aguarde o fim do pause técnico!"')
                        return False
                    self.match_state['unpause_votes'].add(player_team)
                    remaining = 2 - len(self.match_state['unpause_votes'])
                    await self.rcon.execute(f'say "Time {player_team} votou para despausar! (Faltam {remaining} votos)"')
                    if len(self.match_state['unpause_votes']) == 2:
                        await self.rcon.execute('mp_unpause_match')
                        self.match_state['paused'] = False
                        self.match_state['unpause_votes'].clear()
                        await self.rcon.execute('say "Partida despausada!"')
                    return True

                case "!score":
                    score_message = f"Score: CT {self.match_state['score_ct']} - {self.match_state['score_t']} T (Round {self.match_state['round']})"
                    await self.rcon.execute(f'say "{score_message}"')
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Erro ao processar comando CS2: {e}")
            return False

    async def setup_cs2_listeners(self):
        """Configurar listeners para comandos do CS2"""
        try:
            welcome_message = [
                'say "Comandos disponíveis:"',
                'say "!ready - Marcar como pronto"',
                'say "!unready - Desmarcar pronto"',
                'say "!pause - Pausar partida"',
                'say "!unpause - Despausar partida (requer aprovação dos dois times)"',
                'say "!tech - Pause técnico (3 minutos, 4 por time)"',
                'say "!score - Ver placar atual"'
            ]

            for msg in welcome_message:
                await self.rcon.execute(msg)

            if self.metrics:
                await self.metrics.record_player_stat('cs2_listeners_setup', '1')

            return True

        except Exception as e:
            self.logger.error(f"Erro ao configurar listeners CS2: {e}")
            return False

    async def start_match(self) -> bool:
        """Iniciar partida"""
        try:
            if not self._are_teams_balanced():
                await self.rcon.execute('say "Times precisam estar balanceados para iniciar!"')
                return False

            if not self._all_players_ready():
                await self.rcon.execute('say "Todos os jogadores precisam estar prontos!"')
                return False

            # Bloquear mudanças de equipe
            self.locked_teams = True
            self.match_state['active'] = True
            self.match_state['warmup'] = False

            # Iniciar partida
            await self.rcon.execute('mp_warmup_end')
            await self.rcon.execute('mp_restartgame 1')
            await self.rcon.execute('say "Partida iniciando! Boa sorte a todos!"')

            if self.metrics:
                await self.metrics.record_player_stat('matches_started', '1')

            return True

        except Exception as e:
            self.logger.error(f"Erro ao iniciar partida: {e}")
            return False

    async def end_match(self) -> bool:
        """Finalizar partida"""
        try:
            async with self.server_lock:
                if not self.active_server:
                    return False

                if not self.match_state['active']:
                    return False

                # Desbloquear times
                self.locked_teams = False
                self._reset_match_state()

                # Finalizar via RCON
                await self.rcon.execute('mp_endmatch')
                await self.rcon.execute('say "Partida finalizada!"')

                # Limpar servidor ativo
                self.active_server = None

                if self.metrics:
                    await self.metrics.record_player_stat('matches_ended', '1')

                return True

        except Exception as e:
            self.logger.error(f"Erro ao finalizar partida: {e}")
            return False

    async def get_server_status(self) -> Dict:
        """Obter status do servidor ativo"""
        try:
            if not self.active_server:
                return {
                    'active': False,
                    'message': 'Nenhum servidor ativo'
                }

            uptime = datetime.utcnow() - self.active_server['start_time']
            
            return {
                'active': True,
                'server_info': self.active_server,
                'match_state': {
                    'active': self.match_state['active'],
                    'warmup': self.match_state['warmup'],
                    'paused': self.match_state['paused'],
                                        'map': self.match_state['map'],
                    'score_ct': self.match_state['score_ct'],
                    'score_t': self.match_state['score_t'],
                    'round': self.match_state['round'],
                    'uptime': str(uptime).split('.')[0]  # Formato HH:MM:SS
                },
                'teams': {
                    'CT': len(self.teams['CT']),
                    'T': len(self.teams['T']),
                    'SPEC': len(self.teams['SPEC'])
                }
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter status do servidor: {e}")
            return {
                'error': True,
                'message': f'Erro ao obter status: {str(e)}'
            }

    async def change_map(self, map_name: str) -> bool:
        """Mudar mapa do servidor"""
        try:
            valid_maps = [
                'de_ancient', 'de_anubis', 'de_inferno', 'de_mirage', 
                'de_nuke', 'de_overpass', 'de_vertigo', 'de_dust2'
            ]

            if map_name not in valid_maps:
                return False

            await self.rcon.execute(f'changelevel {map_name}')
            self.match_state['map'] = map_name

            if self.metrics:
                await self.metrics.record_player_stat('map_changes', map_name)

            return True

        except Exception as e:
            self.logger.error(f"Erro ao mudar mapa: {e}")
            return False

    async def _tech_pause_timer(self):
        """Timer para pause técnico"""
        try:
            await asyncio.sleep(150)  # 2:30 minutos
            if self.match_state.get('tech_pause', False):
                await self.rcon.execute('say "30 segundos restantes no pause técnico"')
                await asyncio.sleep(30)
                if self.match_state.get('tech_pause', False):
                    await self.rcon.execute('mp_unpause_match')
                    self.match_state['paused'] = False
                    self.match_state['tech_pause'] = False
                    await self.rcon.execute('say "Pause técnico finalizado"')

        except Exception as e:
            self.logger.error(f"Erro no timer de pause técnico: {e}")

    def _are_teams_balanced(self) -> bool:
        """Verificar se times estão balanceados"""
        ct_count = len(self.teams['CT'])
        t_count = len(self.teams['T'])
        return abs(ct_count - t_count) <= 1 and ct_count > 0 and t_count > 0

    def _all_players_ready(self) -> bool:
        """Verificar se todos os jogadores estão prontos"""
        active_players = set()
        for team in ['CT', 'T']:
            active_players.update(self.teams[team])
        return all(p in self.ready_players for p in active_players)

    def _reset_match_state(self):
        """Resetar estado da partida"""
        self.match_state = {
            'active': False,
            'warmup': False,
            'paused': False,
            'map': '',
            'score_ct': 0,
            'score_t': 0,
            'round': 0,
            'tech_pause': False,
            'tech_pauses_CT': 0,
            'tech_pauses_T': 0,
            'unpause_votes': set()
        }
        
        # Limpar times e jogadores
        for team in self.teams.values():
            team.clear()
        self.players.clear()
        self.ready_players.clear()
        self.locked_teams = False

    async def force_end_server(self) -> bool:
        """Forçar encerramento do servidor"""
        try:
            async with self.server_lock:
                if not self.active_server:
                    return False

                # Finalizar via RCON
                await self.rcon.execute('mp_endmatch')
                await self.rcon.execute('say "Servidor sendo encerrado!"')

                # Limpar estado
                self._reset_match_state()
                self.active_server = None

                if self.metrics:
                    await self.metrics.record_player_stat('server_force_ends', '1')

                return True

        except Exception as e:
            self.logger.error(f"Erro ao forçar encerramento do servidor: {e}")
            return False

    async def update_scores(self, ct_score: int, t_score: int, current_round: int):
        """Atualizar placar da partida"""
        try:
            self.match_state['score_ct'] = ct_score
            self.match_state['score_t'] = t_score
            self.match_state['round'] = current_round

            if self.metrics:
                await self.metrics.record_player_stat('score_updates', '1')

        except Exception as e:
            self.logger.error(f"Erro ao atualizar placar: {e}")