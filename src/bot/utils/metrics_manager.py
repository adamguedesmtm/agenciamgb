"""
Metrics Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:47:01
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
from collections import defaultdict
import asyncio
from .logger import Logger

class MetricsManager:
    def __init__(self):
        self.logger = Logger('metrics_manager')
        self._metrics = defaultdict(list)
        self._aggregations = defaultdict(dict)
        self._retention_days = 30
        self._cleanup_task = None

    async def start(self):
        """Iniciar gerenciador de métricas"""
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.logger.info("Metrics manager iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar metrics manager: {e}")

    async def stop(self):
        """Parar gerenciador de métricas"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            self.logger.logger.info("Metrics manager parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar metrics manager: {e}")

    async def record_metric(self, 
                          name: str,
                          value: Union[int, float, Dict],
                          timestamp: datetime = None):
        """Registrar nova métrica"""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            metric = {
                'value': value,
                'timestamp': timestamp
            }
            
            self._metrics[name].append(metric)
            
            # Atualizar agregações
            await self._update_aggregations(name, value, timestamp)
            
            self.logger.logger.debug(f"Métrica registrada: {name}")

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar métrica: {e}")

    async def _update_aggregations(self,
                                 name: str,
                                 value: Union[int, float, Dict],
                                 timestamp: datetime):
        """Atualizar agregações da métrica"""
        try:
            if isinstance(value, (int, float)):
                # Atualizar min/max
                if 'min' not in self._aggregations[name]:
                    self._aggregations[name]['min'] = value
                else:
                    self._aggregations[name]['min'] = min(
                        self._aggregations[name]['min'],
                        value
                    )
                    
                if 'max' not in self._aggregations[name]:
                    self._aggregations[name]['max'] = value
                else:
                    self._aggregations[name]['max'] = max(
                        self._aggregations[name]['max'],
                        value
                    )
                    
                # Atualizar soma e contagem para média
                if 'sum' not in self._aggregations[name]:
                    self._aggregations[name]['sum'] = value
                    self._aggregations[name]['count'] = 1
                else:
                    self._aggregations[name]['sum'] += value
                    self._aggregations[name]['count'] += 1

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar agregações: {e}")

    async def get_metric(self,
                        name: str,
                        start_time: datetime = None,
                        end_time: datetime = None) -> List[Dict]:
        """Obter valores da métrica"""
        try:
            if name not in self._metrics:
                return []

            metrics = self._metrics[name]
            
            # Filtrar por período
            if start_time or end_time:
                metrics = [
                    m for m in metrics
                    if (not start_time or m['timestamp'] >= start_time) and
                       (not end_time or m['timestamp'] <= end_time)
                ]
                
            return metrics

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter métrica: {e}")
            return []

    async def get_aggregations(self, name: str) -> Dict:
        """Obter agregações da métrica"""
        try:
            if name not in self._aggregations:
                return {}

            aggs = self._aggregations[name].copy()
            
            # Calcular média
            if 'sum' in aggs and 'count' in aggs:
                aggs['avg'] = aggs['sum'] / aggs['count']
                
            return aggs

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter agregações: {e}")
            return {}

    async def _cleanup_loop(self):
        """Loop de limpeza de métricas antigas"""
        try:
            while True:
                try:
                    cutoff = datetime.utcnow() - timedelta(
                        days=self._retention_days
                    )
                    
                    for name in list(self._metrics.keys()):
                        self._metrics[name] = [
                            m for m in self._metrics[name]
                            if m['timestamp'] > cutoff
                        ]
                        
                    await asyncio.sleep(3600)  # Executar a cada hora
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no cleanup: {e}")
                    await asyncio.sleep(300)  # 5 minutos em caso de erro
                    
        except asyncio.CancelledError:
            pass

    async def export_metrics(self, filename: str) -> bool:
        """Exportar métricas para arquivo"""
        try:
            data = {
                'metrics': {
                    name: [
                        {
                            'value': m['value'],
                            'timestamp': m['timestamp'].isoformat()
                        }
                        for m in metrics
                    ]
                    for name, metrics in self._metrics.items()
                },
                'aggregations': self._aggregations,
                'exported_at': datetime.utcnow().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            self.logger.logger.info(f"Métricas exportadas para {filename}")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao exportar métricas: {e}")
            return False

    async def import_metrics(self, filename: str) -> bool:
        """Importar métricas de arquivo"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            # Importar métricas
            for name, metrics in data['metrics'].items():
                self._metrics[name] = [
                    {
                        'value': m['value'],
                        'timestamp': datetime.fromisoformat(m['timestamp'])
                    }
                    for m in metrics
                ]
                
            # Importar agregações
            self._aggregations = defaultdict(
                dict,
                data['aggregations']
            )
            
            self.logger.logger.info(f"Métricas importadas de {filename}")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao importar métricas: {e}")
            return False

    async def get_stats(self) -> Dict:
        """Obter estatísticas gerais"""
        try:
            stats = {
                'total_metrics': len(self._metrics),
                'total_points': sum(
                    len(metrics)
                    for metrics in self._metrics.values()
                ),
                'metrics': {}
            }
            
            for name in self._metrics:
                stats['metrics'][name] = {
                    'points': len(self._metrics[name]),
                    'first_timestamp': min(
                        m['timestamp']
                        for m in self._metrics[name]
                    ).isoformat(),
                    'last_timestamp': max(
                        m['timestamp']
                        for m in self._metrics[name]
                    ).isoformat(),
                    'aggregations': await self.get_aggregations(name)
                }
                
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def set_retention(self, days: int):
        """Definir período de retenção das métricas"""
        try:
            if days < 1:
                raise ValueError("Retenção deve ser maior que 0")
                
            self._retention_days = days
            self.logger.logger.info(f"Retenção definida para {days} dias")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir retenção: {e}")

    async def clear_metrics(self, name: str = None):
        """Limpar métricas"""
        try:
            if name:
                if name in self._metrics:
                    del self._metrics[name]
                if name in self._aggregations:
                    del self._aggregations[name]
            else:
                self._metrics.clear()
                self._aggregations.clear()
                
            self.logger.logger.info(
                f"Métricas limpas: {name or 'todas'}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar métricas: {e}")