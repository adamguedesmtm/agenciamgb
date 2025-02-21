"""
ELO Manager
Author: adamguedesmtm
Created: 2025-02-21 15:42:55
"""

from typing import Dict, List, Optional
from datetime import datetime
from .metrics import MetricsManager

class EloManager:
    def __init__(self, metrics: MetricsManager):
        self.metrics = metrics
        self.BASE_K_FACTOR = 32
        self.MIN_K_FACTOR = 12
        self.PERFORMANCE_WEIGHT = 0.4
        
    def calculate_performance_score(self, stats: Dict) -> float:
        """Calcula score de performance individual"""
        kd_ratio = stats["kills"] / max(stats["deaths"], 1)
        kast_factor = stats.get("kast", 70) / 100  # Default KAST 70%
        adr_factor = min(stats.get("adr", 80) / 150, 1.3)  # Default ADR 80
        
        impact_score = (
            (stats.get("entry_kills", 0) * 0.15) + 
            (stats.get("clutches_won", 0) * 0.2)
        )
        
        base_score = (kd_ratio * 0.4 + kast_factor * 0.3 + adr_factor * 0.3)
        return base_score * (1 + impact_score)
    
    def get_rank_info(self, rating: float) -> Dict:
        """Retorna informações do rank"""
        ranks = [
            {"name": "Ferro I", "min": 0, "max": 700, "icon": "🔨"},
            {"name": "Ferro II", "min": 700, "max": 800, "icon": "🔨"},
            {"name": "Bronze I", "min": 800, "max": 900, "icon": "🥉"},
            {"name": "Bronze II", "min": 900, "max": 1000, "icon": "🥉"},
            {"name": "Prata I", "min": 1000, "max": 1100, "icon": "⚔️"},
            {"name": "Prata II", "min": 1100, "max": 1200, "icon": "⚔️"},
            {"name": "Ouro I", "min": 1200, "max": 1300, "icon": "🏆"},
            {"name": "Ouro II", "min": 1300, "max": 1400, "icon": "🏆"},
            {"name": "Platina I", "min": 1400, "max": 1500, "icon": "💎"},
            {"name": "Platina II", "min": 1500, "max": 1600, "icon": "💎"},
            {"name": "Diamante I", "min": 1600, "max": 1700, "icon": "💠"},
            {"name": "Diamante II", "min": 1700, "max": 1800, "icon": "💠"},
            {"name": "Mestre", "min": 1800, "max": 2000, "icon": "👑"},
            {"name": "Elite", "min": 2000, "max": 2200, "icon": "🌟"},
            {"name": "Elite Global", "min": 2200, "max": 999999, "icon": "🌠"}
        ]
        
        for rank in ranks:
            if rank["min"] <= rating < rank["max"]:
                progress = (rating - rank["min"]) / (rank["max"] - rank["min"])
                return {
                    "name": rank["name"],
                    "icon": rank["icon"],
                    "rating": round(rating),
                    "progress": round(progress * 100),
                    "next_rank": ranks[ranks.index(rank) + 1]["name"] if rank["name"] != "Elite Global" else None,
                    "points_to_next": round(rank["max"] - rating) if rank["name"] != "Elite Global" else 0
                }

    def calculate_match_elo(self, match_data: Dict) -> List[Dict]:
        """
        Calcula mudanças de ELO para uma partida
        
        Args:
            match_data: Dicionário com dados da partida {
                'team_ct': [lista de jogadores CT],
                'team_t': [lista de jogadores T],
                'score_ct': int,
                'score_t': int
            }
        """
        team_ct = match_data['team_ct']
        team_t = match_data['team_t']
        ct_score = match_data['score_ct']
        t_score = match_data['score_t']
        total_rounds = ct_score + t_score
        
        # Calcular ratings médios
        ct_rating = sum(p["rating"] for p in team_ct) / len(team_ct)
        t_rating = sum(p["rating"] for p in team_t) / len(team_t)
        
        # Determinar vencedor e fator de dominância
        ct_won = ct_score > t_score
        round_diff = abs(ct_score - t_score)
        dominance_factor = min(1.3, 1 + (round_diff / 32))
        
        changes = []
        for team, is_ct in [(team_ct, True), (team_t, False)]:
            team_won = ct_won if is_ct else not ct_won
            enemy_rating = t_rating if is_ct else ct_rating
            
            for player in team:
                # Calcular performance
                performance = self.calculate_performance_score(player)
                
                # Ajustar k_factor
                k_factor = self.BASE_K_FACTOR
                if player.get("games_played", 0) > 50:
                    k_factor *= max(0.5, 1 - (player["games_played"] - 50) / 200)
                if player.get("rating", 1000) > 1800:
                    k_factor *= 0.8
                
                # Calcular expectativa
                rating_diff = (enemy_rating - player["rating"]) / 400
                expected_win = 1 / (1 + pow(10, rating_diff))
                
                # Calcular resultado real
                if team_won:
                    actual_result = 1 * dominance_factor
                else:
                    # Perder com boa performance reduz a perda
                    actual_result = max(0.2, 0.4 * performance)
                
                # Calcular mudança de rating
                rating_change = k_factor * (actual_result - expected_win)
                rating_change *= (1 + (performance - 1) * self.PERFORMANCE_WEIGHT)
                rating_change = max(-50, min(50, rating_change))
                
                changes.append({
                    "steam_id": player["steam_id"],
                    "old_rating": player["rating"],
                    "new_rating": player["rating"] + rating_change,
                    "rating_change": rating_change,
                    "performance": performance,
                    "won": team_won
                })
                
                # Atualizar métricas
                self.metrics.update_player_rating(
                    player["steam_id"],
                    player["rating"] + rating_change,
                    rating_change
                )
        
        return changes