"""
CS2 Discord Bot Main
Author: adamguedesmtm
Created: 2025-02-21 15:58:46
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
from utils.elo_manager import EloManager
from pathlib import Path

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
        
        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.assets_dir = self.base_dir / "assets"
        self.data_dir = self.base_dir / "data"
        
        # Criar diretórios necessários
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Managers principais
        self.config = ConfigManager()
        self.logger = Logger('cs2bot')
        self.metrics = MetricsManager(
            data_dir=str(self.data_dir),
            logger=self.logger
        )
        self.elo = EloManager(self.metrics)
        
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
        self.matchzy = MatchzyManager(
            logger=self.logger,
            metrics=self.metrics,
            elo_manager=self.elo,
            rcon_manager=self.rcon_5v5
        )
        self.wingman = WingmanManager(
            logger=self.logger,
            metrics=self.metrics,
            elo_manager=self.elo,
            rcon_manager=self.rcon_2v2
        )
        self.retake = RetakeManager(
            logger=self.logger,
            metrics=self.metrics,
            rcon_manager=self.rcon_retake
        )
        
        # Utils
        self.player_card = PlayerCard(
            assets_dir=str(self.assets_dir),
            logger=self.logger,
            metrics=self.metrics
        )
    
    async def setup_hook(self):
        """Setup do bot"""
        # Carregar cogs
        cogs_dir = Path(__file__).parent / "cogs"
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    self.logger.logger.info(f"Cog carregada: {filename}")
                except Exception as e:
                    self.logger.logger.error(f"Erro ao carregar cog {filename}: {e}")
        
        # Sincronizar comandos
        await self.tree.sync()
                
    async def on_ready(self):
        """Evento quando bot está pronto"""
        self.logger.logger.info(f"Bot conectado como {self.user}")
        
        # Status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="CS2 Matches"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Handler global de erros"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        self.logger.logger.error(f"Erro no comando: {error}")
        await ctx.send(f"❌ Erro: {str(error)}")

def main():
    """Função principal"""
    try:
        bot = CS2Bot()
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        print(f"Erro ao iniciar bot: {e}")

if __name__ == "__main__":
    main()