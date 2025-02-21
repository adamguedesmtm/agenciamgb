"""
Logger Manager
Author: adamguedesmtm
Created: 2025-02-21 13:49:37
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os

class Logger:
    def __init__(self, name: str):
        self.name = name
        self.log_dir = Path('/var/log/cs2server')
        self.log_file = self.log_dir / f'{name}.log'
        
        # Criar diretório se não existir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        
        # Handler de arquivo com rotação
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # Handler de console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Adicionar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def get_logger(self):
        return self.logger