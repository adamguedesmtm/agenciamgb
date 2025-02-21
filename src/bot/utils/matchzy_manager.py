"""
Matchzy Manager for CS2 Server (5v5)
Author: adamguedesmtm
Created: 2025-02-21 13:21:23
"""

from typing import Dict, List, Optional, Tuple
from .rcon_manager import RCONManager
from .config_manager import ConfigManager
from .metrics import MetricsManager
from .logger import Logger
from .map_manager import MapManager, MapInfo, MapStatus
from datetime import datetime
import json

class MatchStatus:
    WARMUP = "warmup"
    LIVE = "live"
    HALFTIME = "halftime"
    OVERTIME = "overtime"
    FINISHED = "finished"

class MatchzyManager:
    def __init__(self,
                 rcon_manager: RCONManager,
                 config_manager: ConfigManager,
                 metrics_manager: MetricsManager):
        self.logger = Logger('matchzy_manager')
        self.rcon = rcon_manager
        self.config = config_manager
        self.metrics = metrics_manager
        self.map_manager = MapManager()
        
        self._current_match: Optional[Dict] = None
        self._matches_history: List[Dict] = []
        
        # Backup configs
        self._backup_config = {}
        
    async def setup_competitive_config(self):
        """Configurar servidor para 5v5 competitivo"""
        try:
            # Backup config atual
            self._backup_config = {
                'mp_maxrounds': await self.rcon.execute("mp_maxrounds"),
                'mp_overtime_enable': await self.rcon.execute("mp_overtime_enable"),
                'mp_overtime_maxrounds': await self.rcon.execute("mp_overtime_maxrounds")
            }
            
            commands = [
                "mp_maxrounds 24",           # Primeiro a 13
                "mp_overtime_enable 1",       # Overtime habilitado
                "mp_overtime_maxrounds 6",    # MR6 no overtime
                "mp_roundtime 1.92",         # 1:55 tempo de round
                "mp_freezetime 15",          # 15s freezetime
                "sv_maxplayers 12",          # 10 players + 2 coaches
                "mp_warmuptime 60",          # 1min warmup
                "mp_warmup_pausetimer 0",    # Não pausar timer
                "mp_halftime_duration 15",    # 15s intervalo
                "mp_match_can_clinch 1",     # Vitória antecipada
                "mp_maxmoney 16000",         # Max dinheiro
                "mp_startmoney 800",         # Dinheiro inicial
                "mp_friendlyfire 1",         # Fogo amigo
                "sv_deadtalk 0",             # Mortos não falam
                "sv_talk_enemy_dead 0",      # Sem all chat mortos
                "sv_talk_enemy_living 0",    # Sem all chat vivos
                "sv_competitive_minspec 1",   # Config competitiva
                "mp_overtime_starthealth 100", # HP overtime
                "mp_overtime_startmoney 10000", # Dinheiro overtime
                "sv_coaching_enabled 1",      # Permitir coaches
                "mp_autoteambalance 0",      # Sem auto-balance
                "mp_limitteams 0"            # Sem limite times
            ]
            
            for cmd in commands:
                await self.rcon.execute(cmd)
                
            self.logger.logger.info("Configurações competitivas aplicadas")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao configurar 5v5: {e}")
            return False
            
    async def create_match(self,
                          team1: Dict[str, any],
                          team2: Dict[str, any],
                          maps: List[str],
                          captains: Tuple[str, str]) -> bool:
        """
        Criar partida 5v5
        
        Args:
            team1: Info do time 1 (name, players, coach?)
            team2: Info do time 2
            maps: Lista de mapas escolhidos
            captains: Tupla com Steam IDs dos capitães
            
        Returns:
            True se criada com sucesso
        """
        try:
            if not maps:
                return False
                
            # Setup servidor
            await self.setup_competitive_config()
            
            # Registrar partida
            match_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            self._current_match = {
                'id': match_id,
                'team1': team1,
                'team2': team2,
                'maps': maps,
                'current_map': 0,
                'map_scores': {},
                'status': MatchStatus.WARMUP,
                'captains': captains,
                'start_time': datetime.utcnow().isoformat()
            }
            
            # Carregar primeiro mapa
            await self.load_map(maps[0])
            
            # Setup times
            await self._setup_teams(team1, team2)
            
            await self.metrics.record_metric(
                'matchzy.match_created',
                1,
                {
                    'map': maps[0],
                    'teams': f"{team1['name']}_{team2['name']}"
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar partida: {e}")
            return False
            
    async def _setup_teams(self, team1: Dict, team2: Dict):
        """Setup inicial dos times"""
        try:
            # Limpar times
            await self.rcon.execute("mp_teamswitch_clear")
            
            # Time 1 = CT
            for player in team1['players']:
                await self.rcon.execute(f"mp_teamswitch_ct {player}")
                
            if team1.get('coach'):
                await self.rcon.execute(f"mp_teamswitch_ct {team1['coach']}")
                await self.rcon.execute(f"coach_add {team1['coach']}")
                
            # Time 2 = T
            for player in team2['players']:
                await self.rcon.execute(f"mp_teamswitch_t {player}")
                
            if team2.get('coach'):
                await self.rcon.execute(f"mp_teamswitch_t {team2['coach']}")
                await self.rcon.execute(f"coach_add {team2['coach']}")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao setup times: {e}")
            
    async def load_map(self, map_name: str) -> bool:
        """Carregar mapa específico"""
        try:
            if not self._current_match:
                return False
                
            # Carregar mapa
            await self.rcon.execute(f"map {map_name}")
            await self.rcon.execute("mp_warmup_start")
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar mapa: {e}")
            return False
            
    async def start_match(self) -> bool:
        """Iniciar partida (após warmup)"""
        try:
            if not self._current_match:
                return False
                
            await self.rcon.execute("mp_warmup_end")
            self._current_match['status'] = MatchStatus.LIVE
            
            await self.metrics.record_metric(
                'matchzy.match_started',
                1,
                {'match_id': self._current_match['id']}
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar partida: {e}")
            return False
            
    async def end_match(self, force: bool = False) -> bool:
        """Finalizar partida atual"""
        try:
            if not self._current_match:
                return False
                
            if force:
                await self.rcon.execute("mp_endmatch_votenextmap 0")
                await self.rcon.execute("mp_endmatch")
                
            # Salvar histórico
            self._current_match['end_time'] = datetime.utcnow().isoformat()
            self._matches_history.append(self._current_match)
            
            # Restaurar configs
            for cmd, value in self._backup_config.items():
                if value:
                    await self.rcon.execute(f"{cmd} {value}")
                    
            self._current_match = None
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao finalizar partida: {e}")
            return False
            
    async def get_match_status(self) -> Optional[Dict]:
        """Obter status atual da partida"""
        try:
            if not self._current_match:
                return None
                
            # Atualizar placar
            response = await self.rcon.execute("mp_getstatus")
            if response:
                lines = response.split('\n')
                for line in lines:
                    if 'Score:' in line:
                        scores = line.split(':')[1].strip().split('-')
                        current_map = self._current_match['maps'][self._current_match['current_map']]
                        self._current_match['map_scores'][current_map] = {
                            'team1': int(scores[0]),
                            'team2': int(scores[1])
                        }
                        
            return self._current_match
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            return None