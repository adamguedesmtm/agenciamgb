"""
Resource Control System
Author: adamguedesmtm
Created: 2025-02-21 03:33:26
"""

import psutil
import os
from datetime import datetime
from .logger import Logger

class ResourceController:
    def __init__(self):
        self.logger = Logger('resource_control')
        self.limits = {
            'cpu_critical': 90,
            'mem_critical': 90,
            'disk_critical': 90,
            'network_critical': 100000000  # 100MB/s
        }

    async def check_resources(self):
        try:
            resources = {
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
                'network': self._get_network_usage()
            }

            alerts = self._check_limits(resources)
            if alerts:
                await self._handle_alerts(alerts)

            return resources

        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar recursos: {e}")
            return None

    def _get_network_usage(self):
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv,
            'errin': net.errin,
            'errout': net.errout,
            'dropin': net.dropin,
            'dropout': net.dropout
        }

    def _check_limits(self, resources):
        alerts = []
        
        if resources['cpu'] > self.limits['cpu_critical']:
            alerts.append({
                'type': 'CPU',
                'value': resources['cpu'],
                'limit': self.limits['cpu_critical'],
                'critical': True
            })

        if resources['memory'] > self.limits['mem_critical']:
            alerts.append({
                'type': 'Memory',
                'value': resources['memory'],
                'limit': self.limits['mem_critical'],
                'critical': True
            })

        if resources['disk'] > self.limits['disk_critical']:
            alerts.append({
                'type': 'Disk',
                'value': resources['disk'],
                'limit': self.limits['disk_critical'],
                'critical': True
            })

        return alerts

    async def _handle_alerts(self, alerts):
        for alert in alerts:
            message = (
                f"🔥 {alert['type']} CRÍTICO\n"
                f"Valor atual: {alert['value']}%\n"
                f"Limite: {alert['limit']}%"
            )
            self.logger.logger.warning(message)
            
            # Implementar ações corretivas aqui
            if alert['type'] == 'Memory':
                await self._handle_memory_crisis()
            elif alert['type'] == 'Disk':
                await self._handle_disk_crisis()

    async def _handle_memory_crisis(self):
        try:
            # Limpar cache do sistema
            os.system('sync; echo 3 > /proc/sys/vm/drop_caches')
            
            # Reiniciar serviços não críticos
            services_to_restart = ['matchzy']
            for service in services_to_restart:
                os.system(f'systemctl restart {service}')
                
            self.logger.logger.info("Ações corretivas de memória executadas")
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar ações corretivas de memória: {e}")

    async def _handle_disk_crisis(self):
        try:
            # Limpar logs antigos
            os.system('find /opt/cs2server/logs -type f -mtime +7 -delete')
            
            # Limpar demos antigos
            os.system('find /opt/cs2server/demos/processed -type f -mtime +30 -delete')
            
            # Limpar backups antigos
            os.system('find /opt/cs2server/backups -type f -mtime +14 -delete')
            
            self.logger.logger.info("Ações corretivas de disco executadas")
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar ações corretivas de disco: {e}")