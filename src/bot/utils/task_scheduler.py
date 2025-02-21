"""
Task Scheduler for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 06:05:50
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import uuid
from .logger import Logger

class Task:
    def __init__(self, 
                 func: Callable,
                 args: tuple = None,
                 kwargs: dict = None,
                 interval: int = None,
                 cron: str = None):
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.interval = interval
        self.cron = cron
        self.next_run = None
        self.last_run = None
        self.running = False
        self.error = None
        self.runs = 0

class TaskScheduler:
    def __init__(self):
        self.logger = Logger('task_scheduler')
        self._tasks: Dict[str, Task] = {}
        self._running = False
        self._main_task = None

    async def start(self):
        """Iniciar scheduler"""
        try:
            if self._running:
                return

            self._running = True
            self._main_task = asyncio.create_task(self._scheduler_loop())
            self.logger.logger.info("Task scheduler iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar scheduler: {e}")

    async def stop(self):
        """Parar scheduler"""
        try:
            self._running = False
            if self._main_task:
                self._main_task.cancel()
                try:
                    await self._main_task
                except asyncio.CancelledError:
                    pass
            self.logger.logger.info("Task scheduler parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar scheduler: {e}")

    async def add_task(self,
                      func: Callable,
                      args: tuple = None,
                      kwargs: dict = None,
                      interval: int = None,
                      cron: str = None) -> str:
        """
        Adicionar nova tarefa
        func: Função a ser executada
        args: Argumentos posicionais
        kwargs: Argumentos nomeados
        interval: Intervalo em segundos
        cron: Expressão cron (ex: "0 0 * * *")
        """
        try:
            if not interval and not cron:
                raise ValueError("Deve especificar interval ou cron")

            task = Task(func, args, kwargs, interval, cron)
            
            # Calcular próxima execução
            if interval:
                task.next_run = datetime.now() + timedelta(seconds=interval)
            else:
                task.next_run = self._get_next_cron_run(cron)

            self._tasks[task.id] = task
            self.logger.logger.info(f"Tarefa {task.id} adicionada")
            return task.id

        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar tarefa: {e}")
            return None

    async def remove_task(self, task_id: str) -> bool:
        """Remover tarefa"""
        try:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self.logger.logger.info(f"Tarefa {task_id} removida")
                return True
            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao remover tarefa: {e}")
            return False

    async def _scheduler_loop(self):
        """Loop principal do scheduler"""
        try:
            while self._running:
                try:
                    now = datetime.now()
                    
                    # Verificar tarefas a serem executadas
                    for task in list(self._tasks.values()):
                        if (task.next_run and 
                            now >= task.next_run and 
                            not task.running):
                            # Executar tarefa em background
                            asyncio.create_task(self._run_task(task))
                            
                    await asyncio.sleep(1)  # Verificar a cada segundo
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no scheduler loop: {e}")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            pass

    async def _run_task(self, task: Task):
        """Executar tarefa individual"""
        try:
            task.running = True
            task.last_run = datetime.now()
            task.runs += 1
            
            try:
                result = task.func(*task.args, **task.kwargs)
                if asyncio.iscoroutine(result):
                    await result
                task.error = None
            except Exception as e:
                task.error = str(e)
                self.logger.logger.error(f"Erro ao executar tarefa {task.id}: {e}")
                
            finally:
                task.running = False
                
                # Calcular próxima execução
                if task.interval:
                    task.next_run = datetime.now() + timedelta(seconds=task.interval)
                elif task.cron:
                    task.next_run = self._get_next_cron_run(task.cron)

        except Exception as e:
            self.logger.logger.error(f"Erro ao executar tarefa: {e}")

    def _get_next_cron_run(self, cron: str) -> Optional[datetime]:
        """Calcular próxima execução baseada em cron"""
        try:
            from croniter import croniter
            base = datetime.now()
            return croniter(cron, base).get_next(datetime)
        except Exception as e:
            self.logger.logger.error(f"Erro ao calcular próxima execução: {e}")
            return None

    async def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Obter informações da tarefa"""
        try:
            if task_id not in self._tasks:
                return None

            task = self._tasks[task_id]
            return {
                'id': task.id,
                'function': task.func.__name__,
                'args': task.args,
                'kwargs': task.kwargs,
                'interval': task.interval,
                'cron': task.cron,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'running': task.running,
                'error': task.error,
                'runs': task.runs
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info da tarefa: {e}")
            return None

    async def list_tasks(self) -> List[Dict]:
        """Listar todas as tarefas"""
        try:
            return [
                await self.get_task_info(task_id)
                for task_id in self._tasks
            ]
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar tarefas: {e}")
            return []

    async def pause_task(self, task_id: str) -> bool:
        """Pausar tarefa temporariamente"""
        try:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]
            task.next_run = None
            self.logger.logger.info(f"Tarefa {task_id} pausada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao pausar tarefa: {e}")
            return False

    async def resume_task(self, task_id: str) -> bool:
        """Retomar tarefa pausada"""
        try:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]
            if task.interval:
                task.next_run = datetime.now() + timedelta(seconds=task.interval)
            elif task.cron:
                task.next_run = self._get_next_cron_run(task.cron)
                
            self.logger.logger.info(f"Tarefa {task_id} retomada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao retomar tarefa: {e}")
            return False

    async def update_task(self,
                         task_id: str,
                         interval: int = None,
                         cron: str = None) -> bool:
        """Atualizar configuração da tarefa"""
        try:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]
            
            if interval is not None:
                task.interval = interval
                task.cron = None
                task.next_run = datetime.now() + timedelta(seconds=interval)
            elif cron is not None:
                task.interval = None
                task.cron = cron
                task.next_run = self._get_next_cron_run(cron)
                
            self.logger.logger.info(f"Tarefa {task_id} atualizada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar tarefa: {e}")
            return False

    async def run_task_now(self, task_id: str) -> bool:
        """Executar tarefa imediatamente"""
        try:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]
            if not task.running:
                await self._run_task(task)
                return True
            return False

        except Exception as e:
            self.logger.logger.error(f"Erro ao executar tarefa: {e}")
            return False

    async def clear_tasks(self):
        """Remover todas as tarefas"""
        try:
            self._tasks.clear()
            self.logger.logger.info("Todas as tarefas removidas")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar tarefas: {e}")

    def get_next_runs(self, limit: int = 10) -> List[Dict]:
        """Obter próximas execuções agendadas"""
        try:
            tasks = [
                {
                    'id': task.id,
                    'function': task.func.__name__,
                    'next_run': task.next_run
                }
                for task in self._tasks.values()
                if task.next_run is not None
            ]
            
            return sorted(
                tasks,
                key=lambda x: x['next_run']
            )[:limit]

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter próximas execuções: {e}")
            return []
        