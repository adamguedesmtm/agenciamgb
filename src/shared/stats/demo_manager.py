"""
Demo Manager - CS2 Demo Processing System
Author: adamguedesmtm
Created: 2025-02-21 15:15:42
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from ...web.models.stats import MatchStats, MapStats, PlayerStats, RoundStats

class DemoManager:
    def __init__(self, cs_demo_manager_path: str, demos_dir: str):
        self.cs_demo_manager_path = Path(cs_demo_manager_path)
        self.demos_dir = Path(demos_dir)
        self.demos_dir.mkdir(parents=True, exist_ok=True)

    async def process_demo(self, demo_path: str) -> Optional[MatchStats]:
        """Processar uma demo usando CS Demo Manager"""
        try:
            demo_file = Path(demo_path)
            if not demo_file.exists():
                raise FileNotFoundError(f"Demo não encontrada: {demo_path}")

            output_dir = self.demos_dir / demo_file.stem
            output_dir.mkdir(exist_ok=True)

            process = await asyncio.create_subprocess_exec(
                str(self.cs_demo_manager_path),
                "analyze",
                "-demo", str(demo_file),
                "-out", str(output_dir / "analysis.json"),
                "-format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Erro ao processar demo: {stderr.decode()}")

            with open(output_dir / "analysis.json") as f:
                analysis = json.load(f)

            return await self._convert_analysis(analysis, demo_path)

        except Exception as e:
            print(f"Erro ao processar demo {demo_path}: {e}")
            return None

    async def _convert_analysis(self, analysis: Dict, demo_path: str) -> MatchStats:
        """Converter análise do CS Demo Manager para nosso formato"""
        try:
            match_date = datetime.fromtimestamp(analysis["matchStartTime"])
            match_type = self._determine_match_type(analysis)

            rounds = []
            for round_data in analysis["rounds"]:
                round_stats = RoundStats(
                    round_number=round_data["number"],
                    winner_side=round_data["winnerSide"],
                    win_type=round_data["winType"],
                    duration=round_data["duration"],
                    winning_play=round_data.get("winningPlay")
                )
                rounds.append(round_stats)

            players = []
            for player_data in analysis["players"]:
                player_stats = PlayerStats(
                    steam_id=player_data["steamId"],
                    name=player_data["name"],
                    kills=player_data["kills"],
                    deaths=player_data["deaths"],
                    assists=player_data["assists"],
                    kd_ratio=player_data["kdRatio"],
                    hs_percentage=player_data["headshotPercentage"],
                    adr=player_data["averageDamagePerRound"],
                    kast=player_data["kast"],
                    rating=player_data["rating"]
                )
                players.append(player_stats)

            map_stats = MapStats(
                map_name=analysis["mapName"],
                score_ct=analysis["scoreTeams"]["CT"],
                score_t=analysis["scoreTeams"]["T"],
                duration=analysis["matchDuration"],
                rounds=rounds,
                players=players
            )

            match_stats = MatchStats(
                match_id=analysis["matchId"],
                date=match_date,
                map_name=analysis["mapName"],
                type=match_type,
                demo_path=demo_path,
                maps=[map_stats],
                total_rounds=len(rounds),
                final_score=f"{analysis['scoreTeams']['CT']}-{analysis['scoreTeams']['T']}",
                winner="CT" if analysis["scoreTeams"]["CT"] > analysis["scoreTeams"]["T"] else "T",
                duration=analysis["matchDuration"]
            )

            return match_stats

        except Exception as e:
            print(f"Erro ao converter análise: {e}")
            return None

    def _determine_match_type(self, analysis: Dict) -> str:
        """Determinar tipo de partida baseado na análise"""
        max_players = len(analysis["players"])
        if max_players <= 4:
            return "Wingman"
        elif max_players <= 10:
            return "Competitive"
        else:
            return "Other"