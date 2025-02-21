"""
CS2 Server Configuration Script
Author: adamguedesmtm
Created: 2025-02-21 03:24:21
"""

import os
import sys
import json
import subprocess
from pathlib import Path

class ServerConfigurator:
    def __init__(self):
        self.base_path = Path("/opt/cs2server")
        self.config_path = self.base_path / "config"
        self.cs2_path = self.base_path / "cs2"
        
    def configure_server(self):
        try:
            # Criar estrutura de diretórios
            self._create_directories()
            
            # Configurar permissões
            self._set_permissions()
            
            # Configurar CS2
            self._configure_cs2()
            
            # Configurar sistema
            self._configure_system()
            
            print("✅ Configuração concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a configuração: {e}")
            return False
            
    def _create_directories(self):
        directories = [
            "cs2/cfg",
            "matchzy",
            "bot",
            "demos/new",
            "demos/processed",
            "backups/database",
            "backups/configs",
            "logs/cs2",
            "logs/bot",
            "logs/matchzy",
            "logs/nginx"
        ]
        
        for dir_path in directories:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
            
    def _set_permissions(self):
        subprocess.run([
            "chown", "-R",
            "cs2server:cs2server",
            str(self.base_path)
        ])
        
        # Definir permissões corretas
        subprocess.run([
            "chmod", "-R",
            "750",
            str(self.base_path)
        ])
        
        # Permissões especiais para configs
        subprocess.run([
            "chmod", "700",
            str(self.config_path)
        ])
        
    def _configure_cs2(self):
        # Copiar configs base
        cs2_configs = {
            "server.cfg": self._get_server_config(),
            "admins.cfg": self._get_admins_config(),
            "bans.cfg": self._get_bans_config()
        }
        
        for filename, content in cs2_configs.items():
            config_file = self.cs2_path / "cfg" / filename
            with open(config_file, "w") as f:
                f.write(content)
                
    def _configure_system(self):
        # Configurar limites do sistema
        with open("/etc/security/limits.d/cs2server.conf", "w") as f:
            f.write("cs2server soft nofile 16384\n")
            f.write("cs2server hard nofile 16384\n")
            
        # Configurar sysctl
        with open("/etc/sysctl.d/99-cs2server.conf", "w") as f:
            f.write("net.ipv4.ip_local_port_range = 1024 65535\n")
            f.write("net.ipv4.tcp_tw_reuse = 1\n")
            
        # Aplicar configurações
        subprocess.run(["sysctl", "--system"])
        
    def _get_server_config(self):
        return """// Server Configuration
hostname "AgenciaMGB CS2 Server"
sv_setsteamaccount "YOURTOKEN"
rcon_password "RCON_PASSWORD"
sv_cheats 0
sv_lan 0
// ... resto das configurações
"""

    def _get_admins_config(self):
        return """// Admins Configuration
// Format: "STEAM_X:X:XXXXXXXX" "password" "flags"
"""

    def _get_bans_config(self):
        return """// Bans Configuration
// Format: "STEAM_X:X:XXXXXXXX" "reason" "admin" "duration"
"""

if __name__ == "__main__":
    configurator = ServerConfigurator()
    if not configurator.configure_server():
        sys.exit(1)