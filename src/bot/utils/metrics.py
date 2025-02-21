"""
Metrics Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:41:48
"""

import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
from .logger import Logger

class MetricsManager:
    def __init__(self):
        self.logger = Logger('metrics_manager')
        self._metrics = defaultdict(list)
        self._gauges = {}
        self._counters = defaultdict(int)
        self._histograms = defaultdict(list)
        self._cleanup_task = None

    async def start(self):
        """Iniciar coleta de métricas"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Parar coleta de métricas"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def record_metric(self, name: str, value: float):
        """Registrar uma métrica com timestamp"""
        try:
            self._metrics[name].append({
                'value': value,
                'timestamp': datetime.now()
            })
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar métrica: {e}")

    async def set_gauge(self, name: str, value: float):
        """Definir valor de gauge"""
        try:
            self._gauges[name] = {
                'value': value,
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir gauge: {e}")

    async def increment_counter(self, name: str, value: int = 1):
        """Incrementar contador"""
        try:
            self._counters[name] += value
        except Exception as e:
            self.logger.logger.error(f"Erro ao incrementar contador: {e}")

    async def record_histogram(self, name: str, value: float):
        """Registrar valor em histograma"""
        try:
            self._histograms[name].append(value)
        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar histograma: {e}")

    async def get_metric_stats(self, name: str, window: int = 3600) -> Dict:
        """
        Obter estatísticas de uma métrica
        window: janela de tempo em segundos (padrão: 1 hora)
        """
        try:
            cutoff = datetime.now() - timedelta(seconds=window)
            values = [
                m['value'] for m in self._metrics[name]
                if m['timestamp'] > cutoff
            ]
            
            if not values:
                return {}

            return {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'count': len(values),
                'last': values[-1]
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    async def get_gauge(self, name: str) -> float:
        """Obter valor atual do gauge"""
        try:
            if name in self._gauges:
                return self._gauges[name]['value']
            return 0.0
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter gauge: {e}")
            return 0.0

    async def get_counter(self, name: str) -> int:
        """Obter valor do contador"""
        try:
            return self._counters[name]
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter contador: {e}")
            return 0

    async def get_histogram_stats(self, name: str) -> Dict:
        """Obter estatísticas do histograma"""
        try:
            values = self._histograms[name]
            if not values:
                return {}

            sorted_values = sorted(values)
            length = len(sorted_values)
            
            return {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / length,
                'median': sorted_values[length // 2],
                'p95': sorted_values[int(length * 0.95)],
                'p99': sorted_values[int(length * 0.99)],
                'count': length
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas do histograma: {e}")
            return {}

    async def _cleanup_loop(self):
        """Loop de limpeza de métricas antigas"""
        try:
            while True:
                await self._cleanup_old_metrics()
                await asyncio.sleep(300)  # Executar a cada 5 minutos
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.logger.error(f"Erro no loop de limpeza: {e}")

    async def _cleanup_old_metrics(self, max_age: int = 86400):
        """
        Limpar métricas mais antigas que max_age
        max_age: idade máxima em segundos (padrão: 24 horas)
        """
        try:
            cutoff = datetime.now() - timedelta(seconds=max_age)
            
            # Limpar métricas
            for name in self._metrics:
                self._metrics[name] = [
                    m for m in self._metrics[name]
                    if m['timestamp'] > cutoff
                ]

            # Limpar gauges
            for name in list(self._gauges.keys()):
                if self._gauges[name]['timestamp'] < cutoff:
                    del self._gauges[name]

            # Limpar histogramas (manter últimos 1000 valores)
            for name in self._histograms:
                if len(self._histograms[name]) > 1000:
                    self._histograms[name] = self._histograms[name][-1000:]
                    
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar métricas antigas: {e}")

    async def export_metrics(self) -> Dict:
        """Exportar todas as métricas"""
        try:
            return {
                'metrics': dict(self._metrics),
                'gauges': self._gauges,
                'counters': dict(self._counters),
                'histograms': dict(self._histograms)
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao exportar métricas: {e}")
            return {}

    async def import_metrics(self, data: Dict):
        """Importar métricas"""
        try:
            if 'metrics' in data:
                self._metrics.update(data['metrics'])
            if 'gauges' in data:
                self._gauges.update(data['gauges'])
            if 'counters' in data:
                self._counters.update(data['counters'])
            if 'histograms' in data:
                self._histograms.update(data['histograms'])
        except Exception as e:
            self.logger.logger.error(f"Erro ao importar métricas: {e}")
