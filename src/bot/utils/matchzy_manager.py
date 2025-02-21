"""
Matchzy API Manager
Author: adamguedesmtm
Created: 2025-02-21 13:53:21
"""

import aiohttp
import json
from typing import Dict, List, Optional
from .logger import Logger
from .metrics import MetricsManager
from .rcon_manager import RCONManager

class MatchzyManager:
    def __init__(self, 
                 rcon: RCONManager,
                 api_url: str,
                 api_key: str,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.rcon = rcon
        self.api_url = api_url
        self.api_key = api_key
        self.logger = logger or Logger('matchzy_manager')
        self.metrics = metrics
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    async def create_match(self, players: List[Dict]) -> Optional[str]:
        """Criar nova partida"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'players': [
                        {
                            'steam_id': player['id'],
                            'name': player['name'],
                            'team': 'none'  # Equipes serão definidas pelo matchzy
                        } for player in players
                    ],
                    'map_pool': ['de_dust2', 'de_mirage', 'de_inferno', 
                                'de_overpass', 'de_ancient', 'de_anubis'],
                    'team_size': 5,
                    'series_type': 'bo1'
                }

                async with session.post(
                    f'{self.api_url}/matches/create',
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        match_id = data['match_id']
                        
                        if self.metrics:
                            await self.metrics.record_match_start('competitive')
                            
                        return match_id
                    return None

        except Exception as e:
            self.logger.logger.error(f"Erro ao criar partida: {e}")
            return None

    async def get_match_info(self, match_id: str) -> Optional[Dict]:
        """Obter informações da partida"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.api_url}/matches/{match_id}',
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da partida: {e}")
            return None

    async def update_match_status(self, match_id: str, status: str) -> bool:
        """Atualizar status da partida"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f'{self.api_url}/matches/{match_id}/status',
                    headers=self.headers,
                    json={'status': status}
                ) as response:
                    return response.status == 200

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar status: {e}")
            return False

    async def end_match(self, match_id: str, winner: str) -> bool:
        """Finalizar partida"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f'{self.api_url}/matches/{match_id}/end',
                    headers=self.headers,
                    json={'winner': winner}
                ) as response:
                    success = response.status == 200
                    
                    if success and self.metrics:
                        await self.metrics.record_match_duration('competitive')
                        
                    return success

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
            # Avisar jogadores
            await self.rcon.send_message("Servidor será reiniciado em 10 segundos!")
            await asyncio.sleep(10)
            
            # Reiniciar
            return await self.rcon.execute("_restart") is not None

        except Exception as e:
            self.logger.logger.error(f"Erro ao reiniciar servidor: {e}")
            return False