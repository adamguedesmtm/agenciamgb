import asyncio
import subprocess
from miniupnpc import UPnP

class ServerManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.active_server = None  # Armazena informações sobre o servidor ativo
        self.server_lock = asyncio.Lock()  # Bloqueio para evitar múltiplos servidores
        self.upnp = UPnP()


async def _setup_upnp(self, server_config: Dict):
    """Configurar UPnP para abrir portas"""
    try:
        if not self.config.get('upnp.enabled'):
            return

        for port in [server_config['port'], server_config['port'] + 1]:  # Porta principal e GOTV
            self.upnp.addportmapping(port, 'TCP', self.upnp.lanaddr, port, f"CS2 Server Port {port}", '')
            self.upnp.addportmapping(port, 'UDP', self.upnp.lanaddr, port, f"CS2 Server Port {port}", '')

        self.logger.logger.info("UPnP configurado com sucesso!")
    except Exception as e:
        self.logger.logger.error(f"Erro ao configurar UPnP: {e}")


    async def start_server(self, server_type: str, config: Dict) -> Optional[Dict]:
        """Inicia um servidor específico usando cs2-modded-server."""
        if self.active_server:
            self.logger.error("Já existe um servidor ativo!")
            return None

        async with self.server_lock:
            if not self.active_server:
                try:
                    # Configurar servidor
                    self.active_server = {
                        "type": server_type,
                        "config": config,
                        "started_at": datetime.utcnow()
                    }

                    # Inicializar UPnP
                    await self._initialize_upnp()
                    await self._open_ports(config)

                    # Iniciar servidor CS2 usando cs2-modded-server
                    subprocess.Popen([
                        "/opt/cs2-modded-server/start_server.sh",
                        "-game", "csgo",
                        "+map", "de_dust2",
                        "+maxplayers", str(config.get('max_players', 10)),
                        "+sv_setsteamaccount", "YOUR_STEAM_ACCOUNT_TOKEN",
                        "+rcon_password", config['rcon_password'],
                        "+tv_enable", "1",
                        "+tv_port", str(config['port'] + 1),
                        "+port", str(config['port']),
                        "+hostname", f"AgenciaMGB CS2 - {server_type.capitalize()}",
                        "+ip", "::",  # Escuta em todas as interfaces IPv6
                        "+sv_lan", "0"
                    ])

                    # Atualize o IP do servidor para usar o domínio DuckDNS
                    config['host'] = "seuservidor.duckdns.org"

                    return self.active_server
                except Exception as e:
                    self.logger.error(f"Erro ao iniciar servidor {server_type}: {e}")
                    return None

    async def stop_server(self) -> bool:
        """Para o servidor ativo e fecha as portas via UPnP."""
        if not self.active_server:
            self.logger.warning("Nenhum servidor ativo para parar.")
            return False

        async with self.server_lock:
            try:
                # Parar servidor
                await self._stop_active_server()

                # Fechar portas via UPnP
                await self._close_ports(self.active_server["config"])

                self.active_server = None
                return True
            except Exception as e:
                self.logger.error(f"Erro ao parar servidor: {e}")
                return False

    async def _initialize_upnp(self):
        """Inicializa a conexão UPnP."""
        self.upnp.discoverdelay = 200
        self.upnp.discover()
        self.upnp.selectigd()
        self.logger.info("UPnP inicializado com sucesso!")

    async def _open_ports(self, config: Dict):
        """Abre as portas necessárias via UPnP."""
        self.logger.info(f"Abrindo porta {config['port']} via UPnP...")
        self.upnp.addportmapping(config['port'], 'TCP', self.upnp.lanaddr, config['port'], 'CS2 Server', '')
        self.upnp.addportmapping(config['port'], 'UDP', self.upnp.lanaddr, config['port'], 'CS2 Server', '')

        gotv_port = config['port'] + 1
        self.logger.info(f"Abrindo porta GOTV {gotv_port} via UPnP...")
        self.upnp.addportmapping(gotv_port, 'TCP', self.upnp.lanaddr, gotv_port, 'CS2 GOTV', '')
        self.upnp.addportmapping(gotv_port, 'UDP', self.upnp.lanaddr, gotv_port, 'CS2 GOTV', '')

    async def _close_ports(self, config: Dict):
        """Fecha as portas abertas via UPnP."""
        self.logger.info(f"Fechando porta {config['port']} via UPnP...")
        self.upnp.deleteportmapping(config['port'], 'TCP')
        self.upnp.deleteportmapping(config['port'], 'UDP')

        gotv_port = config['port'] + 1
        self.logger.info(f"Fechando porta GOTV {gotv_port} via UPnP...")
        self.upnp.deleteportmapping(gotv_port, 'TCP')
        self.upnp.deleteportmapping(gotv_port, 'UDP')

async def _launch_server(self, config: Dict):
    """Método interno para iniciar o servidor CS2."""
    try:
        self.logger.logger.info(f"Iniciando servidor {config['type']}...")

        # Configurar UPnP
        await self._setup_upnp(config)
        
        subprocess.Popen([
            "/opt/cs2-modded-server/start_server.sh",
            "-game", "csgo",
            "+map", "de_dust2",
            "+maxplayers", str(config.get('max_players', 10)),
            "+sv_setsteamaccount", "YOUR_STEAM_ACCOUNT_TOKEN",
            "+rcon_password", config['rcon_password'],
            "+tv_enable", "1",
            "+tv_port", str(config['port'] + 1),
            "+port", str(config['port']),
            "+hostname", f"AgenciaMGB CS2 - {config['type'].capitalize()}",
            "+ip", "::",  # Escuta em todas as interfaces IPv6
            "+sv_lan", "0"
        ])

        self.logger.logger.info(f"Servidor {config['type']} iniciado com sucesso!")
    except Exception as e:
        self.logger.logger.error(f"Erro ao iniciar servidor {config['type']}: {e}")

    async def _stop_active_server(self):
        """Método interno para parar o servidor ativo."""
        if not self.active_server:
            return

        self.logger.info(f"Parando servidor {self.active_server['type']}...")
        subprocess.run(["pkill", "-f", "srcds_linux"])