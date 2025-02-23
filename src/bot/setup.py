import os
import json
import asyncio
from pathlib import Path
from miniupnpc import UPnP
from dotenv import load_dotenv
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.logger import Logger
from utils.metrics import MetricsManager
from utils.rcon_manager import RCONManager
from utils.queue_manager import QueueManager
from utils.matchzy_manager import MatchzyManager
from utils.wingman_manager import WingmanManager
from utils.retake_manager import RetakeManager
from utils.player_card import PlayerCard
from utils.elo_manager import EloManager

# Carregar variáveis de ambiente
load_dotenv()

class SetupBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents, help_command=None)

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
        self.metrics = MetricsManager(data_dir=str(self.data_dir), logger=self.logger)
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

async def setup_bot():
    try:
        bot = SetupBot()
        await bot.login(os.getenv('DISCORD_TOKEN'))
        await bot.setup_hook()
        await bot.on_ready()
    except Exception as e:
        print(f"Erro ao iniciar bot: {e}")

async def setup_config():
    config = {}

    # Configurações do Discord
    config['discord'] = {
        'token': input("Insira o token do bot Discord: ").strip(),
        'prefix': input("Insira o prefixo dos comandos (! por padrão): ").strip() or "!",
        'admin_role': input("Insira o nome da role administradora (Admin por padrão): ").strip() or "Admin"
    }

    # Configurações do Banco de Dados
    config['database'] = {
        'host': input("Insira o host do banco de dados (localhost por padrão): ").strip() or "localhost",
        'port': int(input("Insira a porta do banco de dados (5432 por padrão): ").strip() or 5432),
        'name': input("Insira o nome do banco de dados: ").strip(),
        'user': input("Insira o usuário do banco de dados: ").strip(),
        'password': input("Insira a senha do banco de dados: ").strip()
    }

    # Configurações dos Servidores CS2
    config['servers'] = {}
    for server_type in ['competitive', 'wingman', 'retake']:
        config['servers'][server_type] = {
            'host': input(f"Insira o host do servidor {server_type} (localhost por padrão): ").strip() or "localhost",
            'port': int(input(f"Insira a porta do servidor {server_type} (27015, 27016, 27017 por padrão): ").strip()),
            'rcon_password': input(f"Insira a senha RCON do servidor {server_type}: ").strip(),
            'server_password': input(f"Insira a senha do servidor {server_type} (deixe em branco se não houver): ").strip(),
            'maps': input(f"Insira os mapas disponíveis para o modo {server_type} (separados por vírgula): ").strip().split(",")
        }

    # Configurações do Steam API
    config['steam'] = {
        'api_key': input("Insira sua chave da Steam API: ").strip()
    }

    # Configurações dos Canais Discord
    config['channels'] = {
        'notifications': int(input("Insira o ID do canal de notificações: ").strip()),
        'commands': int(input("Insira o ID do canal de comandos: ").strip()),
        'competitive_voice': int(input("Insira o ID do canal de voz competitivo: ").strip()),
        'wingman_voice': int(input("Insira o ID do canal de voz Wingman: ").strip()),
        'retake_voice': int(input("Insira o ID do canal de voz Retake: ").strip())
    }

    # Configurações do DuckDNS (opcional)
    config['duckdns'] = {
        'enabled': input("Deseja usar DuckDNS? (sim/não): ").strip().lower() == "sim",
        'domain': input("Insira seu subdomínio DuckDNS (ex.: seuservidor.duckdns.org): ").strip(),
        'token': input("Insira seu token DuckDNS: ").strip()
    }

    # Configurações do UPnP (opcional)
    config['upnp'] = {
        'enabled': input("Deseja habilitar UPnP para abrir portas automaticamente? (sim/não): ").strip().lower() == "sim"
    }

    # Salvar configurações no arquivo JSON
    config_file = Path(__file__).parent.parent / "config" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"Configurações salvas em {config_file}")
    return config

async def initialize_upnp(config):
    upnp = UPnP()
    upnp.discoverdelay = 200
    upnp.discover()
    upnp.selectigd()

    for server_type in ['competitive', 'wingman', 'retake']:
        server_config = config['servers'][server_type]
        port = server_config['port']
        gotv_port = port + 1

        upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, f"CS2 Server {server_type}", '')
        upnp.addportmapping(port, 'UDP', upnp.lanaddr, port, f"CS2 Server {server_type}", '')
        upnp.addportmapping(gotv_port, 'TCP', upnp.lanaddr, gotv_port, f"CS2 GOTV {server_type}", '')
        upnp.addportmapping(gotv_port, 'UDP', upnp.lanaddr, gotv_port, f"CS2 GOTV {server_type}", '')

    print("Portas abertas via UPnP com sucesso!")

async def main():
    config = await setup_config()
    await setup_bot()
    if config['upnp']['enabled']:
        await initialize_upnp(config)

if __name__ == "__main__":
    asyncio.run(main())