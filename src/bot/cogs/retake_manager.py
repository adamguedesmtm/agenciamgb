"""
Retake Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:23:47
"""

from typing import Dict, List, Optional
from .rcon_manager import RCONManager
from .config_manager import ConfigManager
from .metrics import MetricsManager
from .logger import Logger
from .map_manager import MapManager
from datetime import datetime

class RetakeManager:
    def __init__(self,
                 rcon_manager: RCONManager,
                 config_manager: ConfigManager,
                 metrics_manager: MetricsManager):
        self.logger = Logger('retake_manager')
        self.rcon = rcon_manager
        self.config = config_manager
        self.metrics = metrics_manager
        self.map_manager = MapManager()
        
        self._current_session: Optional[Dict] = None
        self._backup_config = {}
        
    async def setup_retake_config(self):
        """Configurar servidor para retakes"""
        try:
            # Backup config atual
            self._backup_config = {
                'mp_maxrounds': await self.rcon.execute("mp_maxrounds"),
                'mp_roundtime': await self.rcon.execute("mp_roundtime")
            }
            
            commands = [
                "mp_maxrounds 0",            # Infinito
                "mp_roundtime 1.92",         # 1:55 tempo de round
                "mp_freezetime 3",           # 3s freezetime
                "sv_maxplayers 10",          # Max 10 jogadores
                "mp_warmuptime 30",          # 30s warmup
                "mp_warmup_pausetimer 0",    # Não pausar timer
                "mp_autoteambalance 1",      # Auto-balance
                "mp_limitteams 0",           # Sem limite times
                "mp_maxmoney 16000",         # Max dinheiro
                "mp_startmoney 16000",       # Dinheiro inicial
                "mp_friendlyfire 1",         # Fogo amigo
                "sv_deadtalk 1",             # Mortos podem falar
                "mp_randomspawn 1",          # Spawns aleatórios
                "mp_randomspawn_los 1",      # Line of sight spawns
                "mp_weapons_allow_zeus 0",   # Sem zeus
                "mp_ct_default_secondary weapon_usp_silencer", # USP CT
                "mp_t_default_secondary weapon_glock",         # Glock T
                "mp_free_armor 2",           # Armor + Helmet grátis
                "mp_equipment_reset_rounds 1", # Reset equip todo round
                "sm_retakes_enabled 1",       # Plugin retakes
                "sm_retakes_maxplayers 10",   # Max jogadores
                "sm_retakes_ratio_constant 0.4" # 40% T, 60% CT
            ]
            
            for cmd in commands:
                await self.rcon.execute(cmd)
                
            self.logger.logger.info("Configurações retake aplicadas")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao configurar retake: {e}")
            return False
            
    async def start_session(self, map_name: Optional[str] = None) -> bool:
        """
        Iniciar sessão de retake
        
        Args:
            map_name: Mapa específico ou None para aleatório
            
        Returns:
            True se iniciada com sucesso
        """
        try:
            # Setup servidor
            await self.setup_retake_config()
            
            # Escolher mapa aleatório se não especificado
            if not map_name:
                maps = list(self.map_manager._maps.keys())
                map_name = maps[0]  # Primeiro mapa por padrão
                
            # Registrar sessão
            session_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            self._current_session = {
                'id': session_id,
                'map': map_name,
                'players': [],
                'rounds_played': 0,
                'status': 'active',
                'start_time': datetime.utcnow().isoformat()
            }
            
            # Carregar mapa
            await self.rcon.execute(f"map {map_name}")
            
            await self.metrics.record_metric(
                'retake.session_started',
                1,
                {'map': map_name}
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar retake: {e}")
            return False
            
    async def end_session(self) -> bool:
        """Finalizar sessão atual"""
        try:
            if not self._current_session:
                return False
                
            # Restaurar configs
            for cmd, value in self._backup_config.items():
                if value:
                    await self.rcon.execute(f"{cmd} {value}")
                    
            await self.metrics.record_metric(
                'retake.session_ended',
                1,
                {'session_id': self._current_session['id']}
            )
            
            self._current_session = None
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao finalizar retake: {e}")
            return False
            
    async def rotate_map(self) -> bool:
        """Rotacionar para próximo mapa"""
        try:
            if not self._current_session:
                return False
                
            # Escolher próximo mapa
            current = self._current_session['map']
            maps = list(self.map_manager._maps.keys())
            next_index = (maps.index(current) + 1) % len(maps)
            next_map = maps[next_index]
            
            # Carregar novo mapa
            await self.rcon.execute(f"map {next_map}")
            self._current_session['map'] = next_map
            self._current_session['rounds_played'] = 0
            
            await self.metrics.record_metric(
                'retake.map_rotated',
                1,
                {'map': next_map}
            )
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao rotacionar mapa: {e}")
            return False
            
    async def get_session_stats(self) -> Optional[Dict]:
        """Obter estatísticas da sessão"""
        try:
            if not self._current_session:
                return None
                
            # Atualizar info de jogadores
            status = await self.rcon.execute("status")
            if status:
                players = []
                for line in status.split('\n'):
                    if 'STEAM' in line:  # Linha de jogador
                        parts = line.split()
                        players.append({
                            'name': ' '.join(parts[2:-6]),
                            'team': parts[-2],
                            'connected': parts[-1]
                        })
                        
                self._current_session['players'] = players
                
            # Atualizar rounds jogados
            score = await self.rcon.execute("mp_getstatus")
            if score:
                for line in score.split('\n'):
                    if 'Total Rounds Played' in line:
                        self._current_session['rounds_played'] = int(
                            line.split(':')[1].strip()
                        )
                        
            return self._current_session
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats: {e}")
            return None