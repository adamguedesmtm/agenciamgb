"""
RCON Manager
Author: adamguedesmtm
Created: 2025-02-21 13:51:45
"""

import asyncio
import valve.rcon
from typing import Optional, Dict, List
from .logger import Logger
from .metrics import MetricsManager

class RCONManager:
    def __init__(self, 
                 host: str, 
                 port: int, 
                 password: str,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.host = host
        self.port = port
        self.password = password
        self.logger = logger or Logger('rcon_manager')
        self.metrics = metrics
        self._connection = None
        self._lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Conectar ao servidor via RCON"""
        try:
            async with self._lock:
                if self._connection:
                    return True
                
                self._connection = valve.rcon.RCON(
                    (self.host, self.port),
                    self.password
                )
                self._connection.connect()
                
                if self.metrics:
                    await self.metrics.record_command('rcon_connect')
                
                self.logger.logger.info(f"RCON conectado a {self.host}:{self.port}")
                return True
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao conectar RCON: {e}")
            return False

    async def disconnect(self):
        """Desconectar do servidor"""
        try:
            async with self._lock:
                if self._connection:
                    self._connection.close()
                    self._connection = None
                    
                    if self.metrics:
                        await self.metrics.record_command('rcon_disconnect')
                    
                    self.logger.logger.info("RCON desconectado")
                    
        except Exception as e:
            self.logger.logger.error(f"Erro ao desconectar RCON: {e}")

    async def execute(self, command: str) -> Optional[str]:
        """Executar comando RCON"""
        try:
            if not await self.connect():
                return None
                
            async with self._lock:
                response = self._connection.execute(command)
                
                if self.metrics:
                    await self.metrics.record_command('rcon_execute')
                
                return response.decode('utf-8')
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar comando RCON: {e}")
            await self.disconnect()
            return None

    async def get_status(self) -> Optional[Dict]:
        """Obter status do servidor"""
        try:
            response = await self.execute("status")
            if not response:
                return None
                
            # Parsear resposta
            status = {
                'hostname': '',
                'version': '',
                'map': '',
                'players': [],
                'players_online': 0,
                'max_players': 0
            }
            
            for line in response.splitlines():
                if 'hostname:' in line:
                    status['hostname'] = line.split('hostname:')[1].strip()
                elif 'version' in line:
                    status['version'] = line.split('version')[1].strip()
                elif 'map' in line:
                    status['map'] = line.split('map:')[1].strip()
                elif '#' in line and 'STEAM' in line:
                    status['players'].append(self._parse_player(line))
                    
            status['players_online'] = len(status['players'])
            
            if self.metrics:
                await self.metrics.update_server_status(
                    'players_online',
                    status['players_online']
                )
            
            return status
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            return None

    def _parse_player(self, line: str) -> Dict:
        """Parsear informações do jogador da linha de status"""
        try:
            parts = line.split()
            return {
                'id': parts[1],
                'name': ' '.join(parts[2:-7]),
                'steamid': parts[-7],
                'ping': int(parts[-2]),
                'loss': int(parts[-1].rstrip('%')),
                'state': parts[-3]
            }
        except:
            return {}

    async def change_map(self, map_name: str) -> bool:
        """Trocar mapa do servidor"""
        try:
            response = await self.execute(f"changelevel {map_name}")
            success = response and "Changed map" in response
            
            if success and self.metrics:
                await self.metrics.record_command('map_change')
                
            return success
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao trocar mapa: {e}")
            return False

    async def send_message(self, message: str) -> bool:
        """Enviar mensagem para o servidor"""
        try:
            response = await self.execute(f"say {message}")
            return response is not None
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao enviar mensagem: {e}")
            return False

    async def kick_player(self, steam_id: str, reason: str = "") -> bool:
        """Kickar jogador do servidor"""
        try:
            response = await self.execute(f"kickid {steam_id} {reason}")
            success = response and "Kicked" in response
            
            if success and self.metrics:
                await self.metrics.record_command('player_kick')
                
            return success
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao kickar jogador: {e}")
            return False

    async def set_password(self, password: str) -> bool:
        """Definir senha do servidor"""
        try:
            response = await self.execute(f"sv_password {password}")
            return response is not None
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao definir senha: {e}")
            return False