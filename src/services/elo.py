"""
Enhanced ELO System
Author: adamguedesmtm
Created: 2025-02-21 15:38:17
"""

from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Player, Match, PlayerMatch
import math

class EloService:
    def __init__(self, db: Session):
        self.db = db
        self.BASE_K_FACTOR = 32
        self.MIN_K_FACTOR = 12
        self.PERFORMANCE_WEIGHT = 0.4
        
    def calculate_performance_score(self, stats: Dict) -> float:
        """Calcula score de performance individual"""
        kd_ratio = stats["kills"] / max(stats["deaths"], 1)
        kast_factor = stats["kast"] / 100
        adr_factor = min(stats["adr"] / 150, 1.3)
        
        impact_score = (
            (stats.get("entry_kills", 0) * 0.15) + 
            (stats.get("clutches_won", 0) * 0.2)
        )
        
        base_score = (kd_ratio * 0.4 + kast_factor * 0.3 + adr_factor * 0.3)
        return base_score * (1 + impact_score)
    
    def get_k_factor(self, player: Player) -> float:
        """Calcula K-factor dinâmico"""
        k = self.BASE_K_FACTOR
        
        if player.games_played > 50:
            k *= max(0.5, 1 - (player.games_played - 50) / 200)
        
        if player.rating > 1800:
            k *= 0.8
        elif player.rating < 1200:
            k *= 1.2
            
        return max(self.MIN_K_FACTOR, k)
    
    def update_match_ratings(self, match_id: int) -> List[Dict]:
        """Atualiza ratings para uma partida completa"""
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError(f"Match {match_id} not found")
            
        player_matches = self.db.query(PlayerMatch).filter(
            PlayerMatch.match_id == match_id
        ).all()
        
        # Separar jogadores por time
        team_ct = []
        team_t = []
        
        for pm in player_matches:
            player = self.db.query(Player).filter(Player.id == pm.player_id).first()
            stats = {
                "player": player,
                "player_match": pm,
                "kills": pm.kills,
                "deaths": pm.deaths,
                "kast": pm.kast,
                "adr": pm.adr,
                "entry_kills": pm.entry_kills,
                "clutches_won": pm.clutches_won
            }
            
            if pm.team == "CT":
                team_ct.append(stats)
            else:
                team_t.append(stats)
        
        # Calcular ratings médios
        ct_rating = sum(p["player"].rating for p in team_ct) / len(team_ct)
        t_rating = sum(p["player"].rating for p in team_t) / len(team_t)
        
        # Determinar vencedor
        ct_won = match.score_ct > match.score_t
        round_diff = abs(match.score_ct - match.score_t)
        dominance_factor = min(1.3, 1 + (round_diff / 32))
        
        # Atualizar ratings
        updates = []
        for team, is_ct in [(team_ct, True), (team_t, False)]:
            team_won = ct_won if is_ct else not ct_won
            enemy_rating = t_rating if is_ct else ct_rating
            
            for stats in team:
                player = stats["player"]
                pm = stats["player_match"]
                
                # Calcular performance
                performance = self.calculate_performance_score(stats)
                
                # Calcular K-factor
                k_factor = self.get_k_factor(player)
                
                # Calcular expectativa
                rating_diff = (enemy_rating - player.rating) / 400
                expected_win = 1 / (1 + math.pow(10, rating_diff))
                
                # Calcular resultado real
                if team_won:
                    actual_result = 1 * dominance_factor
                else:
                    actual_result = max(0.2, 0.4 * performance)
                
                # Calcular mudança de rating
                rating_change = k_factor * (actual_result - expected_win)
                rating_change *= (1 + (performance - 1) * self.PERFORMANCE_WEIGHT)
                rating_change = max(-50, min(50, rating_change))
                
                # Atualizar player
                player.rating += rating_change
                player.games_played += 1
                player.last_match = datetime.utcnow()
                
                if team_won:
                    player.wins += 1
                else:
                    player.losses += 1
                
                # Atualizar player_match
                pm.rating_change = rating_change
                
                updates.append({
                    "player_id": player.id,
                    "old_rating": player.rating - rating_change,
                    "new_rating": player.rating,
                    "rating_change": rating_change,
                    "performance_score": performance
                })
                
        self.db.commit()
        return updates
    
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