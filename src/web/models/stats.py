"""
Stats Models - CS2 Stats Data Models
Author: adamguedesmtm
Created: 2025-02-21 15:15:42
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PlayerStats(BaseModel):
    steam_id: str
    name: str
    kills: int
    deaths: int
    assists: int
    kd_ratio: float
    hs_percentage: float
    adr: float
    kast: float
    rating: float
    
class RoundStats(BaseModel):
    round_number: int
    winner_side: str
    win_type: str
    duration: float
    winning_play: Optional[str]

class MapStats(BaseModel):
    map_name: str
    score_ct: int
    score_t: int
    duration: float
    rounds: List[RoundStats]
    players: List[PlayerStats]

class MatchStats(BaseModel):
    match_id: str
    date: datetime
    map_name: str
    type: str
    demo_path: str
    maps: List[MapStats]
    total_rounds: int
    final_score: str
    winner: str
    duration: float