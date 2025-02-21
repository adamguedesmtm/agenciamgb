"""
Metrics Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:17:58
"""

from typing import Dict, Any, Optional
import time
import json
import os
from datetime import datetime

class MetricsManager:
    def __init__(self, metrics_dir: str = "/var/log/cs2server/metrics"):
        self.metrics_dir = metrics_dir
        os.makedirs(metrics_dir, exist_ok=True)
        
        self._current_file = None
        self._current_date = None
        self._metrics_buffer = []
        self._buffer_size = 100
        
    async def record_metric(self,
                          name: str,
                          value: float,
                          labels: Optional[Dict[str, str]] = None):
        """
        Registrar métrica
        
        Args:
            name: Nome da métrica
            value: Valor
            labels: Labels adicionais
        """
        try:
            current_date = datetime.utcnow().date()
            
            # Rotacionar arquivo se necessário
            if current_date != self._current_date:
                await self._rotate_file(current_date)
            
            # Criar entrada
            metric = {
                'timestamp': datetime.utcnow().isoformat(),
                'name': name,
                'value': value,
                'labels': labels or {}
            }
            
            # Adicionar ao buffer
            self._metrics_buffer.append(metric)
            
            # Flush se buffer cheio
            if len(self._metrics_buffer) >= self._buffer_size:
                await self._flush_buffer()
                
        except Exception as e:
            print(f"Erro ao registrar métrica: {e}")
            
    async def _rotate_file(self, new_date):
        """Rotacionar arquivo de métricas"""
        try:
            # Flush buffer atual
            if self._metrics_buffer:
                await self._flush_buffer()
                
            # Fechar arquivo atual
            if self._current_file:
                self._current_file.close()
                
            # Abrir novo arquivo
            filename = f"{self.metrics_dir}/metrics_{new_date}.json"
            self._current_file = open(filename, 'a')
            self._current_date = new_date
            
        except Exception as e:
            print(f"Erro ao rotacionar métricas: {e}")
            
    async def _flush_buffer(self):
        """Flush do buffer para arquivo"""
        try:
            if not self._metrics_buffer:
                return
                
            # Escrever cada métrica
            for metric in self._metrics_buffer:
                self._current_file.write(json.dumps(metric) + '\n')
                
            self._current_file.flush()
            self._metrics_buffer.clear()
            
        except Exception as e:
            print(f"Erro ao flush métricas: {e}")
            
    async def get_metrics(self,
                         start_date: datetime,
                         end_date: datetime,
                         metric_name: Optional[str] = None) -> list:
        """
        Obter métricas em intervalo
        
        Args:
            start_date: Data inicial
            end_date: Data final
            metric_name: Filtrar por nome
            
        Returns:
            Lista de métricas
        """
        metrics = []
        try:
            # Flush buffer atual
            await self._flush_buffer()
            
            # Para cada arquivo no intervalo
            current = start_date.date()
            while current <= end_date.date():
                filename = f"{self.metrics_dir}/metrics_{current}.json"
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        for line in f:
                            metric = json.loads(line)
                            
                            # Filtrar por nome se especificado
                            if metric_name and metric['name'] != metric_name:
                                continue
                                
                            # Filtrar por timestamp
                            ts = datetime.fromisoformat(metric['timestamp'])
                            if start_date <= ts <= end_date:
                                metrics.append(metric)
                                
                current = current.next_day()
                
        except Exception as e:
            print(f"Erro ao obter métricas: {e}")
            
        return metrics