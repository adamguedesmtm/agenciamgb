"""
CS2 Discord Bot Main
Author: adamguedesmtm
Created: 2025-02-21 15:58:46
"""

import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.database_manager import DatabaseManager
from utils.metrics import MetricsManager
from utils.server_manager import ServerManager
from utils.matchzy_manager import MatchzyManager
from utils.wingman_manager import WingmanManager
from utils.retake_manager import RetakeManager
from utils.queue_manager import QueueManager
from utils.demo_manager import DemoManager
from utils.elo_manager import EloManager
from utils.role_system import RoleSystem
from utils.channel_manager import ChannelManager
from utils.stats_manager import StatsManager
from utils.rcon_manager import RCONManager
from utils.steam_manager import SteamManager
from pathlib import Path
import asyncio

class CS2Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=self.config.get("discord.prefix", "!"),
            intents=intents,
            help_command=None
        )

        # Paths
        self.base_dir = Path(__file__).parent.parent
        self.assets_dir = self.base_dir / "assets"
        self.data_dir = self.base_dir / "data"

        # Managers principais
        self.config = ConfigManager()
        self.logger = Logger("cs2bot")
        self.db = DatabaseManager(self.config.get("database"), logger=self.logger)
        self.metrics = MetricsManager(data_dir=str(self.data_dir), logger=self.logger)
        self.server_manager = ServerManager(logger=self.logger)
        self.stats_manager = StatsManager(self.db, logger=self.logger, metrics=self.metrics)
        self.role_system = RoleSystem(self.stats_manager, logger=self.logger, metrics=self.metrics)
        self.channel_manager = ChannelManager(self, logger=self.logger)

        # Game managers
        self.queue = QueueManager(logger=self.logger, metrics=self.metrics)
        self.matchzy = MatchzyManager(logger=self.logger, metrics=self.metrics, stats_manager=self.stats_manager)
        self.wingman = WingmanManager(
            rcon=RCONManager(
                host=self.config.get("servers.wingman.host", "localhost"),
                port=self.config.get("servers.wingman.port", 27016),
                password=self.config.get("servers.wingman.rcon_password", ""),
                logger=self.logger
            ),
            map_manager=MapManager(logger=self.logger),
            logger=self.logger,
            metrics=self.metrics
        )
        self.retake = RetakeManager(
            rcon=RCONManager(
                host=self.config.get("servers.retake.host", "localhost"),
                port=self.config.get("servers.retake.port", 27017),
                password=self.config.get("servers.retake.rcon_password", ""),
                logger=self.logger
            ),
            logger=self.logger,
            metrics=self.metrics
        )

        # Steam integration
        self.steam_manager = SteamManager(
            api_key=self.config.get("steam.api_key", ""),
            logger=self.logger
        )

    async def setup_hook(self):
        """Setup do bot."""
        cogs_dir = Path(__file__).parent / "cogs"
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    self.logger.logger.info(f"Cog carregada: {filename}")
                except Exception as e:
                    self.logger.logger.error(f"Erro ao carregar cog {filename}: {e}")

        # Sincronizar comandos
        await self.tree.sync()

    async def on_ready(self):
        """Evento quando o bot está pronto."""
        self.logger.logger.info(f"Bot conectado como {self.user}")
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="CS2 Matches"
        )
        await self.change_presence(activity=activity)

def main():
    """Função principal."""
    try:
        bot = CS2Bot()
        bot.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        print(f"Erro ao iniciar bot: {e}")

if __name__ == "__main__":
    main()