"""
Matchzy Manager - CS2 Server Management System
Author: adamguedesmtm
Created: 2025-02-21 14:59:00
"""

from typing import Dict, Optional, Set
from datetime import datetime
import asyncio
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
        
        # Estado do servidor
        self.active_server = None
        self.match_state = {
            'active': False,
            'warmup': True,
            'paused': False,
            'map': None,
            'round': 0,
            'score_ct': 0,
            'score_t': 0
        }
        
        # Estado do BO3
        self.bo3_state = {
            'active': False,
            'maps': [],
            'current_map': 0,
            'scores': {'team1': 0, 'team2': 0}
        }
        
        # Estado dos jogadores
        self.teams = {
            'CT': set(),
            'T': set(),
            'SPEC': set()
        }
        self.players = {}
        self.ready_players = set()
        
        # Callbacks para eventos
        self.on_knife_round_start = None
        self.on_warmup_end = None
        self.match_id = None
        
        # Lock para operações concorrentes
        self.server_lock = asyncio.Lock()

    async def register_callbacks(self, on_knife_round_start=None, on_warmup_end=None):
        """Registrar callbacks para eventos"""
        self.on_knife_round_start = on_knife_round_start
        self.on_warmup_end = on_warmup_end

    async def setup_match(self, match_type: str, is_bo3: bool = False) -> Dict:
        """Configurar nova partida"""
        try:
            async with self.server_lock:
                # Verificar se já existe servidor ativo
                if self.active_server:
                    return {
                        'error': True,
                        'message': 'Já existe um servidor ativo'
                    }

                # Configurar servidor
                config = await self._configure_server(match_type)
                if not config:
                    return {
                        'error': True,
                        'message': 'Erro ao configurar servidor'
                    }

                # Configurar estado inicial
                self.active_server = {
                    'ip': config['ip'],
                    'port': config['port'],
                    'gotv': config['gotv'],
                    'match_type': match_type
                }

                self._reset_match_state()

                # Configurar BO3 se necessário
                if is_bo3 and match_type == 'competitive':
                    self.bo3_state = {
                        'active': True,
                        'maps': [],
                        'current_map': 0,
                        'scores': {'team1': 0, 'team2': 0}
                    }

                # Gerar ID único para a partida
                self.match_id = f"{int(datetime.utcnow().timestamp())}"

                # Registrar métricas
                if self.metrics:
                    self.metrics.record_match_setup(match_type, is_bo3)

                return {
                    'success': True,
                    'match_id': self.match_id,
                    **self.active_server
                }

        except Exception as e:
            self.logger.error(f"Erro ao configurar partida: {e}")
            return {
                'error': True,
                'message': f'Erro ao configurar servidor: {str(e)}'
            }

    async def _configure_server(self, match_type: str) -> Optional[Dict]:
        """Configurar servidor CS2"""
        try:
            # Configurações específicas para cada modo
            config = {
                'competitive': {
                    'maxplayers': 12,
                    'maxrounds': 30,
                    'configs': [
                        "mp_autoteambalance 0",
                        "mp_randomspawn 0",
                        "mp_warmuptime 60",
                        "mp_round_restart_delay 5",
                        "mp_freezetime 15",
                        "mp_match_can_clinch 1"
                    ]
                },
                'wingman': {
                    'maxplayers': 4,
                    'maxrounds': 16,
                    'configs': [
                        "mp_autoteambalance 0",
                        "mp_randomspawn 0",
                        "mp_warmuptime 30",
                        "mp_round_restart_delay 3",
                        "mp_freezetime 10"
                    ]
                },
                'practice': {
                    'maxplayers': 10,
                    'maxrounds': 0,
                    'configs': [
                        "mp_autoteambalance 1",
                        "mp_randomspawn 1",
                        "mp_warmuptime 0",
                        "mp_round_restart_delay 2",
                        "mp_freezetime 3"
                    ]
                }
            }

            if match_type not in config:
                return None

            # Aplicar configurações
            settings = config[match_type]
            await self.rcon.execute(f"maxplayers {settings['maxplayers']}")
            await self.rcon.execute(f"mp_maxrounds {settings['maxrounds']}")
            
            # Aplicar configurações específicas
            for cmd in settings['configs']:
                await self.rcon.execute(cmd)

            # Obter informações do servidor
            server_info = await self.rcon.get_server_info()
            return server_info

        except Exception as e:
            self.logger.error(f"Erro ao configurar servidor: {e}")
            return None

    async def process_game_event(self, event_type: str, data: Dict):
        """Processar eventos do jogo"""
        try:
            if event_type == "knife_round_start":
                if self.on_knife_round_start and self.active_server['match_type'] != 'practice':
                    await self.on_knife_round_start(self.match_id)
                    
            elif event_type == "warmup_end":
                if self.bo3_state['active'] and self.on_warmup_end:
                    await self.on_warmup_end(self.match_id)
                    
            elif event_type == "round_end":
                await self._update_match_state(data)

        except Exception as e:
            self.logger.error(f"Erro ao processar evento do jogo: {e}")

    def _reset_match_state(self):
        """Resetar estado da partida"""
        self.match_state = {
            'active': False,
            'warmup': True,
            'paused': False,
            'map': None,
            'round': 0,
            'score_ct': 0,
            'score_t': 0
        }
        self.teams = {'CT': set(), 'T': set(), 'SPEC': set()}
        self.players = {}
        self.ready_players = set()

    async def _update_match_state(self, data: Dict):
        """Atualizar estado da partida"""
        try:
            self.match_state.update(data)
            
            # Registrar estatísticas
            if self.stats_manager:
                await self.stats_manager.update_match_stats(
                    self.match_id,
                    self.match_state
                )

        except Exception as e:
            self.logger.error(f"Erro ao atualizar estado da partida: {e}")

    async def end_match(self) -> bool:
        """Finalizar partida atual"""
        try:
            async with self.server_lock:
                if not self.active_server:
                    return False

                # Salvar estatísticas finais
                if self.stats_manager:
                    await self.stats_manager.save_match_stats(self.match_id, self.match_state)

                # Limpar estado
                self.active_server = None
                self._reset_match_state()
                self.bo3_state = {
                    'active': False,
                    'maps': [],
                    'current_map': 0,
                    'scores': {'team1': 0, 'team2': 0}
                }

                return True

        except Exception as e:
            self.logger.error(f"Erro ao finalizar partida: {e}")
            return False