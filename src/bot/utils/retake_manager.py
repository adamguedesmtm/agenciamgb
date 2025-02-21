"""
Retake Manager
Author: adamguedesmtm
Created: 2025-02-21 13:55:14
"""

import asyncio
from typing import Dict, List, Optional
from .logger import Logger
from .metrics import MetricsManager
from .rcon_manager import RCONManager
from .map_manager import MapManager

class RetakeManager:
    def __init__(self,
                 rcon: RCONManager,
                 map_manager: MapManager,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.rcon = rcon
        self.map_manager = map_manager
        self.logger = logger or Logger('retake_manager')
        self.metrics = metrics
        self.active_sessions: Dict[str, Dict] = {}
        self.session_counter = 0

    async def setup_server(self, player_count: int) -> Optional[Dict]:
        """Configurar servidor retake"""
        try:
            # Gerar ID único para a sessão
            self.session_counter += 1
            session_id = f"rt_{self.session_counter}"

            # Selecionar mapa
            map_name = await self.map_manager.get_next_map('retake')
            if not map_name:
                raise Exception("Nenhum mapa disponível")

            # Configurar servidor
            await self.rcon.execute("mp_autoteambalance 1")
            await self.rcon.execute("mp_limitteams 0")
            await self.rcon.execute("mp_maxrounds 0")  # Infinito
            await self.rcon.execute("mp_roundtime 1.92")  # ~2 minutos
            await self.rcon.execute("mp_freezetime 3")
            await self.rcon.execute("mp_respawn_on_death_t 1")
            await self.rcon.execute("mp_respawn_on_death_ct 1")
            
            # Configurar proporção CT/T
            ct_ratio = 0.6  # 60% CT, 40% T
            max_players = min(player_count, 10)
            ct_players = int(max_players * ct_ratio)
            t_players = max_players - ct_players
            
            await self.rcon.execute(f"mp_limitteams {max_players}")
            await self.rcon.execute(f"mp_maxplayers {max_players}")
            
            # Gerar senha única
            session_password = f"rt_{session_id}"
            await self.rcon.set_password(session_password)

            # Trocar mapa
            if not await self.rcon.change_map(map_name):
                raise Exception("Falha ao trocar mapa")

            # Registrar sessão
            self.active_sessions[session_id] = {
                'id': session_id,
                'map': map_name,
                'password': session_password,
                'max_players': max_players,
                'ct_players': ct_players,
                't_players': t_players,
                'status': 'active'
            }

            if self.metrics:
                await self.metrics.record_command('retake_session_start')

            return {
                'ip': self.rcon.host,
                'port': self.rcon.port,
                'password': session_password,
                'map': map_name,
                'max_players': max_players
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao configurar servidor retake: {e}")
            return None

    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Obter informações da sessão"""
        try:
            if session_id not in self.active_sessions:
                return None

            session = self.active_sessions[session_id]
            server_info = await self.rcon.get_status()

            return {
                'id': session['id'],
                'map': session['map'],
                'ip': self.rcon.host,
                'port': self.rcon.port,
                'password': session['password'],
                'status': session['status'],
                'max_players': session['max_players'],
                'ct_players': session['ct_players'],
                't_players': session['t_players'],
                'players_online': server_info['players_online'] if server_info else 0
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da sessão: {e}")
            return None

    async def rotate_map(self) -> bool:
        """Rotacionar mapa"""
        try:
            # Selecionar novo mapa
            current_map = (await self.rcon.get_status())['map']
            next_map = await self.map_manager.get_next_map(
                'retake',
                exclude=[current_map]
            )

            if not next_map:
                return False

            # Avisar jogadores
            await self.rcon.send_message(f"Trocando mapa para {next_map}...")
            
            # Trocar mapa
            success = await self.rcon.change_map(next_map)
            
            if success and self.metrics:
                await self.metrics.record_command('retake_map_rotation')
                
            return success

        except Exception as e:
            self.logger.logger.error(f"Erro ao rotacionar mapa: {e}")
            return False

    async def get_server_info(self) -> Optional[Dict]:
        """Obter informações do servidor"""
        try:
            status = await self.rcon.get_status()
            if not status:
                return None

            return {
                'ip': self.rcon.host,
                'port': self.rcon.port,
                'map': status['map'],
                'players_online': status['players_online'],
                'max_players': 10,
                'status': 'online' if status else 'offline'
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do servidor: {e}")
            return None

    async def change_map(self, map_name: str) -> bool:
        """Trocar mapa do servidor"""
        return await self.rcon.change_map(map_name)

    async def kick_player(self, steam_id: str, reason: str = "") -> bool:
        """Kickar jogador do servidor"""
        return await self.rcon.kick_player(steam_id, reason)

    async def restart_server(self) -> bool:
        """Reiniciar servidor"""
        try:
            # Limpar sessões ativas
            self.active_sessions.clear()
            
            # Reiniciar servidor
            return await self.rcon.execute("_restart") is not None

        except Exception as e:
            self.logger.logger.error(f"Erro ao reiniciar servidor: {e}")
            return False

    async def balance_teams(self) -> bool:
        """Balancear times automaticamente"""
        try:
            return await self.rcon.execute("mp_scrambleteams 1") is not None

        except Exception as e:
            self.logger.logger.error(f"Erro ao balancear times: {e}")
            return False