"""
Job Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:47:01
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import uuid
from .logger import Logger
from .metrics import MetricsManager

class Job:
    def __init__(self,
                 func: Callable,
                 args: tuple = None,
                 kwargs: dict = None,
                 max_retries: int = 3,
                 retry_delay: int = 5):
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retries = 0
        self.status = 'pending'
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.finished_at = None
        self.next_retry_at = None

class JobManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('job_manager')
        self.metrics = metrics_manager
        self._jobs: Dict[str, Job] = {}
        self._queue: List[str] = []
        self._processing: Dict[str, asyncio.Task] = {}
        self._max_concurrent = 5

    async def submit_job(self,
                        func: Callable,
                        args: tuple = None,
                        kwargs: dict = None,
                        max_retries: int = 3,
                        retry_delay: int = 5) -> str:
        """Submeter novo job"""
        try:
            job = Job(func, args, kwargs, max_retries, retry_delay)
            self._jobs[job.id] = job
            self._queue.append(job.id)
            
            # Registrar métrica
            await self.metrics.record_metric('jobs.submitted', 1)
            
            # Iniciar processamento se possível
            await self._process_queue()
            
            self.logger.logger.info(f"Job {job.id} submetido")
            return job.id

        except Exception as e:
            self.logger.logger.error(f"Erro ao submeter job: {e}")
            return None

    async def _process_queue(self):
        """Processar fila de jobs"""
        try:
            while (len(self._processing) < self._max_concurrent and
                   self._queue):
                job_id = self._queue[0]
                job = self._jobs[job_id]
                
                if job.status == 'pending':
                    # Criar task para executar job
                    task = asyncio.create_task(
                        self._execute_job(job)
                    )
                    self._processing[job_id] = task
                    self._queue.pop(0)
                    
                elif job.status == 'failed' and job.next_retry_at:
                    # Verificar se já pode tentar novamente
                    if datetime.utcnow() >= job.next_retry_at:
                        task = asyncio.create_task(
                            self._execute_job(job)
                        )
                        self._processing[job_id] = task
                        self._queue.pop(0)
                    else:
                        break

        except Exception as e:
            self.logger.logger.error(f"Erro ao processar fila: {e}")

    async def _execute_job(self, job: Job):
        """Executar job individual"""
        try:
            job.status = 'running'
            job.started_at = datetime.utcnow()
            
            try:
                # Executar função
                result = job.func(*job.args, **job.kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                    
                job.result = result
                job.status = 'completed'
                job.error = None
                
                # Registrar métrica de sucesso
                await self.metrics.record_metric('jobs.completed', 1)
                
            except Exception as e:
                job.error = str(e)
                
                # Tentar novamente se possível
                if job.retries < job.max_retries:
                    job.retries += 1
                    job.status = 'failed'
                    job.next_retry_at = datetime.utcnow() + timedelta(
                        seconds=job.retry_delay * (2 ** (job.retries - 1))
                    )
                    self._queue.append(job.id)
                    
                    # Registrar métrica de retry
                    await self.metrics.record_metric('jobs.retried', 1)
                    
                else:
                    job.status = 'failed'
                    # Registrar métrica de falha
                    await self.metrics.record_metric('jobs.failed', 1)
                    
            finally:
                job.finished_at = datetime.utcnow()
                if job.id in self._processing:
                    del self._processing[job.id]
                    
                # Processar próximo job
                await self._process_queue()

        except Exception as e:
            self.logger.logger.error(f"Erro ao executar job: {e}")

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Obter status do job"""
        try:
            if job_id not in self._jobs:
                return None

            job = self._jobs[job_id]
            return {
                'id': job.id,
                'status': job.status,
                'retries': job.retries,
                'max_retries': job.max_retries,
                'error': job.error,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'finished_at': job.finished_at.isoformat() if job.finished_at else None,
                'next_retry': job.next_retry_at.isoformat() if job.next_retry_at else None,
                'result': job.result
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status do job: {e}")
            return None

    async def list_jobs(self, 
                       status: str = None,
                       limit: int = None) -> List[Dict]:
        """Listar jobs"""
        try:
            jobs = []
            for job_id, job in self._jobs.items():
                if status and job.status != status:
                    continue
                    
                jobs.append({
                    'id': job.id,
                    'status': job.status,
                    'retries': job.retries,
                    'created_at': job.created_at.isoformat()
                })
                
            # Ordenar por data de criação
            jobs.sort(key=lambda x: x['created_at'], reverse=True)
            
            if limit:
                jobs = jobs[:limit]
                
            return jobs

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar jobs: {e}")
            return []

    async def cancel_job(self, job_id: str) -> bool:
        """Cancelar job"""
        try:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]
            
            # Remover da fila se estiver pendente
            if job_id in self._queue:
                self._queue.remove(job_id)
                
            # Cancelar se estiver em execução
            if job_id in self._processing:
                self._processing[job_id].cancel()
                try:
                    await self._processing[job_id]
                except asyncio.CancelledError:
                    pass
                del self._processing[job_id]
                
            job.status = 'cancelled'
            job.finished_at = datetime.utcnow()
            
            # Registrar métrica
            await self.metrics.record_metric('jobs.cancelled', 1)
            
            self.logger.logger.info(f"Job {job_id} cancelado")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao cancelar job: {e}")
            return False

    async def retry_job(self, job_id: str) -> bool:
        """Forçar retry do job"""
        try:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]
            
            if job.status != 'failed':
                return False
                
            # Resetar estado do job
            job.status = 'pending'
            job.retries = 0
            job.error = None
            job.result = None
            job.started_at = None
            job.finished_at = None
            job.next_retry_at = None
            
            # Adicionar na fila
            if job_id not in self._queue:
                self._queue.append(job_id)
                
            # Iniciar processamento
            await self._process_queue()
            
            self.logger.logger.info(f"Job {job_id} agendado para retry")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao agendar retry: {e}")
            return False

    async def clear_completed(self, max_age: int = None) -> int:
        """Limpar jobs completados"""
        try:
            count = 0
            now = datetime.utcnow()
            
            for job_id in list(self._jobs.keys()):
                job = self._jobs[job_id]
                
                if job.status != 'completed':
                    continue
                    
                if (max_age and job.finished_at and
                    (now - job.finished_at).total_seconds() > max_age):
                    del self._jobs[job_id]
                    count += 1
                    
            self.logger.logger.info(f"{count} jobs removidos")
            return count

        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar jobs: {e}")
            return 0

    async def get_queue_info(self) -> Dict:
        """Obter informações da fila"""
        try:
            return {
                'queued': len(self._queue),
                'processing': len(self._processing),
                'max_concurrent': self._max_concurrent,
                'status_counts': {
                    status: len([
                        j for j in self._jobs.values()
                        if j.status == status
                    ])
                    for status in ['pending', 'running', 'completed', 
                                 'failed', 'cancelled']
                }
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da fila: {e}")
            return {}

    def set_max_concurrent(self, value: int):
        """Definir número máximo de jobs concorrentes"""
        try:
            if value < 1:
                raise ValueError("Valor deve ser maior que 0")
                
            self._max_concurrent = value
            self.logger.logger.info(f"Max concurrent definido para {value}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir max concurrent: {e}")

    async def get_job_metrics(self) -> Dict:
        """Obter métricas dos jobs"""
        try:
            now = datetime.utcnow()
            
            metrics = {
                'total_jobs': len(self._jobs),
                'total_queued': len(self._queue),
                'total_processing': len(self._processing),
                'avg_wait_time': 0,
                'avg_processing_time': 0,
                'success_rate': 0
            }
            
            completed = 0
            total_wait = 0
            total_proc = 0
            
            for job in self._jobs.values():
                if job.started_at:
                    wait_time = (job.started_at - job.created_at).total_seconds()
                    total_wait += wait_time
                    
                if job.finished_at and job.started_at:
                    proc_time = (job.finished_at - job.started_at).total_seconds()
                    total_proc += proc_time
                    
                if job.status == 'completed':
                    completed += 1
                    
            if self._jobs:
                metrics['avg_wait_time'] = total_wait / len(self._jobs)
                metrics['avg_processing_time'] = total_proc / len(self._jobs)
                metrics['success_rate'] = (completed / len(self._jobs)) * 100
                
            return metrics

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter métricas: {e}")
            return {}

    async def pause_queue(self):
        """Pausar processamento da fila"""
        try:
            self._max_concurrent = 0
            self.logger.logger.info("Fila pausada")
        except Exception as e:
            self.logger.logger.error(f"Erro ao pausar fila: {e}")

    async def resume_queue(self, max_concurrent: int = None):
        """Retomar processamento da fila"""
        try:
            self._max_concurrent = max_concurrent or 5
            await self._process_queue()
            self.logger.logger.info("Fila retomada")
        except Exception as e:
            self.logger.logger.error(f"Erro ao retomar fila: {e}")

    async def clear_queue(self):
        """Limpar fila de jobs pendentes"""
        try:
            count = len(self._queue)
            self._queue.clear()
            self.logger.logger.info(f"{count} jobs removidos da fila")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar fila: {e}")