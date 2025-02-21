"""
CS2 Discord Bot Main
Author: adamguedesmtm
Created: 2025-02-21 13:27:15
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.config_manager import ConfigManager
from utils.metrics import MetricsManager
from utils.logger import Logger
from utils.rcon_manager import RCONManager
from utils.queue_manager import QueueManager
from utils.matchzy_manager import MatchzyManager
from utils.wingman_manager import WingmanManager
from utils.retake_manager import RetakeManager
from utils.player_card import PlayerCard

# Carregar variáveis de ambiente
load_dotenv()

class CS2Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Inicializar managers
        self.config = ConfigManager()
        self.metrics = MetricsManager()
        self.logger = Logger('cs2bot')
        
        # RCON managers
        self.rcon_5v5 = RCONManager(
            self.config.get('servers.competitive.host', 'localhost'),
            self.config.get('servers.competitive.port', 27015),
            self.config.get('servers.competitive.rcon_password', '')
        )
        
        self.rcon_2v2 = RCONManager(
            self.config.get('servers.wingman.host', 'localhost'),
            self.config.get('servers.wingman.port', 27016),
            self.config.get('servers.wingman.rcon_password', '')
        )
        
        self.rcon_retake = RCONManager(
            self.config.get('servers.retake.host', 'localhost'),
            self.config.get('servers.retake.port', 27017),
            self.config.get('servers.retake.rcon_password', '')
        )
        
        # Game managers
        self.queue = QueueManager(self.metrics)
        self.matchzy = MatchzyManager(self.rcon_5v5, self.config, self.metrics)
        self.wingman = WingmanManager(self.rcon_2v2, self.config, self.metrics)
        self.retake = RetakeManager(self.rcon_retake, self.config, self.metrics)
        self.player_card = PlayerCard(self.metrics)
        
    async def setup_hook(self):
        """Setup do bot"""
        # Carregar cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                self.logger.logger.info(f"Cog carregada: {filename}")
                
    async def on_ready(self):
        """Evento quando bot está pronto"""
        self.logger.logger.info(f"Bot conectado como {self.user}")
        
        # Status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="CS2 Matches"
        )
        await self.change_presence(activity=activity)

def main():
    """Função principal"""
    bot = CS2Bot()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()