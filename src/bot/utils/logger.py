"""
Logger System for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 11:44:00
"""

import logging
import logging.handlers
from pathlib import Path
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
import os

class Logger:
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self._config = config or self._default_config()
        self.logger = self._setup_logger()

    def _default_config(self) -> Dict:
        """Configuração padrão do logger"""
        return {
            'log_dir': '/opt/cs2server/logs',
            'max_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'level': 'INFO',
            'console_output': True,
            'file_output': True,
            'json_format': True,
            'include_trace': True,
            'include_process': True,
            'include_thread': True
        }

    def _setup_logger(self) -> logging.Logger:
        """Configurar logger"""
        try:
            # Criar logger
            logger = logging.getLogger(self.name)
            logger.setLevel(self._get_level())
            
            # Evitar duplicação de handlers
            logger.handlers.clear()
            
            # Formatar mensagens
            formatter = self._create_formatter()
            
            # Adicionar handler de console
            if self._config['console_output']:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
                
            # Adicionar handler de arquivo
            if self._config['file_output']:
                file_handler = self._create_file_handler(formatter)
                logger.addHandler(file_handler)
                
            return logger

        except Exception as e:
            print(f"Erro ao configurar logger: {e}")
            # Fallback para logger básico
            basic_logger = logging.getLogger(self.name)
            basic_logger.setLevel(logging.INFO)
            return basic_logger

    def _get_level(self) -> int:
        """Obter nível de log"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(
            self._config['level'].upper(),
            logging.INFO
        )

    def _create_formatter(self) -> logging.Formatter:
        """Criar formatador de log"""
        if self._config['json_format']:
            return JsonFormatter(
                self._config['include_trace'],
                self._config['include_process'],
                self._config['include_thread']
            )
        return logging.Formatter(
            self._config['format'],
            self._config['date_format']
        )

    def _create_file_handler(self,
                           formatter: logging.Formatter
                           ) -> logging.Handler:
        """Criar handler para arquivo"""
        # Criar diretório se necessário
        log_dir = Path(self._config['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de log
        log_file = log_dir / f"{self.name}.log"
        
        # Criar rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._config['max_size'],
            backupCount=self._config['backup_count']
        )
        handler.setFormatter(formatter)
        
        return handler

    def update_config(self, config: Dict):
        """Atualizar configuração do logger"""
        try:
            self._config.update(config)
            self.logger = self._setup_logger()
        except Exception as e:
            self.error(f"Erro ao atualizar config: {e}")

    def debug(self, message: str, **kwargs):
        """Log nível DEBUG"""
        self._log('debug', message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log nível INFO"""
        self._log('info', message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log nível WARNING"""
        self._log('warning', message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log nível ERROR"""
        self._log('error', message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log nível CRITICAL"""
        self._log('critical', message, **kwargs)

    def _log(self, level: str, message: str, **kwargs):
        """Registrar log com contexto adicional"""
        try:
            # Adicionar timestamp
            kwargs['timestamp'] = datetime.utcnow().isoformat()
            
            # Adicionar informações do processo
            if self._config['include_process']:
                kwargs['process'] = {
                    'id': os.getpid(),
                    'name': self.name
                }
                
            # Registrar log
            log_func = getattr(self.logger, level)
            log_func(message, extra={'context': kwargs})
            
        except Exception as e:
            # Fallback para log básico
            print(
                f"Erro ao registrar log: {e}\n"
                f"Mensagem original: {message}"
            )

class JsonFormatter(logging.Formatter):
    """Formatador de logs em JSON"""
    
    def __init__(self,
                 include_trace: bool = True,
                 include_process: bool = True,
                 include_thread: bool = True):
        super().__init__()
        self.include_trace = include_trace
        self.include_process = include_process
        self.include_thread = include_thread

    def format(self, record: logging.LogRecord) -> str:
        """Formatar registro de log como JSON"""
        try:
            data = {
                'timestamp': self.formatTime(record),
                'logger': record.name,
                'level': record.levelname,
                'message': record.getMessage()
            }
            
            # Adicionar contexto
            if hasattr(record, 'context'):
                data.update(record.context)
                
            # Adicionar stack trace para erros
            if self.include_trace and record.exc_info:
                data['traceback'] = self.formatException(
                    record.exc_info
                )
                
            # Adicionar informações do processo
            if self.include_process:
                data['process'] = {
                    'id': record.process,
                    'name': record.processName
                }
                
            # Adicionar informações da thread
            if self.include_thread:
                data['thread'] = {
                    'id': record.thread,
                    'name': record.threadName
                }
                
            return json.dumps(data)

        except Exception as e:
            # Fallback para formato simples
            return f"{self.formatTime(record)} - {record.levelname} - {record.getMessage()}"

    def formatTime(self, record: logging.LogRecord) -> str:
        """Formatar timestamp do log"""
        try:
            dt = datetime.fromtimestamp(record.created)
            return dt.isoformat()
        except:
            return super().formatTime(record)

    def formatException(self, exc_info) -> Dict:
        """Formatar informações de exceção"""
        try:
            return {
                'type': exc_info[0].__name__,
                'message': str(exc_info[1]),
                'stack': traceback.format_tb(exc_info[2])
            }
        except:
            return {
                'error': 'Erro ao formatar exceção'
            }