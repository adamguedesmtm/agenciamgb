"""
RCON Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 13:19:44
"""

from typing import Optional
import valve.rcon
import asyncio
from .logger import Logger

class RCONManager:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.logger = Logger('rcon_manager')
        self._connection = None
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """
        Conectar ao servidor
        
        Returns:
            True se conectado com sucesso
        """
        try:
            self._connection = valve.rcon.RCON(
                (self.host, self.port),
                self.password
            )
            await self._connection.connect()
            self.logger.logger.info("RCON conectado")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro RCON connect: {e}")
            return False

    async def disconnect(self):
        """Desconectar do servidor"""
        if self._connection:
            try:
                await self._connection.disconnect()
                self._connection = None
                self.logger.logger.info("RCON desconectado")
            except Exception as e:
                self.logger.logger.error(f"Erro RCON disconnect: {e}")

    async def execute(self, command: str) -> Optional[str]:
        """
        Executar comando RCON
        
        Args:
            command: Comando a executar
            
        Returns:
            Resposta do servidor ou None se erro
        """
        try:
            async with self._lock:
                if not self._connection:
                    if not await self.connect():
                        return None

                response = await self._connection.execute(command)
                self.logger.logger.debug(f"RCON cmd: {command} -> {response}")
                return response

        except valve.rcon.RCONError as e:
            self.logger.logger.error(f"Erro RCON execute: {e}")
            await self.disconnect()  # Reconectar na próxima
            return None

        except Exception as e:
            self.logger.logger.error(f"Erro RCON geral: {e}")
            return None