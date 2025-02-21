"""
Player Card System for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:26:06
"""

from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import aiofiles
import os
from pathlib import Path
from .metrics import MetricsManager
from .logger import Logger

class PlayerCard:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('player_card')
        self.metrics = metrics_manager
        
        # Diretórios
        self._assets_dir = Path('/opt/cs2server/assets')
        self._cache_dir = Path('/tmp/player_cards')
        self._font_path = str(self._assets_dir / 'fonts/cs2.ttf')
        
        # Criar diretórios
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Templates
        self._card_bg = str(self._assets_dir / 'templates/card_bg.png')
        self._rank_icons = {
            'silver1': str(self._assets_dir / 'ranks/silver1.png'),
            'silver2': str(self._assets_dir / 'ranks/silver2.png'),
            'silver3': str(self._assets_dir / 'ranks/silver3.png'),
            'silver4': str(self._assets_dir / 'ranks/silver4.png'),
            'silver_elite': str(self._assets_dir / 'ranks/silver_elite.png'),
            'silver_elite_master': str(self._assets_dir / 'ranks/silver_elite_master.png'),
            'gold1': str(self._assets_dir / 'ranks/gold1.png'),
            'gold2': str(self._assets_dir / 'ranks/gold2.png'),
            'gold3': str(self._assets_dir / 'ranks/gold3.png'),
            'gold_nova_master': str(self._assets_dir / 'ranks/gold_nova_master.png'),
            'mg1': str(self._assets_dir / 'ranks/mg1.png'),
            'mg2': str(self._assets_dir / 'ranks/mg2.png'),
            'mge': str(self._assets_dir / 'ranks/mge.png'),
            'dmg': str(self._assets_dir / 'ranks/dmg.png'),
            'le': str(self._assets_dir / 'ranks/le.png'),
            'lem': str(self._assets_dir / 'ranks/lem.png'),
            'supreme': str(self._assets_dir / 'ranks/supreme.png'),
            'global': str(self._assets_dir / 'ranks/global.png')
        }
        
    async def generate_card(self,
                          player_id: str,
                          player_stats: Dict) -> Optional[str]:
        """
        Gerar card do jogador
        
        Args:
            player_id: ID do jogador
            player_stats: Estatísticas do jogador
                {
                    'name': str,
                    'rank': str,
                    'matches': int,
                    'wins': int,
                    'kills': int,
                    'deaths': int,
                    'assists': int,
                    'headshots': int,
                    'mvps': int,
                    'hours_played': int
                }
                
        Returns:
            Caminho para imagem gerada ou None se erro
        """
        try:
            # Carregar template
            card = Image.open(self._card_bg).convert('RGBA')
            draw = ImageDraw.Draw(card)
            
            # Fontes
            title_font = ImageFont.truetype(self._font_path, 48)
            stats_font = ImageFont.truetype(self._font_path, 32)
            small_font = ImageFont.truetype(self._font_path, 24)
            
            # Nome do jogador
            draw.text(
                (400, 50),
                player_stats['name'],
                font=title_font,
                fill='white',
                anchor='mm'
            )
            
            # Rank (se disponível)
            if player_stats.get('rank') in self._rank_icons:
                rank_icon = Image.open(
                    self._rank_icons[player_stats['rank']]
                ).convert('RGBA')
                rank_icon.thumbnail((100, 100))
                card.paste(
                    rank_icon,
                    (50, 30),
                    rank_icon
                )
                
            # Stats principais
            stats_y = 150
            stats = [
                f"Partidas: {player_stats['matches']}",
                f"Vitórias: {player_stats['wins']}",
                f"K/D: {player_stats['kills']}/{player_stats['deaths']}",
                f"Assistências: {player_stats['assists']}",
                f"Headshots: {player_stats['headshots']}",
                f"MVPs: {player_stats['mvps']}"
            ]
            
            for stat in stats:
                draw.text(
                    (400, stats_y),
                    stat,
                    font=stats_font,
                    fill='white',
                    anchor='mm'
                )
                stats_y += 40
                
            # Horas jogadas
            draw.text(
                (400, 400),
                f"Horas jogadas: {player_stats['hours_played']}",
                font=small_font,
                fill='white',
                anchor='mm'
            )
            
            # Calcular win rate
            if player_stats['matches'] > 0:
                win_rate = (player_stats['wins'] / player_stats['matches']) * 100
                draw.text(
                    (400, 440),
                    f"Win Rate: {win_rate:.1f}%",
                    font=small_font,
                    fill='white',
                    anchor='mm'
                )
                
            # Calcular K/D ratio
            if player_stats['deaths'] > 0:
                kd_ratio = player_stats['kills'] / player_stats['deaths']
                draw.text(
                    (400, 480),
                    f"K/D Ratio: {kd_ratio:.2f}",
                    font=small_font,
                    fill='white',
                    anchor='mm'
                )
                
            # Timestamp
            draw.text(
                (750, 480),
                datetime.utcnow().strftime('%Y-%m-%d'),
                font=small_font,
                fill='gray',
                anchor='rm'
            )
            
            # Salvar imagem
            output_path = self._cache_dir / f"card_{player_id}.png"
            card.save(output_path, "PNG")
            
            await self.metrics.record_metric(
                'player_card.generated',
                1,
                {'player_id': player_id}
            )
            
            return str(output_path)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao gerar card: {e}")
            return None
            
    async def clean_cache(self, max_age_hours: int = 24):
        """Limpar cache de cards antigos"""
        try:
            now = datetime.utcnow()
            count = 0
            
            for file in self._cache_dir.glob('*.png'):
                # Verificar idade do arquivo
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                age = now - mtime
                
                if age.total_seconds() > (max_age_hours * 3600):
                    file.unlink()
                    count += 1
                    
            await self.metrics.record_metric(
                'player_card.cache_cleaned',
                count
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar cache: {e}")