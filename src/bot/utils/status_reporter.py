"""
Status Reporter for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21
"""

import discord
import psutil
import asyncio
from datetime import datetime
import os
from .logger import Logger

class StatusReporter:
    def __init__(self, bot, status_channel_id, admin_channel_id):
        self.bot = bot
        self.status_channel_id = status_channel_id
        self.admin_channel_id = admin_channel_id
        self.last_message = None
        self.logger = Logger('status_reporter')
        self.last_alert_time = {}

    async def send_status_update(self):
        try:
            status_channel = self.bot.get_channel(self.status_channel_id)
            admin_channel = self.bot.get_channel(self.admin_channel_id)
            
            if not status_channel or not admin_channel:
                self.logger.logger.error("Canais não encontrados!")
                return

            system_status = self._get_system_status()
            services_status = await self._get_services_status()
            server_info = await self._get_cs2_server_info()
            alerts = self._check_alerts(system_status, services_status)

            embed = discord.Embed(
                title="🖥️ Status do Servidor CS2",
                description=f"Última atualização: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                color=0x00ff00 if not alerts else 0xff0000
            )

            # Sistema
            embed.add_field(
                name="💻 Sistema",
                value=f"CPU: {system_status['cpu']}%\n"
                      f"RAM: {system_status['memory']}%\n"
                      f"Disco: {system_status['disk']}%\n"
                      f"Temperatura: {system_status['temp']}°C",
                inline=False
            )

            # Serviços
            embed.add_field(
                name="🔧 Serviços",
                value="\n".join([
                    f"{name}: {'🟢' if status else '🔴'}"
                    for name, status in services_status.items()
                ]),
                inline=False
            )

            # Servidor CS2
            embed.add_field(
                name="🎮 Servidor CS2",
                value=f"Players: {server_info['players']}/10\n"
                      f"Mapa: {server_info['map']}\n"
                      f"IP: {os.getenv('SERVER_IP')}:{os.getenv('SERVER_PORT')}",
                inline=False
            )

            # Alertas
            if alerts:
                embed.add_field(
                    name="⚠️ Alertas",
                    value="\n".join(alerts),
                    inline=False
                )
                
                # Enviar alertas críticos para canal admin
                current_time = datetime.now()
                for alert in alerts:
                    if "🔥" in alert:  # Apenas alertas críticos
                        # Evitar spam de alertas (1 alerta a cada 30 minutos)
                        if alert not in self.last_alert_time or \
                           (current_time - self.last_alert_time[alert]).seconds > 1800:
                            await admin_channel.send(f"⚠️ **ALERTA CRÍTICO**\n{alert}")
                            self.last_alert_time[alert] = current_time

            try:
                if self.last_message:
                    await self.last_message.edit(embed=embed)
                else:
                    self.last_message = await status_channel.send(embed=embed)
            except Exception as e:
                self.logger.logger.error(f"Erro ao atualizar mensagem: {e}")

        except Exception as e:
            self.logger.logger.error(f"Erro ao enviar status: {e}")

    def _get_system_status(self):
        return {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'temp': self._get_cpu_temp()
        }

    def _get_cpu_temp(self):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return round(int(f.read().strip()) / 1000, 1)
        except:
            return 0

    async def _get_services_status(self):
        return {
            'CS2 Server': await self._check_service('cs2server'),
            'Matchzy': await self._check_service('matchzy'),
            'Database': await self._check_service('postgresql'),
            'Bot': True
        }

    async def _check_service(self, service_name):
        try:
            proc = await asyncio.create_subprocess_shell(
                f"systemctl is-active {service_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip() == "active"
        except:
            return False

    async def _get_cs2_server_info(self):
        try:
            # Implementar lógica real de consulta ao servidor CS2
            return {
                'players': await self._get_player_count(),
                'map': await self._get_current_map(),
                'status': 'online'
            }
        except:
            return {
                'players': '0',
                'map': 'unknown',
                'status': 'offline'
            }

    def _check_alerts(self, system, services):
        alerts = []
        
        # Sistema
        if system['cpu'] > 90:
            alerts.append("🔥 CPU em uso crítico!")
        elif system['cpu'] > 80:
            alerts.append("⚠️ CPU em uso elevado")

        if system['memory'] > 90:
            alerts.append("🔥 Memória em uso crítico!")
        elif system['memory'] > 80:
            alerts.append("⚠️ Memória em uso elevado")

        if system['disk'] > 90:
            alerts.append("🔥 Disco quase cheio!")
        elif system['disk'] > 80:
            alerts.append("⚠️ Disco em uso elevado")

        if system['temp'] > 80:
            alerts.append("🔥 Temperatura crítica!")
        elif system['temp'] > 70:
            alerts.append("⚠️ Temperatura elevada")

        # Serviços
        for service, status in services.items():
            if not status:
                alerts.append(f"🔥 Serviço {service} está offline!")

        return alerts

    async def _get_player_count(self):
        # Implementar lógica real de consulta
        return '0'

    async def _get_current_map(self):
        # Implementar lógica real de consulta
        return 'de_mirage'