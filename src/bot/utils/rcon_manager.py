"""
RCON Manager for CS2 Server Communication
Author: adamguedesmtm
Created: 2025-02-21 14:39:11
"""

import valve.rcon
from typing import Optional
import asyncio
from .logger import Logger

class RCONManager:
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 27015, 
                 password: str = '', 
                 logger: Optional[Logger] = None):
        self.host = host
        self.port = port
        self.password = password
        self.logger = logger or Logger('rcon_manager')
        self._rcon = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Estabelecer conexão RCON."""
        try:
            if not self._rcon:
                self._rcon = valve.rcon.RCON((self.host, self.port), self.password)
                self._rcon.connect()
                self.logger.logger.info("Conexão RCON estabelecida")
        except Exception as e:
            self.logger.logger.error(f"Erro ao conectar RCON: {e}")
            raise

    async def execute(self, command: str) -> str:
        """Executar comando RCON."""
        try:
            async with self._lock:
                if not self._rcon:
                    await self.connect()
                response = self._rcon.execute(command)
                return response.decode('utf-8').strip()
        except Exception as e:
            self.logger.logger.error(f"Erro ao executar comando RCON: {e}")
            await self.connect()  # Tentar reconectar
            return ""

    async def get_server_ip(self) -> str:
        """Obter IP do servidor."""
        try:
            response = await self.execute("net_address")
            if "address" in response:
                parts = response.split()
                return parts[1]  # Formato: "address 192.168.1.100:27015"
            return self.host
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter IP do servidor: {e}")
            return self.host

    async def get_server_port(self) -> int:
        """Obter porta do servidor."""
        try:
            response = await self.execute("net_port")
            if response.isdigit():
                return int(response)
            return self.port
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter porta do servidor: {e}")
            return self.port

    async def get_server_password(self) -> str:
        """Obter senha do servidor."""
        try:
            response = await self.execute("sv_password")
            return response.strip() or "Sem senha"
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter senha do servidor: {e}")
            return "Sem senha"

    async def get_gotv_port(self) -> int:
        """Obter porta GOTV."""
        try:
            response = await self.execute("tv_port")
            if response.isdigit():
                return int(response)
            return self.port + 1
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter porta GOTV: {e}")
            return self.port + 1

    async def get_connect_command(self) -> str:
        """Obter comando de conexão completo."""
        try:
            ip = await self.get_server_ip()
            port = await self.get_server_port()
            password = await self.get_server_password()
            return f"connect {ip}:{port}; password {password}"
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter comando de conexão: {e}")
            return ""

    async def get_status(self) -> Dict:
        """Obter status do servidor."""
        try:
            response = await self.execute("status")
            lines = response.split("\n")

            status = {}
            for line in lines:
                if "udp/ip" in line.lower():
                    parts = line.split()
                    status["ip"] = parts[1]
                    status["port"] = int(parts[2].split('/')[0])
                elif "map" in line.lower():
                    status["map"] = line.split(":")[1].strip()
                elif "players" in line.lower():
                    status["players_online"] = int(line.split(":")[1].split("/")[0].strip())

            return status
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter status: {e}")
            return {}

    async def kick_player(self, steam_id: str, reason: str = "") -> bool:
        """Kickar jogador do servidor."""
        try:
            await self.execute(f"kickid {steam_id} {reason}")
            self.logger.logger.info(f"Jogador {steam_id} kickado")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao kickar jogador: {e}")
            return False

    async def change_map(self, map_name: str) -> bool:
        """Trocar mapa do servidor."""
        try:
            await self.execute(f"changelevel {map_name}")
            self.logger.logger.info(f"Mapa trocado para {map_name}")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao trocar mapa: {e}")
            return False

    async def pause_match(self) -> bool:
        """Pausar partida."""
        try:
            await self.execute("mp_pause_match")
            self.logger.logger.info("Partida pausada")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao pausar partida: {e}")
            return False

    async def unpause_match(self) -> bool:
        """Despausar partida."""
        try:
            await self.execute("mp_unpause_match")
            self.logger.logger.info("Partida despausada")
            return True
        except Exception as e:
            self.logger.logger.error(f"Erro ao despausar partida: {e}")
            return False

    async def get_player_list(self) -> List[Dict]:
        """Obter lista de jogadores conectados."""
        try:
            response = await self.execute("status")
            lines = response.split("\n")
            players = []

            for line in lines:
                if line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 6:
                        player = {
                            "index": parts[0],
                            "steam_id": parts[1],
                            "name": " ".join(parts[2:-3]),
                            "ping": parts[-3],
                            "loss": parts[-2],
                            "state": parts[-1]
                        }
                        players.append(player)

            return players
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter lista de jogadores: {e}")
            return []

    def __del__(self):
        """Cleanup ao destruir objeto."""
        if self._rcon:
            try:
                self._rcon.disconnect()
            except:
                pass