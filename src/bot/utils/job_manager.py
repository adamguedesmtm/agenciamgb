"""
Job Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:41:48
"""

import asyncio
import aiocron
from datetime import datetime
from typing import Callable, Dict, Optional
from .logger import Logger

class JobManager:
    def __init__(self):
        self.logger = Logger('job_manager')
        self._jobs: Dict[str, aiocron.Cron] = {}
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._job_histories: Dict[str, list] = {}

    async def add_job(self, 
                     name: str, 
                     func: Callable, 
                     cron: str, 
                     args: tuple = None,
                     kwargs: dict = None):
        """
        Adicionar novo job
        cron: expressão cron (ex: '*/5 * * * *' para cada 5 minutos)
        """
        try:
            if name in self._jobs:
                raise ValueError(f"Job {name} já existe")

            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}

            async def wrapper():
                try:
                    self._running_jobs[name] = asyncio.current_task()
                    start_time = datetime.now()
                    
                    result = await func(*args, **kwargs)
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    self._add_to_history(name, {
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'status': 'success',
                        'result': result
                    })
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no job {name}: {e}")
                    self._add_to_history(name, {
                        'start_time': start_time,
                        'end_time': datetime.now(),
                        'status': 'error',
                        'error': str(e)
                    })
                finally:
                    if name in self._running_jobs:
                        del self._running_jobs[name]

            self._jobs[name] = aiocron.crontab(cron, func=wrapper)
            self.logger.logger.info(f"Job {name} adicionado com cron: {cron}")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar job: {e}")
            raise

    async def remove_job(self, name: str):
        """Remover job"""
        try:
            if name in self._jobs:
                self._jobs[name].stop()
                del self._jobs[name]
                
                if name in self._running_jobs:
                    self._running_jobs[name].cancel()
                    
                self.logger.logger.info(f"Job {name} removido")
            else:
                raise ValueError(f"Job {name} não encontrado")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover job: {e}")
            raise

    async def get_job_status(self, name: str) -> Optional[Dict]:
        """Obter status do job"""
        try:
            if name not in self._jobs:
                return None

            is_running = name in self._running_jobs
            history = self._job_histories.get(name, [])
            last_run = history[-1] if history else None
            
            return {
                'name': name,
                'is_running': is_running,
                'last_run': last_run,
                'total_runs': len(history),
                'success_runs': sum(
                    1 for h in history if h['status'] == 'success'
                ),
                'error_runs': sum(
                    1 for h in history if h['status'] == 'error'
                )
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status do job: {e}")
            return None

    def _add_to_history(self, name: str, data: Dict):
        """Adicionar execução ao histórico"""
        try:
            if name not in self._job_histories:
                self._job_histories[name] = []
                
            # Manter apenas últimas 100 execuções
            history = self._job_histories[name]
            history.append(data)
            if len(history) > 100:
                history.pop(0)
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar ao histórico: {e}")

    async def get_all_jobs(self) -> Dict[str, Dict]:
        """Obter status de todos os jobs"""
        try:
            return {
                name: await self.get_job_status(name)
                for name in self._jobs
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter todos os jobs: {e}")
            return {}

    async def run_job_now(self, name: str):
        """Executar job imediatamente"""
        try:
            if name not in self._jobs:
                raise ValueError(f"Job {name} não encontrado")
                
            if name in self._running_jobs:
                raise ValueError(f"Job {name} já está em execução")
                
            await self._jobs[name].func()
            self.logger.logger.info(f"Job {name} executado manualmente")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar job: {e}")
            raise

    async def pause_job(self, name: str):
        """Pausar job"""
        try:
            if name not in self._jobs:
                raise ValueError(f"Job {name} não encontrado")
                
            self._jobs[name].stop()
            self.logger.logger.info(f"Job {name} pausado")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao pausar job: {e}")
            raise

    async def resume_job(self, name: str):
        """Retomar job"""
        try:
            if name not in self._jobs:
                raise ValueError(f"Job {name} não encontrado")
                
            self._jobs[name].start()
            self.logger.logger.info(f"Job {name} retomado")
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao retomar job: {e}")
            raise

    async def clear_job_history(self, name: str = None):
        """Limpar histórico de jobs"""
        try:
            if name:
                if name in self._job_histories:
                    self._job_histories[name] = []
                    self.logger.logger.info(f"Histórico do job {name} limpo")
            else:
                self._job_histories.clear()
                self.logger.logger.info("Histórico de todos os jobs limpo")
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar histórico: {e}")
            raise