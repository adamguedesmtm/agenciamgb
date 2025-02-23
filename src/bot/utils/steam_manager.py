"""
Steam Manager
Author: adamguedesmtm
Created: 2025-02-21 15:51:33
"""

import aiohttp
from typing import Dict, Optional
from .logger import Logger

class SteamManager:
    def __init__(self, api_key: str, logger: Optional[Logger] = None):
        self.api_key = api_key
        self.logger = logger or Logger('steam_manager')
        self.cache = {}  # Cache para minimizar chamadas à API

    async def get_community_profile(self, steam_id: str) -> Optional[Dict]:
        """Buscar perfil público do jogador no Steam."""
        try:
            summary = await self.get_player_summary(steam_id)
            if not summary:
                return None

            profile_url = summary.get("profile_url", "")
            async with aiohttp.ClientSession() as session:
                async with session.get(profile_url) as response:
                    if response.status == 200:
                        return await response.json()

        except Exception as e:
            self.logger.logger.error(f"Erro ao buscar perfil Steam: {e}")
        return None

    async def get_player_summary(self, steam_id: str) -> Optional[Dict]:
        """Buscar informações do jogador na Steam"""
        try:
            if steam_id in self.cache:
                return self.cache[steam_id]
                
            async with aiohttp.ClientSession() as session:
                url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
                params = {
                    "key": self.api_key,
                    "steamids": steam_id
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if players := data.get('response', {}).get('players', []):
                            player = players[0]
                            self.cache[steam_id] = {
                                'name': player.get('personaname'),
                                'avatar': player.get('avatarfull'),
                                'profile_url': player.get('profileurl'),
                                'background': player.get('profilebackground', ''),
                                'state': player.get('personastate'),
                                'visibility': player.get('communityvisibilitystate')
                            }
                            return self.cache[steam_id]
                            
        except Exception as e:
            self.logger.logger.error(f"Erro ao buscar dados Steam: {e}")
        return None
    
    def get_player_name(self, steam_id: str) -> str:
        """Retorna nome do jogador (cache)"""
        return self.cache.get(steam_id, {}).get('name', f"Player_{steam_id[-4:]}")
    
    def get_player_avatar(self, steam_id: str) -> str:
        """Retorna URL do avatar (cache)"""
        return self.cache.get(steam_id, {}).get('avatar', '')
    
    def get_player_background(self, steam_id: str) -> str:
        """Retorna URL do background (cache)"""
        return self.cache.get(steam_id, {}).get('background', '')
    
    async def clear_cache(self, steam_id: Optional[str] = None):
        """Limpar cache de um jogador ou todo o cache"""
        if steam_id:
            self.cache.pop(steam_id, None)
        else:
            self.cache.clear()