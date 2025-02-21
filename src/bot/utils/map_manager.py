"""
Map Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:20:18
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import asyncio
import aiofiles
import os

class MapStatus(Enum):
    AVAILABLE = "available"
    PICKED = "picked"
    BANNED = "banned"
    DECIDER = "decider"

@dataclass
class MapInfo:
    name: str           # Nome do mapa (de_mirage)
    display_name: str   # Nome de exibição (Mirage)
    image_path: str     # Caminho para imagem do mapa
    overview_path: str  # Caminho para overview do mapa
    status: MapStatus = MapStatus.AVAILABLE
    picked_by: Optional[str] = None
    banned_by: Optional[str] = None
    side_picked: Optional[str] = None  # CT ou T

class MapManager:
    def __init__(self):
        """Inicializar Map Manager"""
        self._maps_dir = Path('/opt/cs2server/maps')
        self._images_dir = Path('/opt/cs2server/images/maps')
        self._cache_dir = Path('/tmp/map_images')
        self._font_path = '/opt/cs2server/fonts/cs2.ttf'
        
        # Criar diretórios necessários
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapas competitivos (5v5)
        self._maps: Dict[str, MapInfo] = {
            'de_mirage': MapInfo(
                name='de_mirage',
                display_name='Mirage',
                image_path=str(self._images_dir / 'mirage.jpg'),
                overview_path=str(self._images_dir / 'mirage_overview.jpg')
            ),
            'de_inferno': MapInfo(
                name='de_inferno',
                display_name='Inferno',
                image_path=str(self._images_dir / 'inferno.jpg'),
                overview_path=str(self._images_dir / 'inferno_overview.jpg')
            ),
            'de_overpass': MapInfo(
                name='de_overpass',
                display_name='Overpass',
                image_path=str(self._images_dir / 'overpass.jpg'),
                overview_path=str(self._images_dir / 'overpass_overview.jpg')
            ),
            'de_vertigo': MapInfo(
                name='de_vertigo',
                display_name='Vertigo',
                image_path=str(self._images_dir / 'vertigo.jpg'),
                overview_path=str(self._images_dir / 'vertigo_overview.jpg')
            ),
            'de_ancient': MapInfo(
                name='de_ancient',
                display_name='Ancient',
                image_path=str(self._images_dir / 'ancient.jpg'),
                overview_path=str(self._images_dir / 'ancient_overview.jpg')
            ),
            'de_nuke': MapInfo(
                name='de_nuke',
                display_name='Nuke',
                image_path=str(self._images_dir / 'nuke.jpg'),
                overview_path=str(self._images_dir / 'nuke_overview.jpg')
            ),
            'de_anubis': MapInfo(
                name='de_anubis',
                display_name='Anubis',
                image_path=str(self._images_dir / 'anubis.jpg'),
                overview_path=str(self._images_dir / 'anubis_overview.jpg')
            )
        }
        
        # Mapas Wingman (2v2)
        self._wingman_maps: Dict[str, MapInfo] = {
            'de_shortdust': MapInfo(
                name='de_shortdust',
                display_name='Short Dust',
                image_path=str(self._images_dir / 'shortdust.jpg'),
                overview_path=str(self._images_dir / 'shortdust_overview.jpg')
            ),
            'de_shortnuke': MapInfo(
                name='de_shortnuke',
                display_name='Short Nuke',
                image_path=str(self._images_dir / 'shortnuke.jpg'),
                overview_path=str(self._images_dir / 'shortnuke_overview.jpg')
            ),
            'de_shortvertigo': MapInfo(
                name='de_shortvertigo',
                display_name='Short Vertigo',
                image_path=str(self._images_dir / 'shortvertigo.jpg'),
                overview_path=str(self._images_dir / 'shortvertigo_overview.jpg')
            ),
            'de_lake': MapInfo(
                name='de_lake',
                display_name='Lake',
                image_path=str(self._images_dir / 'lake.jpg'),
                overview_path=str(self._images_dir / 'lake_overview.jpg')
            ),
            'de_chalice': MapInfo(
                name='de_chalice',
                display_name='Chalice',
                image_path=str(self._images_dir / 'chalice.jpg'),
                overview_path=str(self._images_dir / 'chalice_overview.jpg')
            )
        }

    async def generate_veto_image(self, 
                                map_name: str, 
                                status: MapStatus,
                                team1_name: Optional[str] = None,
                                team2_name: Optional[str] = None) -> str:
        """
        Gerar imagem para veto de mapa
        
        Args:
            map_name: Nome do mapa
            status: Status atual do mapa
            team1_name: Nome do time 1 (se picked/banned)
            team2_name: Nome do time 2 (se picked/banned)
            
        Returns:
            Caminho para imagem gerada
        """
        try:
            map_info = self._maps.get(map_name) or self._wingman_maps.get(map_name)
            if not map_info:
                return ""
            
            # Carregar imagem base
            with Image.open(map_info.image_path) as img:
                # Redimensionar mantendo proporção
                img = img.copy()
                img.thumbnail((800, 450))
                
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(self._font_path, 36)
                small_font = ImageFont.truetype(self._font_path, 24)
                
                # Aplicar overlay baseado no status
                overlay = Image.new('RGBA', img.size, (0,0,0,0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                if status == MapStatus.BANNED:
                    # Overlay vermelho para banido
                    overlay_draw.rectangle(
                        [(0,0), img.size],
                        fill=(255,0,0,128)
                    )
                    text = "BANNED"
                elif status == MapStatus.PICKED:
                    # Overlay verde para escolhido
                    overlay_draw.rectangle(
                        [(0,0), img.size],
                        fill=(0,255,0,128)
                    )
                    text = "PICKED"
                elif status == MapStatus.DECIDER:
                    # Overlay azul para decider
                    overlay_draw.rectangle(
                        [(0,0), img.size],
                        fill=(0,0,255,128)
                    )
                    text = "DECIDER"
                else:
                    text = "AVAILABLE"
                
                img = Image.alpha_composite(img.convert('RGBA'), overlay)
                
                # Adicionar texto
                draw = ImageDraw.Draw(img)
                
                # Nome do mapa
                draw.text(
                    (img.width/2, 50),
                    map_info.display_name,
                    font=font,
                    fill='white',
                    anchor='mm',
                    stroke_width=2,
                    stroke_fill='black'
                )
                
                # Status
                draw.text(
                    (img.width/2, img.height-50),
                    text,
                    font=font,
                    fill='white',
                    anchor='mm',
                    stroke_width=2,
                    stroke_fill='black'
                )
                
                # Times (se aplicável)
                if team1_name and status in [MapStatus.PICKED, MapStatus.BANNED]:
                    draw.text(
                        (10, img.height-30),
                        team1_name,
                        font=small_font,
                        fill='white',
                        anchor='lm',
                        stroke_width=2,
                        stroke_fill='black'
                    )
                    
                if team2_name and status == MapStatus.PICKED:
                    draw.text(
                        (img.width-10, img.height-30),
                        team2_name,
                        font=small_font,
                        fill='white',
                        anchor='rm',
                        stroke_width=2,
                        stroke_fill='black'
                    )
                
                # Salvar imagem
                output_path = self._cache_dir / f"veto_{map_name}_{status.value}.png"
                img.save(output_path, "PNG")
                return str(output_path)
                
        except Exception as e:
            print(f"Erro ao gerar imagem: {e}")
            return ""