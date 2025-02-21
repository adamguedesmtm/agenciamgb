"""
Monitoring System for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 05:24:43
"""

import psutil
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from .logger import Logger
from .metrics import MetricsManager

class MonitoringSystem:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('monitoring')
        self.metrics = metrics_manager
        self._monitoring = False
        self._monitor_task = None
        self._thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 90.0
        }

    async def start_monitoring(self):
        """Iniciar monitoramento"""
        try:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.logger.logger.info("Monitoramento iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar monitoramento: {e}")

    async def stop_monitoring(self):
        """Parar monitoramento"""
        try:
            if not self._monitoring:
                return

            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                    
            self.logger.logger.info("Monitoramento parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar monitoramento: {e}")

    async def _monitor_loop(self):
        """Loop principal de monitoramento"""
        try:
            while self._monitoring:
                try:
                    # Coletar métricas do sistema
                    system_metrics = await self.get_system_metrics()
                    
                    # Registrar métricas
                    for key, value in system_metrics.items():
                        await self.metrics.record_metric(f"system.{key}", value)
                    
                    # Verificar alertas
                    await self._check_alerts(system_metrics)
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(60)  # Coletar a cada minuto
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no ciclo de monitoramento: {e}")
                    await asyncio.sleep(5)  # Pequeno delay em caso de erro
                    
        except asyncio.CancelledError:
            self.logger.logger.info("Loop de monitoramento cancelado")
        except Exception as e:
            self.logger.logger.error(f"Erro fatal no monitoramento: {e}")

    async def get_system_metrics(self) -> Dict:
        """Coletar métricas do sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu_percent': cpu_percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_percent': disk.percent,
                'timestamp': datetime.now().isoformat()
            }
            
            # Informações de rede
            net_io = psutil.net_io_counters()
            metrics.update({
                'net_bytes_sent': net_io.bytes_sent,
                'net_bytes_recv': net_io.bytes_recv,
                'net_packets_sent': net_io.packets_sent,
                'net_packets_recv': net_io.packets_recv
            })
            
            return metrics
        except Exception as e:
            self.logger.logger.error(f"Erro ao coletar métricas: {e}")
            return {}

    async def _check_alerts(self, metrics: Dict):
        """Verificar e gerar alertas baseado em thresholds"""
        try:
            alerts = []
            
            # CPU
            if metrics.get('cpu_percent', 0) > self._thresholds['cpu_percent']:
                alerts.append({
                    'type': 'high_cpu',
                    'value': metrics['cpu_percent'],
                    'threshold': self._thresholds['cpu_percent']
                })
                
            # Memória
            if metrics.get('memory_percent', 0) > self._thresholds['memory_percent']:
                alerts.append({
                    'type': 'high_memory',
                    'value': metrics['memory_percent'],
                    'threshold': self._thresholds['memory_percent']
                })
                
            # Disco
            if metrics.get('disk_percent', 0) > self._thresholds['disk_percent']:
                alerts.append({
                    'type': 'high_disk',
                    'value': metrics['disk_percent'],
                    'threshold': self._thresholds['disk_percent']
                })
                
            # Registrar alertas
            for alert in alerts:
                await self.metrics.record_metric('system.alert', alert)
                self.logger.logger.warning(
                    f"Alerta: {alert['type']} - Valor: {alert['value']}%"
                )
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar alertas: {e}")

    async def get_process_metrics(self, pid: Optional[int] = None) -> Dict:
        """Coletar métricas de processo específico"""
        try:
            if pid is None:
                pid = os.getpid()

            process = psutil.Process(pid)
            
            metrics = {
                'pid': pid,
                'cpu_percent': process.cpu_percent(interval=1),
                'memory_percent': process.memory_percent(),
                'memory_rss': process.memory_info().rss,
                'memory_vms': process.memory_info().vms,
                'threads': process.num_threads(),
                'fds': process.num_fds(),
                'status': process.status(),
                'created_time': datetime.fromtimestamp(process.create_time()).isoformat()
            }
            
            return metrics
        except Exception as e:
            self.logger.logger.error(f"Erro ao coletar métricas do processo: {e}")
            return {}

    def set_threshold(self, metric: str, value: float):
        """Definir threshold para métrica"""
        try:
            if metric not in self._thresholds:
                raise ValueError(f"Métrica inválida: {metric}")
            
            self._thresholds[metric] = value
            self.logger.logger.info(f"Threshold {metric} definido para {value}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir threshold: {e}")

    def get_thresholds(self) -> Dict:
        """Obter thresholds atuais"""
        return self._thresholds.copy()