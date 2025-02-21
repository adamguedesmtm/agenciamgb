"""
Wingman Manager
Author: adamguedesmtm
Created: 2025-02-21 13:53:21
"""

import asyncio
from typing import Dict, List, Optional
from .logger import Logger
from .metrics import MetricsManager
from .rcon_manager import RCONManager
from .map_manager import MapManager

class WingmanManager:
    def __init__(self,
                 rcon: RCONManager,
                 map_manager: MapManager,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.rcon = rcon
        self.map_manager = map_manager
        self.logger = logger or Logger('wingman_manager')
        self.metrics = metrics
        self.active_matches: Dict[str, Dict] = {}
        self.match_counter = 0

    async def create_match(self, players: List[Dict]) -> Optional[str]:
        """Criar nova partida 2v2"""
        try:
            if len(players) != 4:
                raise ValueError("Wingman requer exatamente 4 jogadores")

            # Gerar ID único para a partida
            self.match_counter += 1
            match_id = f"wm_{self.match_counter}"

            # Selecionar mapa
            map_name = await self.map_manager.get_next_map('wingman')
            if not map_name:
                raise Exception("Nenhum mapa disponível")

            # Dividir times (2v2)
            team1 = players[:2]
            team2 = players[2:]

            # Configurar servidor
            await self.rcon.execute("mp_teamsize 2")
            await self.rcon.execute("mp_maxrounds 16")
            await self.rcon.execute("mp_overtime_enable 1")
            
            # Gerar senha única
            match_password = f"wm_{match_id}"
            await self.rcon.set_password(match_password)

            # Trocar mapa
            if not await self.rcon.change_map(map_name):
                raise Exception("Falha ao trocar mapa")

            # Registrar partida
            self.active_matches[match_id] = {
                'id': match_id,
                'map': map_name,
                'team1': team1,
                'team2': team2,
                'password': match_password,
                'status': 'setup',
                'score_team1': 0,
                'score_team2': 0
            }

            if self.metrics:
                await self.metrics.record_match_start('wingman')

            return match_id

        except Exception as e:
            self.logger.logger.error(f"Erro ao criar partida wingman: {e}")
            return None

    async def get_match_info(self, match_id: str) -> Optional[Dict]:
        """Obter informações da partida"""
        try:
            if match_id not in self.active_matches:
                return None

            match = self.active_matches[match_id]
            server_info = await self.rcon.get_status()

            return {
                'id': match['id'],
                'map': match['map'],
                'ip': self.rcon.host,
                'port': self.rcon.port,
                'password': match['password'],
                'status': match['status'],
                'team1': match['team1'],
                'team2': match['team2'],
                'score_team1': match['score_team1'],
                'score_team2': match['score_team2'],
                'players_online': server_info['players_online'] if server_info else 0
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da partida: {e}")
            return None

    async def update_match_score(self, match_id: str, team1_score: int, team2_score: int) -> bool:
        """Atualizar placar da partida"""
        try:
            if match_id not in self.active_matches:
                return False

            self.active_matches[match_id].update({
                'score_team1': team1_score,
                'score_team2': team2_score
            })

            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar placar: {e}")
            return False

    async def end_match(self, match_id: str) -> bool:
        """Finalizar partida"""
        try:
            if match_id not in self.active_matches:
                return False

            match = self.active_matches[match_id]
            
            # Registrar métricas
            if self.metrics:
                await self.metrics.record_match_duration('wingman')
                
                # Registrar stats dos jogadores
                for team in [match['team1'], match['team2']]:
                    for player in team:
                        await self.metrics.record_player_stat(
                            'matches_played',
                            player['id']
                        )

            # Limpar servidor
            await self.rcon.execute("mp_warmup_end")
            await self.rcon.set_password("")

            # Remover partida
            del self.active_matches[match_id]

            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao finalizar partida: {e}")
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
                'max_players': 4,
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
            # Limpar partidas ativas
            self.active_matches.clear()
            
            # Reiniciar servidor
            return await self.rcon.execute("_restart") is not None

        except Exception as e:
            self.logger.logger.error(f"Erro ao reiniciar servidor: {e}")
            return False