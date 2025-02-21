"""
Wingman Manager for CS2 Server (2v2)
Author: adamguedesmtm
Created: 2025-02-21 13:22:35
"""

from typing import Dict, List, Optional, Tuple
from .rcon_manager import RCONManager
from .config_manager import ConfigManager
from .metrics import MetricsManager
from .logger import Logger
from .map_manager import MapManager, MapInfo, MapStatus
from datetime import datetime

class WingmanStatus:
    WARMUP = "warmup"
    LIVE = "live"
    HALFTIME = "halftime"
    OVERTIME = "overtime"
    FINISHED = "finished"

class WingmanManager:
    def __init__(self,
                 rcon_manager: RCONManager,
                 config_manager: ConfigManager,
                 metrics_manager: MetricsManager):
        self.logger = Logger('wingman_manager')
        self.rcon = rcon_manager
        self.config = config_manager
        self.metrics = metrics_manager
        self.map_manager = MapManager()
        
        self._current_match: Optional[Dict] = None
        self._matches_history: List[Dict] = []
        self._backup_config = {}

    async def setup_wingman_config(self):
        """Configurar servidor para 2v2"""
        try:
            # Backup config atual
            self._backup_config = {
                'mp_maxrounds': await self.rcon.execute("mp_maxrounds"),
                'mp_overtime_enable': await self.rcon.execute("mp_overtime_enable")
            }
            
            commands = [
                "mp_maxrounds 16",           # Primeiro a 9
                "mp_overtime_enable 1",       # Overtime habilitado
                "mp_overtime_maxrounds 6",    # MR6 no overtime
                "mp_roundtime 1.92",         # 1:55 tempo de round
                "mp_freezetime 10",          # 10s freezetime (menor que 5v5)
                "sv_maxplayers 4",           # Max 4 jogadores
                "mp_warmuptime 30",          # 30s warmup
                "mp_warmup_pausetimer 0",    # Não pausar timer
                "mp_halftime_duration 10",    # 10s intervalo
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
                "sv_coaching_enabled 0",      # Sem coaches em 2v2
                "mp_autoteambalance 0",      # Sem auto-balance
                "mp_limitteams 0"            # Sem limite times
            ]
            
            for cmd in commands:
                await self.rcon.execute(cmd)
                
            self.logger.logger.info("Configurações wingman aplicadas")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao configurar 2v2: {e}")
            return False
            
    async def create_match(self,
                          team1: Dict[str, any],
                          team2: Dict[str, any],
                          map_name: str) -> bool:
        """
        Criar partida 2v2
        
        Args:
            team1: Info do time 1 (name, players)
            team2: Info do time 2
            map_name: Mapa escolhido
            
        Returns:
            True se criada com sucesso
        """
        try:
            if len(team1['players']) != 2 or len(team2['players']) != 2:
                return False
                
            # Setup servidor
            await self.setup_wingman_config()
            
            # Registrar partida
            match_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            self._current_match = {
                'id': match_id,
                'team1': team1,
                'team2': team2,
                'map': map_name,
                'score': {'team1': 0, 'team2': 0},
                'status': WingmanStatus.WARMUP,
                'start_time': datetime.utcnow().isoformat()
            }
            
            # Carregar mapa
            await self.load_map(map_name)
            
            # Setup times
            await self._setup_teams(team1, team2)
            
            await self.metrics.record_metric(
                'wingman.match_created',
                1,
                {
                    'map': map_name,
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
                
            # Time 2 = T    
            for player in team2['players']:
                await self.rcon.execute(f"mp_teamswitch_t {player}")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao setup times: {e}")
            
    async def load_map(self, map_name: str) -> bool:
        """Carregar mapa wingman"""
        try:
            if map_name not in self.map_manager._wingman_maps:
                return False
                
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
            self._current_match['status'] = WingmanStatus.LIVE
            
            await self.metrics.record_metric(
                'wingman.match_started',
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
                        self._current_match['score'] = {
                            'team1': int(scores[0]),
                            'team2': int(scores[1])
                        }
                        
            return self._current_match
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            return None