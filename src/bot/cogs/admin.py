"""
Admin Cog - Administrative commands for bot management
Author: adamguedesmtm
Created: 2025-02-21 14:18:04
"""

import discord
from discord.ext import commands
from typing import Optional

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="updateroles")
    @commands.has_permissions(administrator=True)
    async def force_role_update(self, ctx):
        """Forçar atualização de roles"""
        try:
            await ctx.send("🔄 Iniciando atualização de roles...")
            await self.bot.get_cog('Stats').role_system.update_roles(ctx.guild)
            await ctx.send("✅ Roles atualizadas!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao atualizar roles: {e}")
            await ctx.send("❌ Ocorreu um erro ao atualizar roles!")
            
    @commands.command(name="forcebackup")
    @commands.has_permissions(administrator=True)
    async def force_backup(self, ctx):
        """Forçar criação de backup."""
        try:
            await ctx.send("🔄 Criando backup...")
            success = await self.bot.server_monitor._create_backup()
            if success:
                await ctx.send("✅ Backup criado com sucesso!")
            else:
                await ctx.send("❌ Falha ao criar backup!")

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao criar backup: {e}")
            await ctx.send("❌ Ocorreu um erro ao criar backup!")    
    @commands.command(name="resetstats")
    @commands.has_permissions(administrator=True)
    async def reset_stats(self, ctx, member: discord.Member):
        """Resetar estatísticas de um jogador"""
        try:
            confirm = await ctx.send(
                f"⚠️ Tem certeza que deseja resetar as stats de {member.mention}?\n"
                f"Reaja com ✅ para confirmar ou ❌ para cancelar."
            )
            
            await confirm.add_reaction("✅")
            await confirm.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

            reaction, _ = await self.bot.wait_for('reaction_add', check=check)

            if str(reaction.emoji) == "✅":
                await self.bot.stats_manager.reset_player_stats(member.id)
                await ctx.send(f"✅ Estatísticas de {member.mention} foram resetadas!")
            else:
                await ctx.send("❌ Operação cancelada!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao resetar stats: {e}")
            await ctx.send("❌ Ocorreu um erro ao resetar estatísticas!")

    @commands.command(name="setrole")
    @commands.has_permissions(administrator=True)
    async def set_role(self, ctx, member: discord.Member, *, role_name: str):
        """Definir role manualmente"""
        try:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not role:
                await ctx.send(f"❌ Role '{role_name}' não encontrada!")
                return

            await member.add_roles(role)
            await ctx.send(f"✅ Role {role.name} adicionada a {member.mention}!")

        except Exception as e:
            self.bot.logger.error(f"Erro ao definir role: {e}")
            await ctx.send("❌ Ocorreu um erro ao definir role!")

async def setup(bot):
    await bot.add_cog(Admin(bot))