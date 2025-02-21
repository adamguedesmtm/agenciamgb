"""
Config - CS2 Stats Configuration
Author: adamguedesmtm
Created: 2025-02-21 15:20:04
"""

from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Diretórios
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DEMOS_DIR: Path = BASE_DIR / "data" / "demos"
    ANALYSIS_DIR: Path = BASE_DIR / "data" / "analysis"
    
    # CS Demo Manager
    CS_DEMO_MANAGER_PATH: str = "/usr/local/bin/cs-demo-manager"
    
    # Servidor Web
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hora
    
    # Limites
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_CONCURRENT_UPLOADS: int = 3
    
    class Config:
        env_prefix = "CS2STATS_"

settings = Settings()