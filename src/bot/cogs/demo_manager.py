"""
Demo Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 03:48:00
"""

import discord
from discord.ext import commands
import os
import asyncio
import glob
from datetime import datetime
from ..utils.logger import Logger

class DemoManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger('demo_manager')
        self.demo_dir = "/opt/cs2server/demos"
        self.new_demos = f"{self.demo_dir}/new"
        self.processed_demos = f"{self.demo_dir}/processed"

    @commands.command(name='demos')
    async def list_demos(self, ctx, days: int = 7):
        """Listar demos disponíveis"""
        try:
            demos = await self._get_recent_demos(days)
            
            if not demos:
                await ctx.send("❌ Nenhuma demo encontrada!")
                return

            embed = discord.Embed(
                title="📼 Demos Disponíveis",
                description=f"Últimos {days} dias",
                color=0x00ff00
            )

            for demo in demos[:10]:  # Limitar a 10 demos
                size = os.path.getsize(demo['path']) / (1024 * 1024)  # MB
                embed.add_field(
                    name=demo['name'],
                    value=f"Data: {demo['date']}\n"
                          f"Tamanho: {size:.1f}MB\n"
                          f"ID: {demo['id']}",
                    inline=True
                )

            if len(demos) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(demos)} demos")

            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao listar demos: {e}")
            await ctx.send("❌ Erro ao listar demos")

    @commands.command(name='getdemo')
    async def get_demo(self, ctx, demo_id: str):
        """Obter link de download de uma demo"""
        try:
            demo = await self._find_demo(demo_id)
            
            if not demo:
                await ctx.send("❌ Demo não encontrada!")
                return

            # Criar link temporário
            link = await self._create_temp_link(demo['path'])
            
            embed = discord.Embed(
                title="📥 Download da Demo",
                description=f"Demo: {demo['name']}\n"
                          f"Válido por: 1 hora",
                color=0x00ff00
            )
            embed.add_field(
                name="Link",
                value=link,
                inline=False
            )

            await ctx.send(embed=embed)
            self.logger.logger.info(
                f"Demo {demo_id} solicitada por {ctx.author}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter demo: {e}")
            await ctx.send("❌ Erro ao obter demo")

    @commands.command(name='deletedemo')
    @commands.has_role('Admin')
    async def delete_demo(self, ctx, demo_id: str):
        """Deletar uma demo"""
        try:
            demo = await self._find_demo(demo_id)
            
            if not demo:
                await ctx.send("❌ Demo não encontrada!")
                return

            os.remove(demo['path'])
            await ctx.send(f"✅ Demo {demo['name']} deletada!")
            
            self.logger.logger.info(
                f"Demo {demo_id} deletada por {ctx.author}"
            )
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao deletar demo: {e}")
            await ctx.send("❌ Erro ao deletar demo")

    async def _get_recent_demos(self, days):
        """Obter demos recentes"""
        try:
            demos = []
            for path in glob.glob(f"{self.processed_demos}/*.dem"):
                stats = os.stat(path)
                demo_time = datetime.fromtimestamp(stats.st_mtime)
                
                # Verificar se está dentro do período
                if (datetime.now() - demo_time).days <= days:
                    demos.append({
                        'name': os.path.basename(path),
                        'path': path,
                        'date': demo_time.strftime('%Y-%m-%d %H:%M'),
                        'id': os.path.splitext(os.path.basename(path))[0]
                    })
                    
            return sorted(demos, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter demos recentes: {e}")
            return []

    async def _find_demo(self, demo_id):
        """Encontrar uma demo específica"""
        try:
            for path in glob.glob(f"{self.processed_demos}/*.dem"):
                if demo_id in path:
                    stats = os.stat(path)
                    return {
                        'name': os.path.basename(path),
                        'path': path,
                        'date': datetime.fromtimestamp(stats.st_mtime).strftime(
                            '%Y-%m-%d %H:%M'
                        )
                    }
            return None
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao procurar demo: {e}")
            return None

    async def _create_temp_link(self, demo_path):
        """Criar link temporário para download"""
        try:
            # Esta é uma implementação simplificada
            # Em produção, usar um serviço apropriado de compartilhamento
            server_ip = os.getenv('SERVER_IP')
            filename = os.path.basename(demo_path)
            return f"http://{server_ip}/demos/{filename}"
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar link temporário: {e}")
            raise

def setup(bot):
    bot.add_cog(DemoManager(bot))