"""
Metrics Manager for tracking system and player statistics
Author: adamguedesmtm
Created: 2025-02-21 15:54:36
"""

from typing import Optional, Dict, List, Any, Union
import time
import json
from pathlib import Path
from datetime import datetime
from .logger import Logger

class MetricsManager:
    def __init__(self, 
                 data_dir: str = "/opt/cs2bot/data",
                 logger: Optional[Logger] = None):
        self.logger = logger or Logger('metrics')
        self.data_dir = Path(data_dir)
        
        # Métricas do sistema
        self.metrics = {
            'matches_setup': 0,
            'matches_started': 0,
            'matches_ended': 0,
            'server_force_ends': 0,
            'map_changes': {},
            'team_joins': 0,
            'team_leaves': 0,
            'player_ready': 0,
            'match_pauses': 0,
            'match_unpauses': 0,
            'tech_pauses': 0,
            'score_updates': 0
        }
        self.start_time = time.time()
        
        # Arquivos de dados
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.players_file = self.data_dir / "players.json"
        self.matches_file = self.data_dir / "matches.json"
        self.accounts_file = self.data_dir / "accounts.json"
        
        # Carregar dados
        self.players = self._load_json(self.players_file, {})
        self.matches = self._load_json(self.matches_file, [])
        self.accounts = self._load_json(self.accounts_file, {})

    def _load_json(self, file: Path, default: Union[Dict, List]) -> Union[Dict, List]:
        """Carregar arquivo JSON"""
        try:
            if file.exists():
                with open(file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar {file}: {e}")
        return default
    
    def _save_json(self, file: Path, data: Union[Dict, List]):
        """Salvar arquivo JSON"""
        try:
            with open(file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar {file}: {e}")

    # Métodos existentes do sistema
    async def record_player_stat(self, stat_type: str, value: Any):
        """Registrar estatística do sistema"""
        try:
            if stat_type in self.metrics:
                if isinstance(self.metrics[stat_type], dict):
                    if value in self.metrics[stat_type]:
                        self.metrics[stat_type][value] += 1
                    else:
                        self.metrics[stat_type][value] = 1
                else:
                    self.metrics[stat_type] += 1
        except Exception as e:
            self.logger.error(f"Erro ao registrar métrica {stat_type}: {e}")

    def get_stats(self) -> Dict:
        """Obter estatísticas do sistema"""
        uptime = time.time() - self.start_time
        return {
            'uptime': uptime,
            'metrics': self.metrics
        }

    def reset_stats(self):
        """Resetar estatísticas do sistema"""
        self.metrics = {k: {} if isinstance(v, dict) else 0 for k, v in self.metrics.items()}
        self.start_time = time.time()

    # Novos métodos para estatísticas de jogadores
    def update_player_rating(self, steam_id: str, new_rating: float, rating_change: float):
        """Atualizar rating de um jogador"""
        if steam_id not in self.players:
            self.players[steam_id] = {
                'rating': 1000,
                'games_played': 0,
                'wins': 0,
                'losses': 0,
                'history': []
            }
        
        player = self.players[steam_id]
        player['rating'] = new_rating
        player['history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'rating_change': rating_change,
            'new_rating': new_rating
        })
        
        self._save_json(self.players_file, self.players)

    def get_player_stats(self, steam_id: str) -> Dict:
        """Buscar estatísticas de um jogador"""
        return self.players.get(steam_id, {
            'rating': 1000,
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'headshots': 0,
            'entry_kills': 0,
            'clutches_won': 0,
            'maps': {}
        })

    def link_accounts(self, steam_id: str, discord_id: str, discord_name: str):
        """Vincular conta Steam ao Discord"""
        self.accounts[discord_id] = {
            'steam_id': steam_id,
            'discord_name': discord_name,
            'linked_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        self._save_json(self.accounts_file, self.accounts)

    def get_steam_id(self, discord_id: str) -> Optional[str]:
        """Buscar Steam ID vinculado ao Discord ID"""
        if account := self.accounts.get(discord_id):
            return account.get('steam_id')
        return None

    def get_discord_id(self, steam_id: str) -> Optional[str]:
        """Buscar Discord ID vinculado ao Steam ID"""
        for discord_id, account in self.accounts.items():
            if account.get('steam_id') == steam_id:
                return discord_id
        return None

    def get_top_players(self, limit: int = 10, page: int = 1) -> List[Dict]:
        """Buscar top jogadores"""
        try:
            players_list = [
                {
                    'steam_id': steam_id,
                    'name': self.accounts.get(self.get_discord_id(steam_id), {}).get('discord_name', f"Player_{steam_id[-4:]}"),
                    'rating': stats.get('rating', 1000),
                    'wins': stats.get('wins', 0),
                    'losses': stats.get('losses', 0),
                    'games_played': stats.get('games_played', 0)
                }
                for steam_id, stats in self.players.items()
            ]
            
            players_list.sort(key=lambda x: x['rating'], reverse=True)
            start = (page - 1) * limit
            return players_list[start:start + limit]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar top players: {e}")
            return []

    def record_match(self, match_data: Dict):
        """Registrar uma partida"""
        try:
            match_id = len(self.matches)
            
            # Adicionar partida ao histórico
            match = {
                'id': match_id,
                'timestamp': datetime.utcnow().isoformat(),
                'map': match_data.get('map'),
                'score_ct': match_data.get('score_ct'),
                'score_t': match_data.get('score_t'),
                'players': match_data.get('players', [])
            }
            
            self.matches.append(match)
            self._save_json(self.matches_file, self.matches)
            
            # Atualizar stats dos jogadores
            for player_data in match_data.get('players', []):
                steam_id = player_data.get('steam_id')
                if not steam_id:
                    continue
                
                if steam_id not in self.players:
                    self.players[steam_id] = self.get_player_stats(steam_id)
                
                player = self.players[steam_id]
                player['games_played'] += 1
                player['wins'] += 1 if player_data.get('won') else 0
                player['losses'] += 0 if player_data.get('won') else 1
                player['kills'] = player.get('kills', 0) + player_data.get('kills', 0)
                player['deaths'] = player.get('deaths', 0) + player_data.get('deaths', 0)
                player['assists'] = player.get('assists', 0) + player_data.get('assists', 0)
                player['headshots'] = player.get('headshots', 0) + player_data.get('headshots', 0)
                player['entry_kills'] = player.get('entry_kills', 0) + player_data.get('entry_kills', 0)
                player['clutches_won'] = player.get('clutches_won', 0) + player_data.get('clutches_won', 0)
                
                # Atualizar stats do mapa
                map_name = match_data.get('map', 'unknown')
                if map_name not in player['maps']:
                    player['maps'][map_name] = {'played': 0, 'wins': 0}
                
                player['maps'][map_name]['played'] += 1
                if player_data.get('won'):
                    player['maps'][map_name]['wins'] += 1
            
            self._save_json(self.players_file, self.players)
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar partida: {e}")