"""
RCON Manager for CS2 Server Communication
Author: adamguedesmtm
Created: 2025-02-21 14:39:11
"""

import valve.rcon
from typing import Optional
import asyncio
from .logger import Logger

class RconManager:
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 27015,
                 password: str = None,
                 logger: Optional[Logger] = None):
        self.host = host
        self.port = port
        self.password = password
        self.logger = logger or Logger('rcon')
        self._rcon = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Estabelecer conexão RCON"""
        try:
            if not self._rcon:
                self._rcon = valve.rcon.RCON(self.host, self.port, self.password)
                self._rcon.connect()
                self.logger.info("Conexão RCON estabelecida")
        except Exception as e:
            self.logger.error(f"Erro ao conectar RCON: {e}")
            raise

    async def execute(self, command: str) -> str:
        """Executar comando RCON"""
        try:
            async with self._lock:
                if not self._rcon:
                    await self.connect()
                response = self._rcon.execute(command)
                return response.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Erro ao executar comando RCON: {e}")
            await self.connect()  # Tentar reconectar
            return ""

    async def get_server_ip(self) -> str:
        """Obter IP do servidor"""
        try:
            response = await self.execute('status')
            for line in response.split('\n'):
                if 'udp/ip' in line.lower():
                    return line.split()[1]
            return self.host
        except:
            return self.host

    async def get_server_port(self) -> int:
        """Obter porta do servidor"""
        return self.port

    async def get_gotv_port(self) -> int:
        """Obter porta GOTV"""
        try:
            response = await self.execute('tv_status')
            for line in response.split('\n'):
                if 'port' in line.lower():
                    return int(line.split()[1])
            return self.port + 5
        except:
            return self.port + 5

    async def get_connect_command(self) -> str:
        """Obter comando de conexão"""
        ip = await self.get_server_ip()
        return f"connect {ip}:{self.port}"

    async def get_player_name(self, steam_id: str) -> str:
        """Obter nome do jogador pelo Steam ID"""
        try:
            response = await self.execute('status')
            for line in response.split('\n'):
                if steam_id in line:
                    parts = line.split()
                    return ' '.join(parts[2:-2])  # Nome está entre o índice 2 e os últimos 2 campos
            return "Unknown"
        except:
            return "Unknown"

    def __del__(self):
        """Cleanup ao destruir objeto"""
        if self._rcon:
            try:
                self._rcon.close()
            except:
                pass