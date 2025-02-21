"""
Connection Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 07:35:11
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import uuid
from .logger import Logger
from .metrics import MetricsManager

class Connection:
    def __init__(self, 
                 conn_id: str,
                 user_id: str,
                 conn_type: str,
                 metadata: Dict = None):
        self.id = conn_id
        self.user_id = user_id
        self.type = conn_type
        self.metadata = metadata or {}
        self.connected_at = datetime.utcnow()
        self.last_activity = self.connected_at
        self.disconnected_at = None
        self.status = 'active'
        self.total_messages = 0
        self.total_errors = 0
        self.ping = 0.0

class ConnectionManager:
    def __init__(self, metrics_manager: MetricsManager):
        self.logger = Logger('connection_manager')
        self.metrics = metrics_manager
        self._connections: Dict[str, Connection] = {}
        self._user_connections: Dict[str, Set[str]] = {}
        self._type_connections: Dict[str, Set[str]] = {}
        self._heartbeat_interval = 30  # segundos
        self._timeout = 90  # segundos
        self._cleanup_task = None
        self._running = False

    async def start(self):
        """Iniciar gerenciador de conexões"""
        try:
            self._running = True
            self._cleanup_task = asyncio.create_task(
                self._cleanup_loop()
            )
            self.logger.logger.info("Connection manager iniciado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao iniciar: {e}")

    async def stop(self):
        """Parar gerenciador de conexões"""
        try:
            self._running = False
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            self.logger.logger.info("Connection manager parado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao parar: {e}")

    async def register_connection(self,
                                user_id: str,
                                conn_type: str,
                                metadata: Dict = None) -> Optional[str]:
        """Registrar nova conexão"""
        try:
            conn_id = str(uuid.uuid4())
            
            conn = Connection(
                conn_id,
                user_id,
                conn_type,
                metadata
            )
            
            self._connections[conn_id] = conn
            
            # Registrar em índices
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(conn_id)
            
            if conn_type not in self._type_connections:
                self._type_connections[conn_type] = set()
            self._type_connections[conn_type].add(conn_id)
            
            # Registrar métricas
            await self.metrics.record_metric(
                f"connections.{conn_type}.connected",
                1
            )
            
            self.logger.logger.info(
                f"Nova conexão {conn_id} para usuário {user_id}"
            )
            return conn_id

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar conexão: {e}")
            return None

    async def close_connection(self, conn_id: str) -> bool:
        """Fechar conexão"""
        try:
            if conn_id not in self._connections:
                return False

            conn = self._connections[conn_id]
            
            # Atualizar estado
            conn.status = 'closed'
            conn.disconnected_at = datetime.utcnow()
            
            # Remover dos índices
            self._user_connections[conn.user_id].remove(conn_id)
            if not self._user_connections[conn.user_id]:
                del self._user_connections[conn.user_id]
                
            self._type_connections[conn.type].remove(conn_id)
            if not self._type_connections[conn.type]:
                del self._type_connections[conn.type]
                
            # Registrar métricas
            await self.metrics.record_metric(
                f"connections.{conn.type}.disconnected",
                1
            )
            
            self.logger.logger.info(f"Conexão {conn_id} fechada")
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao fechar conexão: {e}")
            return False

    async def heartbeat(self, conn_id: str, ping: float = None) -> bool:
        """Atualizar heartbeat da conexão"""
        try:
            if conn_id not in self._connections:
                return False

            conn = self._connections[conn_id]
            now = datetime.utcnow()
            
            # Calcular tempo desde última atividade
            delta = (now - conn.last_activity).total_seconds()
            
            conn.last_activity = now
            if ping is not None:
                conn.ping = ping
                
            # Registrar métricas
            await self.metrics.record_metric(
                f"connections.{conn.type}.ping",
                ping or delta
            )
            
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro no heartbeat: {e}")
            return False

    async def _cleanup_loop(self):
        """Loop de limpeza de conexões inativas"""
        try:
            while self._running:
                try:
                    now = datetime.utcnow()
                    timeout = now - timedelta(
                        seconds=self._timeout
                    )
                    
                    # Verificar conexões inativas
                    for conn_id in list(self._connections.keys()):
                        conn = self._connections[conn_id]
                        
                        if (conn.status == 'active' and
                            conn.last_activity <= timeout):
                            # Fechar conexão inativa
                            await self.close_connection(conn_id)
                            
                    await asyncio.sleep(self._heartbeat_interval)
                    
                except Exception as e:
                    self.logger.logger.error(f"Erro no cleanup: {e}")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            pass

    async def get_connection_info(self, conn_id: str) -> Optional[Dict]:
        """Obter informações da conexão"""
        try:
            if conn_id not in self._connections:
                return None

            conn = self._connections[conn_id]
            return {
                'id': conn.id,
                'user_id': conn.user_id,
                'type': conn.type,
                'status': conn.status,
                'metadata': conn.metadata,
                'connected_at': conn.connected_at.isoformat(),
                'last_activity': conn.last_activity.isoformat(),
                'disconnected_at': (
                    conn.disconnected_at.isoformat()
                    if conn.disconnected_at else None
                ),
                'total_messages': conn.total_messages,
                'total_errors': conn.total_errors,
                'ping': conn.ping
            }

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter info: {e}")
            return None

    async def get_user_connections(self, 
                                 user_id: str,
                                 conn_type: str = None) -> List[Dict]:
        """Obter conexões do usuário"""
        try:
            if user_id not in self._user_connections:
                return []

            connections = []
            for conn_id in self._user_connections[user_id]:
                conn = self._connections[conn_id]
                if conn_type and conn.type != conn_type:
                    continue
                info = await self.get_connection_info(conn_id)
                if info:
                    connections.append(info)
                    
            return connections

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter conexões: {e}")
            return []

    async def list_connections(self,
                             conn_type: str = None,
                             status: str = None) -> List[Dict]:
        """Listar conexões"""
        try:
            connections = []
            
            if conn_type:
                if conn_type not in self._type_connections:
                    return []
                conn_ids = self._type_connections[conn_type]
            else:
                conn_ids = self._connections.keys()
                
            for conn_id in conn_ids:
                conn = self._connections[conn_id]
                if status and conn.status != status:
                    continue
                info = await self.get_connection_info(conn_id)
                if info:
                    connections.append(info)
                    
            return connections

        except Exception as e:
            self.logger.logger.error(f"Erro ao listar conexões: {e}")
            return []

    async def update_metadata(self,
                            conn_id: str,
                            metadata: Dict) -> bool:
        """Atualizar metadata da conexão"""
        try:
            if conn_id not in self._connections:
                return False

            conn = self._connections[conn_id]
            conn.metadata.update(metadata)
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar metadata: {e}")
            return False

    async def record_message(self,
                           conn_id: str,
                           error: bool = False) -> bool:
        """Registrar mensagem na conexão"""
        try:
            if conn_id not in self._connections:
                return False

            conn = self._connections[conn_id]
            conn.total_messages += 1
            if error:
                conn.total_errors += 1
                
            # Registrar métricas
            await self.metrics.record_metric(
                f"connections.{conn.type}.messages",
                1
            )
            if error:
                await self.metrics.record_metric(
                    f"connections.{conn.type}.errors",
                    1
                )
                
            return True

        except Exception as e:
            self.logger.logger.error(f"Erro ao registrar mensagem: {e}")
            return False

    def set_timeout(self, seconds: int):
        """Definir timeout de inatividade"""
        try:
            if seconds < 1:
                raise ValueError("Timeout deve ser maior que 0")
            self._timeout = seconds
            self.logger.logger.info(f"Timeout definido: {seconds}s")
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir timeout: {e}")

    def set_heartbeat_interval(self, seconds: int):
        """Definir intervalo de heartbeat"""
        try:
            if seconds < 1:
                raise ValueError("Intervalo deve ser maior que 0")
            self._heartbeat_interval = seconds
            self.logger.logger.info(f"Intervalo definido: {seconds}s")
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir intervalo: {e}")

    async def get_stats(self) -> Dict:
        """Obter estatísticas das conexões"""
        try:
            stats = {
                'total_connections': len(self._connections),
                'active_connections': len([
                    c for c in self._connections.values()
                    if c.status == 'active'
                ]),
                'users_connected': len(self._user_connections),
                'connection_types': {
                    ctype: len(conns)
                    for ctype, conns in self._type_connections.items()
                },
                'total_messages': sum(
                    c.total_messages
                    for c in self._connections.values()
                ),
                'total_errors': sum(
                    c.total_errors
                    for c in self._connections.values()
                ),
                'avg_ping': sum(
                    c.ping for c in self._connections.values()
                    if c.status == 'active'
                ) / len([
                    c for c in self._connections.values()
                    if c.status == 'active'
                ]) if any(
                    c.status == 'active'
                    for c in self._connections.values()
                ) else 0
            }
            return stats

        except Exception as e:
            self.logger.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}