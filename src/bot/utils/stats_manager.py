"""
Statistics Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:47:45
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from collections import defaultdict
from .logger import Logger
from .metrics import MetricsManager

class StatsManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('stats_manager')
        self.metrics = metrics_manager
        self._stats = defaultdict(lambda: defaultdict(int))
        self._sessions = {}
        self._player_stats = defaultdict(lambda: defaultdict(int))
        self._map_stats = defaultdict(lambda: defaultdict(int))
        self._weapon_stats = defaultdict(lambda: defaultdict(int))

    async def record_event(self, 
                          event_type: str,
                          data: Dict,
                          timestamp: datetime = None):
        """Registrar evento para estatísticas"""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Registrar estatística básica
            self._stats[event_type]['total'] += 1
            self._stats[event_type]['last_timestamp'] = timestamp

            # Processar baseado no tipo de evento
            if event_type == 'kill':
                await self._process_kill_event(data, timestamp)
            elif event_type == 'round_end':
                await self._process_round_event(data, timestamp)
            elif event_type == 'match_end':
                await self._process_match_event(data, timestamp)
            elif event_type == 'player_connect':
                await self._process_connect_event(data, timestamp)
            elif event_type == 'player_disconnect':
                await self._process_disconnect_event(data, timestamp)

            # Registrar na métrica
            await self.metrics.record_metric(
                f"stats.{event_type}",
                1
            )

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar evento: {e}")

    async def _process_kill_event(self, data: Dict, timestamp: datetime):
        """Processar evento de kill"""
        try:
            killer_id = data.get('killer_id')
            victim_id = data.get('victim_id')
            weapon = data.get('weapon')
            headshot = data.get('headshot', False)

            if killer_id and victim_id:
                # Estatísticas do jogador
                self._player_stats[killer_id]['kills'] += 1
                self._player_stats[victim_id]['deaths'] += 1
                if headshot:
                    self._player_stats[killer_id]['headshots'] += 1

                # Estatísticas da arma
                if weapon:
                    self._weapon_stats[weapon]['kills'] += 1
                    if headshot:
                        self._weapon_stats[weapon]['headshots'] += 1

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar kill: {e}")

    async def _process_round_event(self, data: Dict, timestamp: datetime):
        """Processar evento de round"""
        try:
            winner = data.get('winner')
            map_name = data.get('map')
            round_time = data.get('duration', 0)

            if map_name:
                self._map_stats[map_name]['rounds'] += 1
                self._map_stats[map_name]['total_time'] += round_time
                if winner == 'CT':
                    self._map_stats[map_name]['ct_rounds'] += 1
                elif winner == 'T':
                    self._map_stats[map_name]['t_rounds'] += 1

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar round: {e}")

    async def _process_match_event(self, data: Dict, timestamp: datetime):
        """Processar evento de partida"""
        try:
            map_name = data.get('map')
            winner = data.get('winner')
            score_ct = data.get('score_ct', 0)
            score_t = data.get('score_t', 0)
            duration = data.get('duration', 0)

            if map_name:
                self._map_stats[map_name]['matches'] += 1
                self._map_stats[map_name]['total_match_time'] += duration

            # Atualizar estatísticas dos jogadores
            for player_id, stats in data.get('player_stats', {}).items():
                for stat, value in stats.items():
                    self._player_stats[player_id][stat] += value

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar partida: {e}")

    async def _process_connect_event(self, data: Dict, timestamp: datetime):
        """Processar evento de conexão"""
        try:
            player_id = data.get('player_id')
            if player_id:
                self._sessions[player_id] = {
                    'connect_time': timestamp,
                    'disconnect_time': None
                }
                self._player_stats[player_id]['connections'] += 1

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar conexão: {e}")

    async def _process_disconnect_event(self, data: Dict, timestamp: datetime):
        """Processar evento de desconexão"""
        try:
            player_id = data.get('player_id')
            if player_id and player_id in self._sessions:
                session = self._sessions[player_id]
                session['disconnect_time'] = timestamp
                
                # Calcular tempo de sessão
                if session['connect_time']:
                    duration = (timestamp - session['connect_time']).total_seconds()
                    self._player_stats[player_id]['total_time'] += duration

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar desconexão: {e}")

    async def get_player_stats(self, 
                             player_id: str,
                             timeframe: str = None) -> Dict:
        """Obter estatísticas do jogador"""
        try:
            stats = self._player_stats[player_id].copy()
            
            # Calcular estatísticas derivadas
            if stats['kills'] > 0:
                stats['kd_ratio'] = stats['kills'] / max(stats['deaths'], 1)
                stats['hs_ratio'] = stats['headshots'] / stats['kills']
            
            if timeframe:
                # Filtrar por período de tempo
                now = datetime.utcnow()
                if timeframe == 'day':
                    cutoff = now - timedelta(days=1)
                elif timeframe == 'week':
                    cutoff = now - timedelta(weeks=1)
                elif timeframe == 'month':
                    cutoff = now - timedelta(days=30)
                    
                # Implementar filtro de tempo aqui
                
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats do jogador: {e}")
            return {}

    async def get_map_stats(self, map_name: str = None) -> Dict:
        """Obter estatísticas do mapa"""
        try:
            if map_name:
                stats = self._map_stats[map_name].copy()
                
                # Calcular estatísticas derivadas
                if stats['rounds'] > 0:
                    stats['ct_win_rate'] = stats['ct_rounds'] / stats['rounds']
                    stats['t_win_rate'] = stats['t_rounds'] / stats['rounds']
                    stats['avg_round_time'] = stats['total_time'] / stats['rounds']
                return stats
            else:
                # Retornar estatísticas de todos os mapas
                return {
                    map_name: await self.get_map_stats(map_name)
                    for map_name in self._map_stats
                }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats do mapa: {e}")
            return {}

    async def get_weapon_stats(self, weapon: str = None) -> Dict:
        """Obter estatísticas da arma"""
        try:
            if weapon:
                stats = self._weapon_stats[weapon].copy()
                
                # Calcular estatísticas derivadas
                if stats['kills'] > 0:
                    stats['hs_ratio'] = stats['headshots'] / stats['kills']
                return stats
            else:
                # Retornar estatísticas de todas as armas
                return {
                    weapon: await self.get_weapon_stats(weapon)
                    for weapon in self._weapon_stats
                }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats da arma: {e}")
            return {}

    async def get_global_stats(self) -> Dict:
        """Obter estatísticas globais"""
        try:
            stats = {
                'total_kills': sum(
                    p['kills'] for p in self._player_stats.values()
                ),
                'total_rounds': sum(
                    m['rounds'] for m in self._map_stats.values()
                ),
                'total_matches': sum(
                    m['matches'] for m in self._map_stats.values()
                ),
                'total_players': len(self._player_stats),
                'total_playtime': sum(
                    p['total_time'] for p in self._player_stats.values()
                )
            }
            
            # Calcular médias
            if stats['total_matches'] > 0:
                stats['avg_rounds_per_match'] = stats['total_rounds'] / stats['total_matches']
            
            if stats['total_players'] > 0:
                stats['avg_kills_per_player'] = stats['total_kills'] / stats['total_players']
            
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter stats globais: {e}")
            return {}

    async def get_leaderboard(self, 
                             stat: str,
                             limit: int = 10,
                             timeframe: str = None) -> List[Dict]:
        """Obter ranking de jogadores"""
        try:
            # Filtrar jogadores por timeframe se necessário
            players = self._player_stats.items()
            
            # Ordenar por estatística
            sorted_players = sorted(
                players,
                key=lambda x: x[1].get(stat, 0),
                reverse=True
            )
            
            # Formatar resultado
            return [
                {
                    'player_id': player_id,
                    'value': stats.get(stat, 0),
                    'rank': i + 1
                }
                for i, (player_id, stats) in enumerate(sorted_players[:limit])
            ]

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter leaderboard: {e}")
            return []

    async def save_stats(self, filename: str) -> bool:
        """Salvar estatísticas em arquivo"""
        try:
            data = {
                'player_stats': dict(self._player_stats),
                'map_stats': dict(self._map_stats),
                'weapon_stats': dict(self._weapon_stats),
                'saved_at': datetime.utcnow().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            self.logger.logger.info(f"Estatísticas salvas em {filename}")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar estatísticas: {e}")
            return False

    async def load_stats(self, filename: str) -> bool:
        """Carregar estatísticas de arquivo"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self._player_stats = defaultdict(
                lambda: defaultdict(int),
                data.get('player_stats', {})
            )
            self._map_stats = defaultdict(
                lambda: defaultdict(int),
                data.get('map_stats', {})
            )
            self._weapon_stats = defaultdict(
                lambda: defaultdict(int),
                data.get('weapon_stats', {})
            )
            
            self.logger.logger.info(f"Estatísticas carregadas de {filename}")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar estatísticas: {e}")
            return False

    async def reset_stats(self, stat_type: str = None):
        """Resetar estatísticas"""
        try:
            if stat_type == 'player':
                self._player_stats.clear()
            elif stat_type == 'map':
                self._map_stats.clear()
            elif stat_type == 'weapon':
                self._weapon_stats.clear()
            else:
                self._player_stats.clear()
                self._map_stats.clear()
                self._weapon_stats.clear()
                
            self.logger.logger.info(f"Estatísticas resetadas: {stat_type or 'todas'}")

        except Exception as e:
            self.logger.logger.error(f"Erro ao resetar estatísticas: {e}")