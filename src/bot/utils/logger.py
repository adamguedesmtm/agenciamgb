"""
Logging System
Author: adamguedesmtm
Created: 2025-02-21
"""

import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Criar diretório de logs
        log_dir = '/opt/cs2server/logs/bot'
        os.makedirs(log_dir, exist_ok=True)

        # Configurar arquivo de log
        log_file = os.path.join(
            log_dir, 
            f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Formatador
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)