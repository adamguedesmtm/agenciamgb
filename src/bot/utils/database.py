"""
Database Handler
Author: adamguedesmtm
Created: 2025-02-21
"""

import asyncpg
import os
from dotenv import load_dotenv
from .logger import Logger

class Database:
    def __init__(self):
        self.pool = None
        self.logger = Logger('database')

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                host=os.getenv('DB_HOST')
            )
            self.logger.logger.info("Database conectada com sucesso")
        except Exception as e:
            self.logger.logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.logger.logger.info("Database desconectada")