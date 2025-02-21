"""
Monitor - CS2 Stats Monitoring System
Author: adamguedesmtm
Created: 2025-02-21 15:21:43
"""

import psutil
import asyncio
from datetime import datetime
from pathlib import Path
from ..config import settings

class SystemMonitor:
    def __init__(self):
        self.start_time = datetime.utcnow()
        
    async def get_system_status(self):
        """Obter status detalhado do sistema"""
        try:
            # Status do servidor
            uptime = datetime.utcnow() - self.start_time
            
            # Status do sistema
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Status dos diretórios
            demos_count = len(list(Path(settings.DEMOS_DIR).glob('*.dem')))
            analysis_count = len(list(Path(settings.ANALYSIS_DIR).glob('*.json')))
            
            return {
                "server": {
                    "status": "running",
                    "uptime": str(uptime).split('.')[0],
                    "version": "1.0.0"
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                },
                "stats": {
                    "demos_stored": demos_count,
                    "analysis_stored": analysis_count
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }