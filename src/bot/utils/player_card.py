"""
Player Card Generator
Author: adamguedesmtm
Created: 2025-02-21 13:56:20
"""

from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple
import aiohttp
import io
import os
from pathlib import Path
from .logger import Logger
from .metrics import MetricsManager

class PlayerCard:
    def __init__(self,
                 assets_dir: str = "/opt/cs2server/assets",
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.assets_dir = Path(assets_dir)
        self.logger = logger or Logger('player_card')
        self.metrics = metrics
        self.fonts = self._load_fonts()
        self.rank_images = self._load_rank_images()
        self.template = self._load_template()

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Carregar fontes necessárias"""
        try:
            fonts_dir = self.assets_dir / 'fonts'
            return {
                'title': ImageFont.truetype(str(fonts_dir / 'title.ttf'), 48),
                'stats': ImageFont.truetype(str(fonts_dir / 'stats.ttf'), 32),
                'details': ImageFont.truetype(str(fonts_dir / 'details.ttf'), 24)
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar fontes: {e}")
            return {}

    def _load_rank_images(self) -> Dict[str, Image.Image]:
        """Carregar imagens dos rankings"""
        try:
            ranks_dir = self.assets_dir / 'ranks'
            ranks = {}
            for rank_file in ranks_dir.glob('*.png'):
                ranks[rank_file.stem] = Image.open(rank_file)
            return ranks
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar ranks: {e}")
            return {}

    def _load_template(self) -> Optional[Image.Image]:
        """Carregar template do card"""
        try:
            template_path = self.assets_dir / 'templates' / 'player_card.png'
            return Image.open(template_path)
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar template: {e}")
            return None

    async def get_player_stats(self, player_id: int) -> Dict:
        """Obter estatísticas do jogador"""
        # Simulação de estatísticas (substituir por integração real)
        return {
            'rank': 'gold_nova_master',
            'matches': 150,
            'wins': 89,
            'losses': 61,
            'draws': 0,
            'winrate': 59.3,
            'rating': 1.15,
            'kd_ratio': 1.23,
            'headshot_percent': 48.7,
            'accuracy': 22.4,
            'most_played_maps': [
                ('de_mirage', 45),
                ('de_inferno', 38),
                ('de_dust2', 34)
            ]
        }

    async def generate(self, player_id: int, player_name: str, avatar_url: Optional[str] = None) -> Optional[io.BytesIO]:
        """Gerar card do jogador"""
        try:
            # Obter estatísticas
            stats = await self.get_player_stats(player_id)
            
            if not self.template:
                raise Exception("Template não carregado")

            # Criar nova imagem
            card = self.template.copy()
            draw = ImageDraw.Draw(card)

            # Adicionar avatar se disponível
            if avatar_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(avatar_url) as response:
                            if response.status == 200:
                                avatar_data = await response.read()
                                avatar = Image.open(io.BytesIO(avatar_data))
                                avatar = avatar.resize((128, 128))
                                card.paste(avatar, (50, 50))
                except Exception as e:
                    self.logger.logger.error(f"Erro ao carregar avatar: {e}")

            # Adicionar nome e rank
            draw.text((200, 50), player_name, font=self.fonts['title'])
            rank_img = self.rank_images.get(stats['rank'])
            if rank_img:
                card.paste(rank_img, (200, 120), rank_img)

            # Adicionar estatísticas principais
            stats_y = 250
            draw.text((50, stats_y), f"Partidas: {stats['matches']}", font=self.fonts['stats'])
            draw.text((50, stats_y + 40), f"Vitórias: {stats['wins']}", font=self.fonts['stats'])
            draw.text((50, stats_y + 80), f"Winrate: {stats['winrate']}%", font=self.fonts['stats'])
            
            draw.text((300, stats_y), f"Rating: {stats['rating']}", font=self.fonts['stats'])
            draw.text((300, stats_y + 40), f"K/D: {stats['kd_ratio']}", font=self.fonts['stats'])
            draw.text((300, stats_y + 80), f"HS%: {stats['headshot_percent']}%", font=self.fonts['stats'])

            # Adicionar mapas mais jogados
            maps_y = 400
            draw.text((50, maps_y), "Mapas mais jogados:", font=self.fonts['stats'])
            for i, (map_name, count) in enumerate(stats['most_played_maps']):
                draw.text(
                    (50, maps_y + 40 + (i * 30)),
                    f"{map_name}: {count} partidas",
                    font=self.fonts['details']
                )

            # Salvar imagem
            output = io.BytesIO()
            card.save(output, format='PNG')
            output.seek(0)

            if self.metrics:
                await self.metrics.record_command('player_card_generated')

            return output

        except Exception as e:
            self.logger.logger.error(f"Erro ao gerar player card: {e}")
            return None

    async def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Obter top jogadores"""
        # Simulação (substituir por integração real)
        return [
            {
                'name': f'Player{i}',
                'rating': round(2.0 - (i * 0.1), 2),
                'kd': round(1.5 - (i * 0.05), 2),
                'hs_percent': 50 - i
            }
            for i in range(limit)
        ]

    async def get_recent_matches(self, player_id: int, limit: int = 5) -> List[Dict]:
        """Obter partidas recentes do jogador"""
        # Simulação (substituir por integração real)
        maps = ['de_dust2', 'de_mirage', 'de_inferno', 'de_overpass', 'de_ancient']
        return [
            {
                'map': maps[i % len(maps)],
                'won': i % 2 == 0,
                'team_score': 16 if i % 2 == 0 else 13,
                'enemy_score': 13 if i % 2 == 0 else 16,
                'kills': 20 + i,
                'deaths': 15 + i,
                'assists': 5 + i,
                'rating': round(1.2 - (i * 0.1), 2)
            }
            for i in range(limit)
        ]