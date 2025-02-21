"""
Server Monitor - CS2 Server Health Check and Backup System
Author: adamguedesmtm
Created: 2025-02-21 14:42:05
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict
from .logger import Logger
from .matchzy_manager import MatchzyManager
from .rcon_manager import RconManager

class ServerMonitor:
    def __init__(self, 
                 matchzy: MatchzyManager,
                 logger: Optional[Logger] = None,
                 backup_interval: int = 300,  # 5 minutos
                 health_check_interval: int = 60):  # 1 minuto
        
        self.matchzy = matchzy
        self.logger = logger or Logger('server_monitor')
        self.backup_interval = backup_interval
        self.health_check_interval = health_check_interval
        self.backup_path = 'backups'
        self.last_state = None
        
        # Criar diretório de backups se não existir
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)

    async def start_monitoring(self):
        """Iniciar monitoramento do servidor"""
        self.logger.info("Iniciando monitoramento do servidor")
        asyncio.create_task(self._backup_loop())
        asyncio.create_task(self._health_check_loop())

    async def _backup_loop(self):
        """Loop de backup periódico"""
        while True:
            try:
                await self._create_backup()
                await asyncio.sleep(self.backup_interval)
            except Exception as e:
                self.logger.error(f"Erro no loop de backup: {e}")
                await asyncio.sleep(30)  # Esperar antes de tentar novamente

    async def _health_check_loop(self):
        """Loop de verificação de saúde do servidor"""
        while True:
            try:
                await self._check_server_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Erro no health check: {e}")
                await asyncio.sleep(30)

    async def _create_backup(self):
        """Criar backup do estado atual"""
        try:
            if not self.matchzy.active_server:
                return

            current_state = {
                'timestamp': datetime.utcnow().isoformat(),
                'server_info': self.matchzy.active_server,
                'match_state': self.matchzy.match_state,
                'teams': {
                    team: list(players) 
                    for team, players in self.matchzy.teams.items()
                },
                'players': self.matchzy.players,
                'ready_players': list(self.matchzy.ready_players)
            }

            # Salvar apenas se houver mudanças
            if current_state != self.last_state:
                filename = f"{self.backup_path}/backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(current_state, f, indent=4)
                self.last_state = current_state
                self.logger.info(f"Backup criado: {filename}")

        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")

    async def _check_server_health(self):
        """Verificar saúde do servidor"""
        try:
            if not self.matchzy.active_server:
                return

            # Verificar conexão RCON
            response = await self.matchzy.rcon.execute('status')
            if not response:
                self.logger.error("Servidor não responde ao comando status")
                await self._handle_server_issue("RCON não responde")
                return

            # Verificar uso de CPU e memória
            server_stats = await self._get_server_stats()
            if server_stats['cpu'] > 90 or server_stats['memory'] > 90:
                self.logger.warning(f"Servidor sobrecarregado: CPU {server_stats['cpu']}%, MEM {server_stats['memory']}%")
                await self._handle_server_issue("Servidor sobrecarregado")

            # Verificar tempo de resposta
            if server_stats['response_time'] > 1000:  # mais de 1 segundo
                self.logger.warning(f"Latência alta: {server_stats['response_time']}ms")
                await self._handle_server_issue("Latência alta")

        except Exception as e:
            self.logger.error(f"Erro ao verificar saúde do servidor: {e}")

    async def _get_server_stats(self) -> Dict:
        """Obter estatísticas do servidor"""
        try:
            start_time = datetime.utcnow()
            response = await self.matchzy.rcon.execute('stats')
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            stats = {
                'cpu': 0,
                'memory': 0,
                'response_time': response_time
            }

            if response:
                lines = response.split('\n')
                for line in lines:
                    if 'CPU' in line:
                        stats['cpu'] = float(line.split(':')[1].strip().replace('%', ''))
                    elif 'Memory' in line:
                        stats['memory'] = float(line.split(':')[1].strip().replace('%', ''))

            return stats

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas do servidor: {e}")
            return {'cpu': 0, 'memory': 0, 'response_time': 9999}

    async def _handle_server_issue(self, issue: str):
        """Manipular problemas do servidor"""
        try:
            # Criar backup de emergência
            await self._create_backup()

            # Registrar problema
            self.logger.error(f"Problema detectado: {issue}")

            # Se servidor não responde, tentar reconectar RCON
            if issue == "RCON não responde":
                await self.matchzy.rcon.connect()

            # Se servidor está sobrecarregado, notificar admin
            elif issue == "Servidor sobrecarregado":
                # Aqui você pode implementar notificação para Discord ou outro sistema
                pass

        except Exception as e:
            self.logger.error(f"Erro ao manipular problema do servidor: {e}")

    async def restore_from_backup(self, backup_file: str) -> bool:
        """Restaurar estado do servidor de um backup"""
        try:
            if not os.path.exists(backup_file):
                return False

            with open(backup_file, 'r') as f:
                backup_data = json.load(f)

            # Restaurar estado
            self.matchzy.active_server = backup_data['server_info']
            self.matchzy.match_state = backup_data['match_state']
            
            # Restaurar times
            self.matchzy.teams = {
                team: set(players) 
                for team, players in backup_data['teams'].items()
            }
            
            self.matchzy.players = backup_data['players']
            self.matchzy.ready_players = set(backup_data['ready_players'])

            self.logger.info(f"Estado restaurado do backup: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            return False