"""
Metrics Manager for tracking system statistics
Author: adamguedesmtm
Created: 2025-02-21 14:39:11
"""

from typing import Optional, Dict, Any
import time
from .logger import Logger

class MetricsManager:
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger('metrics')
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

    async def record_player_stat(self, stat_type: str, value: Any):
        """Registrar estatística"""
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
        """Obter todas as estatísticas"""
        uptime = time.time() - self.start_time
        return {
            'uptime': uptime,
            'metrics': self.metrics
        }

    def reset_stats(self):
        """Resetar estatísticas"""
        self.metrics = {k: {} if isinstance(v, dict) else 0 for k, v in self.metrics.items()}
        self.start_time = time.time()