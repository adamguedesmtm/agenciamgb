"""
Logger Configuration
Author: adamguedesmtm
Created: 2025-02-21 14:39:11
"""

import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            
            # Criar diretório de logs se não existir
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Handler para arquivo
            file_handler = logging.FileHandler(
                f'{log_dir}/{name}_{datetime.utcnow().strftime("%Y%m%d")}.log'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formato do log
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)