"""
Map Manager
Author: adamguedesmtm
Created: 2025-02-21 13:51:45
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import random
from .logger import Logger
from .metrics import MetricsManager

class MapManager:
    def __init__(self, 
                 maps_dir: str = "/opt/cs2server/maps",
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.maps_dir = Path(maps_dir)
        self.logger = logger or Logger('map_manager')
        self.metrics = metrics
        self.map_cache: Dict[str, Dict] = {}
        self.map_history: List[str] = []
        self.max_history = 5

    async def load_maps(self) -> Dict[str, List[str]]:
        """Carregar mapas disponíveis"""
        try:
            maps = {
                'competitive': [],
                'wingman': [],
                'retake': []
            }
            
            # Verificar mapas instalados
            for map_file in self.maps_dir.glob('*.bsp'):
                map_name = map_file.stem
                map_info = await self._get_map_info(map_name)
                
                if map_info:
                    if map_info['type'] == 'competitive':
                        maps['competitive'].append(map_name)
                    elif map_info['type'] == 'wingman':
                        maps['wingman'].append(map_name)
                    
                    # Mapas competitivos também podem ser usados para retake
                    if map_info['type'] == 'competitive':
                        maps['retake'].append(map_name)
                        
            if self.metrics:
                for mode, map_list in maps.items():
                    await self.metrics.record_command(
                        f'maps_loaded_{mode}',
                        len(map_list)
                    )
                    
            return maps
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar mapas: {e}")
            return {'competitive': [], 'wingman': [], 'retake': []}

    async def _get_map_info(self, map_name: str) -> Optional[Dict]:
        """Obter informações do mapa"""
        try:
            # Verificar cache primeiro
            if map_name in self.map_cache:
                return self.map_cache[map_name]
                
            # Mapa competitivo padrão
            if map_name.startswith('de_'):
                info = {
                    'name': map_name,
                    'type': 'competitive',
                    'min_players': 10,
                    'max_players': 10
                }
                
                # Mapas específicos para wingman
                if map_name in ['de_lake', 'de_shortdust', 'de_vertigo']:
                    info.update({
                        'type': 'wingman',
                        'min_players': 4,
                        'max_players': 4
                    })
                    
                self.map_cache[map_name] = info
                return info
                
            return None
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info do mapa: {e}")
            return None

    async def get_next_map(self, mode: str, exclude: List[str] = None) -> Optional[str]:
        """Obter próximo mapa para rotação"""
        try:
            maps = await self.load_maps()
            available_maps = maps.get(mode, [])
            
            if not available_maps:
                return None
                
            # Filtrar mapas excluídos e recentes
            exclude = exclude or []
            candidates = [
                m for m in available_maps
                if m not in exclude and m not in self.map_history
            ]
            
            if not candidates:
                # Se não há candidatos, limpar histórico e tentar novamente
                self.map_history.clear()
                candidates = [m for m in available_maps if m not in exclude]
                
            if candidates:
                next_map = random.choice(candidates)
                
                # Atualizar histórico
                self.map_history.append(next_map)
                if len(self.map_history) > self.max_history:
                    self.map_history.pop(0)
                    
                if self.metrics:
                    await self.metrics.record_command('map_rotation')
                    
                return next_map
                
            return None
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter próximo mapa: {e}")
            return None

    async def get_map_config(self, map_name: str) -> Dict:
        """Obter configurações do mapa"""
        try:
            # Configurações padrão
            config = {
                'warmup_time': 60,
                'round_time': 115,
                'freeze_time': 15,
                'buy_time': 20,
                'c4_timer': 40
            }
            
            # Ajustar configurações específicas
            map_info = await self._get_map_info(map_name)
            if map_info:
                if map_info['type'] == 'wingman':
                    config.update({
                        'warmup_time': 30,
                        'round_time': 90,
                        'freeze_time': 10,
                        'buy_time': 15,
                        'c4_timer': 35
                    })
                    
            return config
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter config do mapa: {e}")
            return {}