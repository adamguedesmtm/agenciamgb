"""
CS2 Server Bot
Author: adamguedesmtm
Created: 2025-02-21
"""

import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from utils.database import Database
from utils.status_reporter import StatusReporter
from utils.logger import Logger
from utils.system_check import check_system_requirements
from utils.error_handler import ErrorHandler

load_dotenv('/opt/cs2server/config/.env')

class CS2Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        
        # Inicializar componentes
        self.logger = Logger('cs2bot')
        self.db = Database()
        self.status_reporter = None
        
        # Registrar handler de erros
        self.add_cog(ErrorHandler(self))
        
        # Log de inicialização
        self.logger.logger.info(f"Bot iniciado por {os.getenv('USER')} em {datetime.utcnow()}")

    async def setup_hook(self):
        try:
            # Verificar requisitos
            check_system_requirements()
            
            # Conectar ao banco
            await self.db.connect()
            self.logger.logger.info("Database conectada")
            
            # Inicializar status reporter
            self.status_reporter = StatusReporter(
                self,
                int(os.getenv('CHANNEL_STATUS')),
                int(os.getenv('CHANNEL_ADMIN'))
            )
            self.status_loop.start()
            self.logger.logger.info("Status reporter inicializado")
            
        except Exception as e:
            self.logger.logger.error(f"Erro na inicialização: {e}")
            await self.close()

    @tasks.loop(minutes=5)
    async def status_loop(self):
        await self.status_reporter.send_status_update()

    async def on_ready(self):
        self.logger.logger.info(f'Bot online como {self.user.name}')
        await self.change_presence(
            activity=discord.Game(name="CS2 Server Monitor")
        )

    async def close(self):
        await self.db.close()
        await super().close()

bot = CS2Bot()

if __name__ == "__main__":
    bot.run(os.getenv('BOT_TOKEN'))