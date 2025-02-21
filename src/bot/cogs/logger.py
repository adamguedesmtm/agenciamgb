"""
Logger for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:17:58
"""

import logging
from datetime import datetime
import os

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Criar diretório de logs
        log_dir = "/var/log/cs2server"
        os.makedirs(log_dir, exist_ok=True)
        
        # Handler para arquivo
        log_file = f"{log_dir}/{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Adicionar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def rotate_logs(self):
        """Rotacionar logs antigos"""
        try:
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    log_file = handler.baseFilename
                    if os.path.exists(log_file):
                        # Renomear com timestamp
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        new_name = f"{log_file}.{timestamp}"
                        os.rename(log_file, new_name)
                        
                    # Criar novo handler
                    new_handler = logging.FileHandler(log_file)
                    new_handler.setFormatter(handler.formatter)
                    new_handler.setLevel(handler.level)
                    self.logger.addHandler(new_handler)
                    self.logger.removeHandler(handler)
                    
        except Exception as e:
            print(f"Erro ao rotacionar logs: {e}")