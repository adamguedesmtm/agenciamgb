"""
RCON Client for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 12:19:50
"""

import asyncio
from typing import Optional, Dict, List
import struct
import time
from .logger import Logger
from .metrics import MetricsManager

class RCONPacket:
    """RCON Packet Structure"""
    
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0
    
    def __init__(self,
                 id: int,
                 type: int,
                 body: str = ""):
        self.id = id
        self.type = type
        self.body = body
        
    def encode(self) -> bytes:
        """Encode packet to bytes"""
        body_encoded = self.body.encode('utf-8')
        size = len(body_encoded) + 10
        return struct.pack(
            '<iii',
            size,
            self.id,
            self.type
        ) + body_encoded + b'\x00\x00'
        
    @classmethod
    def decode(cls, data: bytes) -> 'RCONPacket':
        """Decode bytes to packet"""
        size = struct.unpack('<i', data[:4])[0]
        id = struct.unpack('<i', data[4:8])[0]
        type = struct.unpack('<i', data[8:12])[0]
        body = data[12:-2].decode('utf-8')
        return cls(id, type, body)

class RCONClient:
    def __init__(self,
                 host: str,
                 port: int,
                 password: str,
                 logger: Logger,
                 metrics: MetricsManager):
        self.host = host
        self.port = port
        self.password = password
        self.logger = logger
        self.metrics = metrics
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0
        self._authenticated = False
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Connect to RCON server"""
        try:
            # Connect to server
            self._reader, self._writer = await asyncio.open_connection(
                self.host,
                self.port
            )
            
            # Authenticate
            auth_success = await self.authenticate()
            
            if auth_success:
                self.logger.info("RCON connected and authenticated")
                await self.metrics.record_metric(
                    'rcon.connections',
                    1
                )
            else:
                self.logger.error("RCON authentication failed")
                await self.disconnect()
                
            return auth_success
            
        except Exception as e:
            self.logger.error(f"RCON connection failed: {e}")
            await self.metrics.record_metric(
                'rcon.connection_errors',
                1
            )
            return False

    async def disconnect(self):
        """Disconnect from RCON server"""
        try:
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
                
            self._reader = None
            self._writer = None
            self._authenticated = False
            
            self.logger.info("RCON disconnected")
            
        except Exception as e:
            self.logger.error(f"RCON disconnect error: {e}")

    async def authenticate(self) -> bool:
        """Authenticate with RCON server"""
        try:
            # Send auth packet
            packet = RCONPacket(
                self._get_request_id(),
                RCONPacket.SERVERDATA_AUTH,
                self.password
            )
            
            await self._send_packet(packet)
            
            # Get response
            response = await self._read_packet()
            
            # Check auth success
            self._authenticated = (
                response and
                response.type == RCONPacket.SERVERDATA_AUTH_RESPONSE and
                response.id != -1
            )
            
            return self._authenticated
            
        except Exception as e:
            self.logger.error(f"RCON auth error: {e}")
            return False

    async def execute(self, command: str) -> Optional[str]:
        """Execute RCON command"""
        try:
            async with self._lock:
                if not self._authenticated:
                    if not await self.connect():
                        return None
                        
                # Send command
                start_time = time.time()
                packet = RCONPacket(
                    self._get_request_id(),
                    RCONPacket.SERVERDATA_EXECCOMMAND,
                    command
                )
                
                await self._send_packet(packet)
                
                # Get response
                response = await self._read_packet()
                
                # Record metrics
                elapsed = time.time() - start_time
                await self.metrics.record_metric(
                    'rcon.command_time',
                    elapsed,
                    {'command': command.split()[0]}
                )
                
                if response:
                    return response.body
                return None
                
        except Exception as e:
            self.logger.error(f"RCON execute error: {e}")
            await self.metrics.record_metric(
                'rcon.command_errors',
                1,
                {'command': command.split()[0]}
            )
            return None

    async def _send_packet(self, packet: RCONPacket):
        """Send RCON packet"""
        if not self._writer:
            raise ConnectionError("Not connected")
            
        try:
            self._writer.write(packet.encode())
            await self._writer.drain()
        except Exception as e:
            raise ConnectionError(f"Send error: {e}")

    async def _read_packet(self) -> Optional[RCONPacket]:
        """Read RCON packet"""
        if not self._reader:
            raise ConnectionError("Not connected")
            
        try:
            # Read packet size
            size_data = await self._reader.read(4)
            if not size_data:
                return None
                
            size = struct.unpack('<i', size_data)[0]
            
            # Read packet data
            data = size_data + await self._reader.read(size)
            
            return RCONPacket.decode(data)
            
        except Exception as e:
            raise ConnectionError(f"Read error: {e}")

    def _get_request_id(self) -> int:
        """Get next request ID"""
        self._request_id += 1
        return self._request_id