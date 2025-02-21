"""
Admin Commands Manager
Author: adamguedesmtm
Created: 2025-02-21 13:45:30
"""

import discord
from discord.ext import commands
from typing import Optional

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearqueue(self, ctx, queue_type: str):
        """Limpar fila específica"""
        try:
            if queue_type not in ['competitive', 'wingman', 'retake']:
                await ctx.send("❌ Tipo de fila inválido! Use: competitive, wingman ou retake")
                return

            # Limpar fila
            cleared = await self.bot.queue.clear_queue(queue_type)
            
            if cleared:
                await ctx.send(f"✅ Fila {queue_type} foi limpa!")
            else:
                await ctx.send(f"❌ Erro ao limpar fila {queue_type}")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao limpar fila: {e}")
            await ctx.send("❌ Erro ao executar comando!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcemap(self, ctx, server_type: str, map_name: str):
        """Forçar troca de mapa"""
        try:
            if server_type == 'competitive':
                success = await self.bot.matchzy.change_map(map_name)
            elif server_type == 'wingman':
                success = await self.bot.wingman.change_map(map_name)
            elif server_type == 'retake':
                success = await self.bot.retake.change_map(map_name)
            else:
                await ctx.send("❌ Tipo de servidor inválido! Use: competitive, wingman ou retake")
                return

            if success:
                await ctx.send(f"✅ Mapa alterado para {map_name}!")
            else:
                await ctx.send(f"❌ Erro ao alterar mapa!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao trocar mapa: {e}")
            await ctx.send("❌ Erro ao executar comando!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def kickplayer(self, ctx, server_type: str, player_name: str):
        """Kickar jogador de um servidor"""
        try:
            if server_type == 'competitive':
                success = await self.bot.matchzy.kick_player(player_name)
            elif server_type == 'wingman':
                success = await self.bot.wingman.kick_player(player_name)
            elif server_type == 'retake':
                success = await self.bot.retake.kick_player(player_name)
            else:
                await ctx.send("❌ Tipo de servidor inválido! Use: competitive, wingman ou retake")
                return

            if success:
                await ctx.send(f"✅ Jogador {player_name} foi kickado!")
            else:
                await ctx.send(f"❌ Erro ao kickar jogador!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao kickar jogador: {e}")
            await ctx.send("❌ Erro ao executar comando!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def serverinfo(self, ctx, server_type: str):
        """Ver informações do servidor"""
        try:
            if server_type == 'competitive':
                info = await self.bot.matchzy.get_server_info()
            elif server_type == 'wingman':
                info = await self.bot.wingman.get_server_info()
            elif server_type == 'retake':
                info = await self.bot.retake.get_server_info()
            else:
                await ctx.send("❌ Tipo de servidor inválido! Use: competitive, wingman ou retake")
                return

            embed = discord.Embed(
                title=f"ℹ️ Informações do Servidor {server_type.title()}",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="IP",
                value=f"`{info['ip']}:{info['port']}`",
                inline=False
            )

            embed.add_field(
                name="Mapa Atual",
                value=info['map'],
                inline=True
            )

            embed.add_field(
                name="Jogadores",
                value=f"{info['players_online']}/{info['max_players']}",
                inline=True
            )

            embed.add_field(
                name="Status",
                value=info['status'],
                inline=True
            )

            await ctx.send(embed=embed)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao obter info do servidor: {e}")
            await ctx.send("❌ Erro ao executar comando!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restartserver(self, ctx, server_type: str):
        """Reiniciar servidor"""
        try:
            embed = discord.Embed(
                title="⚠️ Confirmação de Reinício",
                description=f"Você tem certeza que deseja reiniciar o servidor {server_type}?",
                color=discord.Color.yellow()
            )

            confirm_msg = await ctx.send(embed=embed)
            await confirm_msg.add_reaction('✅')
            await confirm_msg.add_reaction('❌')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == '✅':
                    # Reiniciar servidor
                    if server_type == 'competitive':
                        success = await self.bot.matchzy.restart_server()
                    elif server_type == 'wingman':
                        success = await self.bot.wingman.restart_server()
                    elif server_type == 'retake':
                        success = await self.bot.retake.restart_server()
                    else:
                        await ctx.send("❌ Tipo de servidor inválido! Use: competitive, wingman ou retake")
                        return

                    if success:
                        await ctx.send(f"✅ Servidor {server_type} está reiniciando!")
                    else:
                        await ctx.send(f"❌ Erro ao reiniciar servidor!")
                else:
                    await ctx.send("❌ Reinício cancelado!")

            except asyncio.TimeoutError:
                await ctx.send("⏰ Tempo esgotado! Reinício cancelado.")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao reiniciar servidor: {e}")
            await ctx.send("❌ Erro ao executar comando!")

async def setup(bot):
    await bot.add_cog(Admin(bot))