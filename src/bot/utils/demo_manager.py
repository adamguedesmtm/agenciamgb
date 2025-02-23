"""
CS Demo Manager Integration
Author: adamguedesmtm
Created: 2025-02-21 14:00:38
"""

import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import json
from datetime import datetime
from .logger import Logger
from .metrics import MetricsManager
from .stats_manager import StatsManager

class DemoManager:
    def __init__(self,
                 demos_dir: str = "/opt/cs2server/demos",
                 parser_path: str = "/opt/csdm/parser",
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None,
                 stats_manager: Optional[StatsManager] = None):
        self.demos_dir = Path(demos_dir)
        self.parser_path = Path(parser_path)
        self.logger = logger or Logger('demo_manager')
        self.metrics = metrics
        self.stats_manager = stats_manager
        self.processing_queue = asyncio.Queue()
        self.is_processing = False

    async def start_processor(self):
        """Iniciar processador de demos em background"""
        self.is_processing = True
        while self.is_processing:
            try:
                demo_path = await self.processing_queue.get()
                await self._process_demo(demo_path)
                self.processing_queue.task_done()
            except Exception as e:
                self.logger.logger.error(f"Erro no processador de demos: {e}")
                await asyncio.sleep(5)  # Esperar antes de tentar novamente

    async def stop_processor(self):
        """Parar processador de demos"""
        self.is_processing = False
        while not self.processing_queue.empty():
            await self.processing_queue.get()
            self.processing_queue.task_done()

    async def queue_demo(self, match_id: str, demo_path: Path):
        """Adicionar demo à fila de processamento"""
        try:
            if not demo_path.exists():
                raise FileNotFoundError(f"Demo não encontrada: {demo_path}")

            # Mover demo para diretório de processamento
            new_path = self.demos_dir / f"{match_id}_{demo_path.name}"
            demo_path.rename(new_path)

            # Adicionar à fila
            await self.processing_queue.put(new_path)

            if self.metrics:
                await self.metrics.record_command('demo_queued')

            self.logger.logger.info(f"Demo {match_id} adicionada à fila")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao enfileirar demo: {e}")
            return False

    async def _process_demo(self, demo_path: Path):
        """Processar demo usando CS Demo Manager GUI."""
        try:
            match_id = demo_path.stem.split('_')[0]

            # Executar GUI em segundo plano
            process = await asyncio.create_subprocess_shell(
                f"xvfb-run ./csgo-demoui -demo {demo_path} -json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Erro ao processar demo: {stderr.decode()}")

            # Parsear resultado
            demo_data = json.loads(stdout.decode())
            match_stats = await self._extract_match_stats(demo_data)

            # Atualizar banco de dados
            if self.stats_manager:
                await self.stats_manager.update_match_stats(match_id, match_stats)

            # Mover demo para pasta processed
            processed_dir = self.demos_dir / 'processed'
            processed_dir.mkdir(exist_ok=True)
            demo_path.rename(processed_dir / demo_path.name)

            self.logger.logger.info(f"Demo {match_id} processada com sucesso")
        except Exception as e:
            self.logger.logger.error(f"Erro ao processar demo {match_id}: {e}")


    async def _extract_match_stats(self, demo_data: Dict) -> Dict:
        """Extrair estatísticas detalhadas da demo"""
        try:
            stats = {
                'general': {
                    'map': demo_data['map'],
                    'duration': demo_data['duration'],
                    'rounds_played': len(demo_data['rounds']),
                    'score_team1': demo_data['team1_score'],
                    'score_team2': demo_data['team2_score'],
                    'winner': 'team1' if demo_data['team1_score'] > demo_data['team2_score'] else 'team2'
                },
                'players': {}
            }

            # Processar estatísticas por jogador
            for player_data in demo_data['players']:
                steam_id = player_data['steam_id']
                stats['players'][steam_id] = {
                    'team': player_data['team'],
                    'name': player_data['name'],
                    'kills': player_data['kills'],
                    'deaths': player_data['deaths'],
                    'assists': player_data['assists'],
                    'kd_ratio': player_data['kd_ratio'],
                    'hs_kills': player_data['hs_kills'],
                    'hs_ratio': player_data['hs_ratio'],
                    'entry_kills': player_data['entry_kills'],
                    'clutches_won': player_data['clutches_won'],
                    'damage_dealt': player_data['damage_dealt'],
                    'utility_damage': player_data['utility_damage'],
                    'flash_assists': player_data['flash_assists'],
                    'enemies_flashed': player_data['enemies_flashed'],
                    'mvps': player_data['mvps'],
                    'score': player_data['score'],
                    'rounds': {
                        'played': player_data['rounds_played'],
                        'survived': player_data['rounds_survived'],
                        'with_kills': player_data['rounds_with_kills'],
                        'with_damage': player_data['rounds_with_damage'],
                        'trade_kills': player_data['trade_kills']
                    },
                    'weapons': {
                        'kills_by_weapon': player_data['kills_by_weapon'],
                        'favorite_weapon': player_data['favorite_weapon']
                    }
                }

            # Calcular estatísticas extras
            stats['rounds'] = await self._analyze_rounds(demo_data['rounds'])
            stats['economy'] = await self._analyze_economy(demo_data['rounds'])
            stats['positions'] = await self._analyze_positions(demo_data['positions'])

            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao extrair stats da demo: {e}")
            return {}

    async def _analyze_rounds(self, rounds: List[Dict]) -> Dict:
        """Analisar detalhes das rounds"""
        try:
            analysis = {
                'pistol_rounds': {'ct_wins': 0, 't_wins': 0},
                'force_buy_rounds': {'ct_wins': 0, 't_wins': 0},
                'eco_rounds': {'ct_wins': 0, 't_wins': 0},
                'retakes': {'attempts': 0, 'successful': 0},
                'average_round_time': 0,
                'round_win_reasons': {}
            }

            total_time = 0
            for round_data in rounds:
                # Analisar tipo de round
                if round_data['round_number'] in (1, 16):  # Pistol rounds
                    if round_data['winner'] == 'CT':
                        analysis['pistol_rounds']['ct_wins'] += 1
                    else:
                        analysis['pistol_rounds']['t_wins'] += 1

                # Analisar compras
                if round_data['is_force_buy']:
                    if round_data['winner'] == 'CT':
                        analysis['force_buy_rounds']['ct_wins'] += 1
                    else:
                        analysis['force_buy_rounds']['t_wins'] += 1
                elif round_data['is_eco']:
                    if round_data['winner'] == 'CT':
                        analysis['eco_rounds']['ct_wins'] += 1
                    else:
                        analysis['eco_rounds']['t_wins'] += 1

                # Analisar retakes
                if round_data['bomb_planted']:
                    analysis['retakes']['attempts'] += 1
                    if round_data['winner'] == 'CT':
                        analysis['retakes']['successful'] += 1

                # Tempo da round
                total_time += round_data['duration']

                # Razão da vitória
                reason = round_data['win_reason']
                analysis['round_win_reasons'][reason] = \
                    analysis['round_win_reasons'].get(reason, 0) + 1

            # Calcular média
            analysis['average_round_time'] = total_time / len(rounds)

            return analysis

        except Exception as e:
            self.logger.logger.error(f"Erro ao analisar rounds: {e}")
            return {}

    async def _analyze_economy(self, rounds: List[Dict]) -> Dict:
        """Analisar economia da partida"""
        try:
            analysis = {
                'average_team_value': {'CT': 0, 'T': 0},
                'max_team_value': {'CT': 0, 'T': 0},
                'eco_success_rate': {'CT': 0, 'T': 0},
                'force_buy_success_rate': {'CT': 0, 'T': 0},
                'equipment_value_distribution': {
                    'low': 0,    # < $10000
                    'medium': 0, # $10000-$20000
                    'high': 0    # > $20000
                }
            }

            eco_rounds = {'CT': {'total': 0, 'won': 0}, 'T': {'total': 0, 'won': 0}}
            force_rounds = {'CT': {'total': 0, 'won': 0}, 'T': {'total': 0, 'won': 0}}

            for round_data in rounds:
                # Análise por time
                for team in ['CT', 'T']:
                    team_value = round_data[f'{team.lower()}_equipment_value']
                    
                    # Atualizar médias e máximos
                    analysis['average_team_value'][team] += team_value
                    analysis['max_team_value'][team] = max(
                        analysis['max_team_value'][team],
                        team_value
                    )

                    # Classificar valor do equipamento
                    if team_value < 10000:
                        analysis['equipment_value_distribution']['low'] += 1
                    elif team_value < 20000:
                        analysis['equipment_value_distribution']['medium'] += 1
                    else:
                        analysis['equipment_value_distribution']['high'] += 1

                    # Análise de ecos e force buys
                    if round_data[f'is_{team.lower()}_eco']:
                        eco_rounds[team]['total'] += 1
                        if round_data['winner'] == team:
                            eco_rounds[team]['won'] += 1
                    elif round_data[f'is_{team.lower()}_force']:
                        force_rounds[team]['total'] += 1
                        if round_data['winner'] == team:
                            force_rounds[team]['won'] += 1

            # Calcular médias finais
            for team in ['CT', 'T']:
                analysis['average_team_value'][team] /= len(rounds)
                if eco_rounds[team]['total'] > 0:
                    analysis['eco_success_rate'][team] = \
                        eco_rounds[team]['won'] / eco_rounds[team]['total']
                if force_rounds[team]['total'] > 0:
                    analysis['force_buy_success_rate'][team] = \
                        force_rounds[team]['won'] / force_rounds[team]['total']

            return analysis

        except Exception as e:
            self.logger.logger.error(f"Erro ao analisar economia: {e}")
            return {}

    async def _analyze_positions(self, positions: Dict) -> Dict:
        """Analisar posições e movimentação"""
        try:
            analysis = {
                'heatmaps': {
                    'kills': {},
                    'deaths': {},
                    'bomb_plants': {},
                    'grenades': {}
                },
                'common_angles': {
                    'CT': [],
                    'T': []
                },
                'entry_paths': {
                    'successful': [],
                    'failed': []
                }
            }

            # Processar posições de kills
            for kill in positions['kills']:
                pos = (kill['x'], kill['y'])
                analysis['heatmaps']['kills'][pos] = \
                    analysis['heatmaps']['kills'].get(pos, 0) + 1

                # Registrar ângulos comuns
                if kill['attacker_team'] == 'CT':
                    analysis['common_angles']['CT'].append(kill['attacker_angle'])
                else:
                    analysis['common_angles']['T'].append(kill['attacker_angle'])

                # Analisar entry paths
                if kill['is_entry']:
                    path = kill['attacker_path']
                    if kill['attacker_team'] == kill['winner_team']:
                        analysis['entry_paths']['successful'].append(path)
                    else:
                        analysis['entry_paths']['failed'].append(path)

            # Processar posições de plantas
            for plant in positions['bomb_plants']:
                pos = (plant['x'], plant['y'])
                analysis['heatmaps']['bomb_plants'][pos] = \
                    analysis['heatmaps']['bomb_plants'].get(pos, 0) + 1

            # Processar uso de granadas
            for nade in positions['grenades']:
                pos = (nade['x'], nade['y'])
                analysis['heatmaps']['grenades'][pos] = \
                    analysis['heatmaps']['grenades'].get(pos, 0) + 1

            return analysis

        except Exception as e:
            self.logger.logger.error(f"Erro ao analisar posições: {e}")
            return {}