"""
Player Card Generator
Author: adamguedesmtm
Created: 2025-02-21 15:46:19
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Carregar fontes necessárias"""
        try:
            fonts_dir = self.assets_dir / 'fonts'
            return {
                'title': ImageFont.truetype(str(fonts_dir / 'title.ttf'), 48),
                'stats': ImageFont.truetype(str(fonts_dir / 'stats.ttf'), 32),
                'details': ImageFont.truetype(str(fonts_dir / 'details.ttf'), 24),
                'elo': ImageFont.truetype(str(fonts_dir / 'elo.ttf'), 64)  # Nova fonte para ELO
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

    async def get_steam_profile_background(self, steam_id: str) -> Optional[Image.Image]:
        """Buscar imagem de fundo do perfil Steam"""
        try:
            async with aiohttp.ClientSession() as session:
                # Primeiro, buscar o perfil Steam para obter a URL da imagem
                profile_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={os.getenv('STEAM_API_KEY')}&steamids={steam_id}"
                async with session.get(profile_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if players := data.get('response', {}).get('players', []):
                            player = players[0]
                            # Tentar pegar a imagem de perfil em alta resolução
                            bg_url = player.get('profilebackground', '')
                            if bg_url:
                                async with session.get(bg_url) as img_response:
                                    if img_response.status == 200:
                                        img_data = await img_response.read()
                                        return Image.open(io.BytesIO(img_data))
        except Exception as e:
            self.logger.logger.error(f"Erro ao buscar fundo do Steam: {e}")
        return None

    def create_background(self, width: int, height: int, steam_bg: Optional[Image.Image] = None) -> Image.Image:
        """Criar fundo do card"""
        if steam_bg:
            # Redimensionar e aplicar blur na imagem do Steam
            bg = steam_bg.resize((width, height), Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=5))
            
            # Adicionar overlay escuro para melhor legibilidade
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 128))
            bg = Image.alpha_composite(bg.convert('RGBA'), overlay)
        else:
            # Criar gradiente como fallback
            bg = Image.new('RGBA', (width, height), (32, 32, 32, 255))
            gradient = Image.new('RGBA', (width, height))
            draw = ImageDraw.Draw(gradient)
            for y in range(height):
                alpha = int(255 * (1 - y/height))
                draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
            bg = Image.alpha_composite(bg, gradient)
        
        return bg

    async def generate(self, player_id: int, player_name: str, steam_id: str, avatar_url: Optional[str] = None) -> Optional[io.BytesIO]:
        """Gerar card do jogador"""
        try:
            # Obter estatísticas
            stats = await self.get_player_stats(player_id)
            
            # Dimensões do card
            width, height = 800, 600
            
            # Obter fundo do Steam
            steam_bg = await self.get_steam_profile_background(steam_id)
            background = self.create_background(width, height, steam_bg)
            
            # Criar nova imagem
            card = Image.new('RGBA', (width, height))
            card.paste(background, (0, 0))
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
                                
                                # Criar máscara circular
                                mask = Image.new('L', (128, 128), 0)
                                mask_draw = ImageDraw.Draw(mask)
                                mask_draw.ellipse((0, 0, 128, 128), fill=255)
                                
                                # Aplicar máscara
                                output = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
                                output.paste(avatar, (0, 0))
                                output.putalpha(mask)
                                
                                card.paste(output, (50, 50), output)
                except Exception as e:
                    self.logger.logger.error(f"Erro ao carregar avatar: {e}")

            # Adicionar nome e ELO
            draw.text((200, 50), player_name, font=self.fonts['title'], fill=(255, 255, 255))
            
            # Destacar o ELO
            elo_text = f"{int(stats['rating'])}"
            elo_w, elo_h = draw.textsize(elo_text, font=self.fonts['elo'])
            elo_x = width - elo_w - 50
            elo_y = 50
            
            # Adicionar glow ao ELO
            for offset in range(3, 0, -1):
                draw.text(
                    (elo_x-offset, elo_y-offset), 
                    elo_text, 
                    font=self.fonts['elo'], 
                    fill=(255, 215, 0, 64)
                )
            draw.text(
                (elo_x, elo_y), 
                elo_text, 
                font=self.fonts['elo'], 
                fill=(255, 215, 0)
            )

            # Adicionar estatísticas principais
            stats_y = 250
            stats_color = (255, 255, 255)
            draw.text((50, stats_y), f"Partidas: {stats['matches']}", font=self.fonts['stats'], fill=stats_color)
            draw.text((50, stats_y + 40), f"Vitórias: {stats['wins']}", font=self.fonts['stats'], fill=stats_color)
            draw.text((50, stats_y + 80), f"Winrate: {stats['winrate']}%", font=self.fonts['stats'], fill=stats_color)
            
            draw.text((300, stats_y), f"Rating: {stats['rating']:.2f}", font=self.fonts['stats'], fill=stats_color)
            draw.text((300, stats_y + 40), f"K/D: {stats['kd_ratio']}", font=self.fonts['stats'], fill=stats_color)
            draw.text((300, stats_y + 80), f"HS%: {stats['headshot_percent']}%", font=self.fonts['stats'], fill=stats_color)

            # Adicionar mapas mais jogados
            maps_y = 400
            draw.text((50, maps_y), "Mapas mais jogados:", font=self.fonts['stats'], fill=stats_color)
            for i, (map_name, count) in enumerate(stats['most_played_maps']):
                draw.text(
                    (50, maps_y + 40 + (i * 30)),
                    f"{map_name}: {count} partidas",
                    font=self.fonts['details'],
                    fill=stats_color
                )

            # Adicionar ranks (medalhas)
            if rank_img := self.rank_images.get(stats['rank']):
                rank_size = (64, 64)
                rank_img = rank_img.resize(rank_size)
                card.paste(rank_img, (width - rank_size[0] - 50, height - rank_size[1] - 50), rank_img)

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

    # ... (resto dos métodos permanece igual)