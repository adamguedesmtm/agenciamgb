"""
CS2 Discord Bot Main
Author: adamguedesmtm
Created: 2025-02-21 15:48:25
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
from utils.elo_manager import EloManager  # Novo import
from utils.steam_manager import SteamManager  # Novo import
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
        
        # Stats & Cards
        self.player_card = PlayerCard(
            assets_dir=str(self.assets_dir),
            logger=self.logger,
            metrics=self.metrics
        )
        
        # Novos managers
        self.elo = EloManager(self.metrics)
        self.steam = SteamManager(
            api_key=os.getenv('STEAM_API_KEY'),
            logger=self.logger
        )
        
        # Listeners para eventos
        self.setup_listeners()
    
    def setup_listeners(self):
        """Configurar event listeners"""
        @self.event
        async def on_match_end(match_data: dict):
            """Atualizar ELO quando uma partida termina"""
            try:
                # Atualizar ELO dos jogadores
                elo_changes = self.elo.calculate_match_elo(match_data)
                
                # Atualizar métricas
                for change in elo_changes:
                    self.metrics.update_player_rating(
                        change['steam_id'],
                        change['new_rating'],
                        change['rating_change']
                    )
                
                # Notificar no canal de resultados
                results_channel_id = self.config.get('channels.match_results')
                if results_channel_id:
                    channel = self.get_channel(int(results_channel_id))
                    if channel:
                        embed = discord.Embed(
                            title="🏁 Partida Finalizada",
                            color=discord.Color.blue()
                        )
                        
                        # Score
                        score_ct = match_data['score_ct']
                        score_t = match_data['score_t']
                        embed.add_field(
                            name="Placar",
                            value=f"CT {score_ct} x {score_t} T",
                            inline=False
                        )
                        
                        # ELO changes
                        elo_text = ""
                        for change in elo_changes:
                            player_name = self.steam.get_player_name(change['steam_id'])
                            sign = "+" if change['rating_change'] > 0 else ""
                            elo_text += f"{player_name}: {sign}{change['rating_change']:.1f}\n"
                        
                        embed.add_field(
                            name="Mudanças de ELO",
                            value=elo_text or "Nenhuma mudança",
                            inline=False
                        )
                        
                        await channel.send(embed=embed)
                
            except Exception as e:
                self.logger.logger.error(f"Erro ao processar fim de partida: {e}")
    
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