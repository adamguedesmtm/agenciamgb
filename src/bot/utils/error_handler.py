"""
Error Handler for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 11:44:00
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import traceback
import sys
import asyncio
from .logger import Logger
from .metrics import MetricsManager
from .notification_manager import NotificationManager

class ErrorHandler:
    def __init__(self,
                 logger: Logger,
                 metrics: MetricsManager,
                 notifications: NotificationManager):
        self.logger = logger
        self.metrics = metrics
        self.notifications = notifications
        self._handlers: Dict[str, List[Callable]] = {}
        self._error_history: List[Dict] = []
        self._max_history = 1000
        self._notify_critical = True
        self._collect_sys_info = True

    async def handle_error(self,
                          error: Exception,
                          context: Dict = None,
                          notify: bool = True) -> Dict:
        """Processar e registrar erro"""
        try:
            # Criar registro do erro
            timestamp = datetime.utcnow()
            error_id = f"ERR_{timestamp.strftime('%Y%m%d%H%M%S')}_{id(error)}"
            
            error_info = {
                'id': error_id,
                'timestamp': timestamp.isoformat(),
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._format_traceback(error),
                'context': context or {},
                'sys_info': (
                    self._collect_system_info()
                    if self._collect_sys_info else None
                )
            }
            
            # Adicionar ao histórico
            self._add_to_history(error_info)
            
            # Registrar log
            self.logger.error(
                f"Erro {error_id}: {error}",
                error_info=error_info
            )
            
            # Registrar métrica
            await self.metrics.record_metric(
                f"errors.{error_info['type'].lower()}",
                1
            )
            
            # Notificar se necessário
            if notify and self._should_notify(error):
                await self._send_notification(error_info)
                
            # Executar handlers específicos
            await self._execute_handlers(error, error_info)
            
            return error_info

        except Exception as e:
            # Fallback para log básico em caso de erro
            self.logger.critical(
                f"Erro ao processar erro: {e}\n"
                f"Erro original: {error}"
            )
            return {
                'id': 'ERR_INTERNAL',
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'InternalError',
                'message': f"Erro ao processar erro: {e}"
            }

    def _format_traceback(self, error: Exception) -> List[str]:
        """Formatar stack trace do erro"""
        try:
            return traceback.format_exception(
                type(error),
                error,
                error.__traceback__
            )
        except:
            return ['Erro ao formatar traceback']

    def _collect_system_info(self) -> Dict:
        """Coletar informações do sistema"""
        try:
            import platform
            import psutil
            
            return {
                'platform': platform.platform(),
                'python': sys.version,
                'cpu_percent': psutil.cpu_percent(),
                'memory': dict(psutil.virtual_memory()._asdict()),
                'disk': dict(psutil.disk_usage('/')._asdict()),
                'process': {
                    'pid': os.getpid(),
                    'memory': dict(
                        psutil.Process().memory_info()._asdict()
                    )
                }
            }
        except:
            return {'error': 'Erro ao coletar info do sistema'}

    def _add_to_history(self, error_info: Dict):
        """Adicionar erro ao histórico"""
        self._error_history.append(error_info)
        
        # Limitar tamanho do histórico
        while len(self._error_history) > self._max_history:
            self._error_history.pop(0)

    def _should_notify(self, error: Exception) -> bool:
        """Verificar se erro deve gerar notificação"""
        if not self._notify_critical:
            return False
            
        # Notificar erros críticos
        return isinstance(error, (
            SystemError,
            MemoryError,
            KeyboardInterrupt,
            SystemExit
        ))

    async def _send_notification(self, error_info: Dict):
        """Enviar notificação sobre erro"""
        try:
            await self.notifications.create_notification(
                title=f"Erro Crítico: {error_info['type']}",
                message=(
                    f"ID: {error_info['id']}\n"
                    f"Mensagem: {error_info['message']}\n"
                    f"Timestamp: {error_info['timestamp']}"
                ),
                type='error',
                metadata=error_info,
                priority=1
            )
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação: {e}")

    async def _execute_handlers(self,
                              error: Exception,
                              error_info: Dict):
        """Executar handlers registrados para o tipo de erro"""
        error_type = type(error).__name__
        
        if error_type in self._handlers:
            for handler in self._handlers[error_type]:
                try:
                    result = handler(error, error_info)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    self.logger.error(
                        f"Erro em handler de {error_type}: {e}"
                    )

    def register_handler(self,
                        error_type: str,
                        handler: Callable) -> bool:
        """Registrar handler para tipo de erro"""
        try:
            if error_type not in self._handlers:
                self._handlers[error_type] = []
            self._handlers[error_type].append(handler)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao registrar handler: {e}")
            return False

    def unregister_handler(self,
                          error_type: str,
                          handler: Callable) -> bool:
        """Remover handler"""
        try:
            if error_type in self._handlers:
                if handler in self._handlers[error_type]:
                    self._handlers[error_type].remove(handler)
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao remover handler: {e}")
            return False

    def get_error_history(self,
                         error_type: str = None,
                         limit: int = None) -> List[Dict]:
        """Obter histórico de erros"""
        try:
            history = self._error_history
            
            if error_type:
                history = [
                    e for e in history
                    if e['type'] == error_type
                ]
                
            if limit:
                history = history[-limit:]
                
            return history
            
        except Exception as e:
            self.logger.error(f"Erro ao obter histórico: {e}")
            return []

        def clear_history(self):
        """Limpar histórico de erros"""
        try:
            self._error_history.clear()
        except Exception as e:
            self.logger.error(f"Erro ao limpar histórico: {e}")

    def set_notification_config(self, notify_critical: bool = True):
        """Configurar notificações de erro"""
        try:
            self._notify_critical = notify_critical
            self.logger.info(
                f"Notificações {'ativadas' if notify_critical else 'desativadas'}"
            )
        except Exception as e:
            self.logger.error(f"Erro na configuração: {e}")

    def set_sys_info_collection(self, enabled: bool = True):
        """Configurar coleta de informações do sistema"""
        try:
            self._collect_sys_info = enabled
            self.logger.info(
                f"Coleta de info {'ativada' if enabled else 'desativada'}"
            )
        except Exception as e:
            self.logger.error(f"Erro na configuração: {e}")

    async def get_stats(self) -> Dict:
        """Obter estatísticas de erros"""
        try:
            stats = {
                'total_errors': len(self._error_history),
                'by_type': {},
                'handlers': {
                    type_: len(handlers)
                    for type_, handlers in self._handlers.items()
                }
            }
            
            # Contar erros por tipo
            for error in self._error_history:
                error_type = error['type']
                if error_type not in stats['by_type']:
                    stats['by_type'][error_type] = 0
                stats['by_type'][error_type] += 1
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}