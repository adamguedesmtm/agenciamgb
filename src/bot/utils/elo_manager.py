"""
ELO Manager
Author: adamguedesmtm
Created: 2025-02-21 15:58:46
"""

from typing import Dict, List
from .metrics import MetricsManager

class EloManager:
    def __init__(self, metrics: MetricsManager):
        self.metrics = metrics
        self.BASE_K_FACTOR = 32
        self.MIN_K_FACTOR = 12
        self.PERFORMANCE_WEIGHT = 0.4
        
    def get_k_factor(self, player: Dict) -> float:
        """Calcula K-factor dinâmico"""
        k = self.BASE_K_FACTOR
        
        # Reduzir K-factor com mais jogos
        if games_played := player.get('games_played', 0):
            k *= max(0.5, 1 - (games_played - 50) / 200)
        
        # Ajustar baseado no rating
        rating = player.get('rating', 1000)
        if rating > 1800:
            k *= 0.8
        elif rating < 1200:
            k *= 1.2
            
        return max(self.MIN_K_FACTOR, k)

    def calculate_team_elo(self, team: List[Dict]) -> float:
        """Calcular ELO médio de um time."""
        try:
            total_rating = sum(player.get("rating", 1000) for player in team)
            return round(total_rating / len(team), 2)

        except Exception as e:
            self.metrics.logger.error(f"Erro ao calcular ELO do time: {e}")
            return 1000.0

    def calculate_match_elo(self, match_data: Dict) -> List[Dict]:
        """
        Calcula mudanças de ELO para uma partida
        """
        try:
            team_ct = match_data['team_ct']
            team_t = match_data['team_t']
            score_ct = match_data['score_ct']
            score_t = match_data['score_t']
            
            # Calcular ratings médios
            ct_rating = sum(p.get('rating', 1000) for p in team_ct) / len(team_ct)
            t_rating = sum(p.get('rating', 1000) for p in team_t) / len(team_t)
            
            # Fator de dominância baseado na diferença de rounds
            round_diff = abs(score_ct - score_t)
            dominance_factor = min(1.3, 1 + (round_diff / 32))
            
            # Determinar vencedor
            ct_won = score_ct > score_t
            
            changes = []
            for team, is_ct in [(team_ct, True), (team_t, False)]:
                team_won = ct_won if is_ct else not ct_won
                enemy_rating = t_rating if is_ct else ct_rating
                
                for player in team:
                    # Performance individual
                    performance = self.calculate_performance(player)
                    k_factor = self.get_k_factor(player)
                    
                    # Expectativa de vitória
                    rating_diff = (enemy_rating - player.get('rating', 1000)) / 400
                    expected_win = 1 / (1 + pow(10, rating_diff))
                    
                    # Resultado real
                    if team_won:
                        actual_result = 1 * dominance_factor
                    else:
                        actual_result = max(0.2, 0.4 * performance)
                    
                    # Calcular mudança
                    rating_change = k_factor * (actual_result - expected_win)
                    rating_change *= (1 + (performance - 1) * self.PERFORMANCE_WEIGHT)
                    rating_change = max(-50, min(50, rating_change))
                    
                    old_rating = player.get('rating', 1000)
                    new_rating = old_rating + rating_change
                    
                    # Atualizar no metrics
                    self.metrics.update_player_rating(
                        player['steam_id'],
                        new_rating,
                        rating_change
                    )
                    
                    changes.append({
                        'steam_id': player.get('steam_id'),
                        'old_rating': old_rating,
                        'new_rating': new_rating,
                        'rating_change': rating_change,
                        'performance': performance,
                        'k_factor': k_factor,
                        'won': team_won
                    })
            
            return changes
            
        except Exception as e:
            self.metrics.logger.error(f"Erro ao calcular ELO: {e}")
            return []
    
    def calculate_performance(self, stats: Dict) -> float:
        """Calcula score de performance individual"""
        try:
            # Stats básicas
            kills = stats.get('kills', 0)
            deaths = max(stats.get('deaths', 1), 1)
            assists = stats.get('assists', 0)
            damage = stats.get('damage', 0)
            rounds = stats.get('rounds_played', 1)
            
            # Cálculos
            kd_ratio = kills / deaths
            kpr = kills / rounds
            adr = damage / rounds
            kast = stats.get('kast', 70) / 100
            
            # Impact frags
            entry_kills = stats.get('entry_kills', 0)
            entry_deaths = stats.get('entry_deaths', 0)
            clutches_won = stats.get('clutches_won', 0)
            clutches_lost = stats.get('clutches_lost', 0)
            
            # Entry success
            entry_success = 0.5
            if entry_kills + entry_deaths > 0:
                entry_success = entry_kills / (entry_kills + entry_deaths)
            
            # Clutch success
            clutch_success = 0.5
            if clutches_won + clutches_lost > 0:
                clutch_success = clutches_won / (clutches_won + clutches_lost)
            
            # Performance score
            base_score = (
                kd_ratio * 0.3 +
                kpr * 0.2 +
                (adr / 100) * 0.3 +
                kast * 0.2
            )
            
            impact_score = (
                entry_success * 0.15 +
                clutch_success * 0.15
            )
            
            return base_score * (1 + impact_score)
            
        except Exception as e:
            self.metrics.logger.error(f"Erro ao calcular performance: {e}")
            return 1.0