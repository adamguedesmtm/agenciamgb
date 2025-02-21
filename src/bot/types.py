"""
Type Definitions for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 12:17:26
"""

from typing import TypeVar, Dict, List, Union, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from .constants import (
    Permission, 
    ServerStatus, 
    CommandType,
    EventType,
    GameMode,
    Team
)

# Type Variables
T = TypeVar('T')
JsonType = Union[Dict, List, str, int, float, bool, None]

# Player Types
@dataclass
class PlayerStats:
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    headshots: int = 0
    score: int = 0
    ping: int = 0
    connected_time: float = 0.0

@dataclass
class Player:
    steam_id: str
    name: str
    team: Team
    stats: PlayerStats
    ip: str
    connected_at: datetime
    last_active: datetime
    permissions: Permission
    is_bot: bool = False
    is_alive: bool = True

# Command Types
@dataclass
class CommandContext:
    name: str
    args: List[str]
    sender: Player
    timestamp: datetime
    raw: str

@dataclass
class Command:
    name: str
    description: str
    usage: str
    aliases: List[str]
    permission: Permission
    type: CommandType
    enabled: bool
    handler: Callable[[CommandContext], Any]

# Event Types
@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None

# Server Types
@dataclass
class ServerInfo:
    name: str
    ip: str
    port: int
    map: str
    game_mode: GameMode
    players: List[Player]
    max_players: int
    tickrate: int
    uptime: float
    status: ServerStatus
    password_protected: bool
    version: str

@dataclass
class MapInfo:
    name: str
    type: str
    workshop_id: Optional[int]
    size: int
    last_modified: datetime
    checksum: str

# Plugin Types
@dataclass
class PluginInfo:
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str]
    enabled: bool
    loaded_at: datetime

# Config Types
ConfigValue = Union[str, int, float, bool, List, Dict]
ConfigDict = Dict[str, ConfigValue]

# Database Types
@dataclass
class DatabaseConfig:
    type: str
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
    timeout: int

# Cache Types
@dataclass
class CacheConfig:
    type: str
    host: str
    port: int
    db: int
    password: Optional[str]
    ttl: int

# API Types
@dataclass
class APIResponse:
    status: int
    data: JsonType
    message: Optional[str] = None
    errors: Optional[List[str]] = None

# Metric Types
@dataclass
class Metric:
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime

# Log Types
@dataclass
class LogEntry:
    level: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    trace: Optional[str] = None

# Error Types
@dataclass
class ErrorInfo:
    type: str
    message: str
    traceback: List[str]
    context: Dict[str, Any]
    timestamp: datetime

# Job Types
@dataclass
class Job:
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    interval: Optional[float]
    next_run: datetime
    last_run: Optional[datetime]
    last_success: Optional[datetime]
    last_error: Optional[ErrorInfo]
    enabled: bool

# State Types
StateValue = Union[str, int, float, bool, List, Dict, None]
StateDict = Dict[str, StateValue]

# Notification Types
@dataclass
class Notification:
    id: str
    title: str
    message: str
    type: str
    timestamp: datetime
    recipient: Optional[str]
    read: bool = False
    delivered: bool = False

# Auth Types
@dataclass
class AuthToken:
    token: str
    type: str
    expires: datetime
    user_id: str
    scope: List[str]