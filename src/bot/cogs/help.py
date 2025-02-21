"""
Help Command Manager
Author: adamguedesmtm
Created: 2025-02-21 13:47:53
"""

import discord
from discord.ext import commands
from typing import Optional

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, command: Optional[str] = None):
        """Mostrar ajuda dos comandos"""
        try:
            if command:
                await self.show_command_help(ctx, command)
            else:
                await self.show_all_help(ctx)

        except Exception as e:
            self.bot.logger.logger.error(f"Erro ao mostrar ajuda: {e}")
            await ctx.send("❌ Erro ao mostrar ajuda!")

    async def show_all_help(self, ctx):
        """Mostrar todos os comandos"""
        embed = discord.Embed(
            title="📚 Comandos Disponíveis",
            description="Use !help <comando> para mais detalhes",
            color=discord.Color.blue()
        )

        # Comandos Competitivo
        competitive = [
            "!queue5v5 - Entrar na fila 5v5",
            "!leave - Sair da fila",
            "!status - Ver status da fila"
        ]
        embed.add_field(
            name="🎮 Competitivo 5v5",
            value="\n".join(competitive),
            inline=False
        )

        # Comandos Wingman
        wingman = [
            "!queue2v2 - Entrar na fila 2v2",
            "!leave2v2 - Sair da fila 2v2",
            "!wingmanstatus - Ver status da fila 2v2"
        ]
        embed.add_field(
            name="👥 Wingman 2v2",
            value="\n".join(wingman),
            inline=False
        )

        # Comandos Retake
        retake = [
            "!queueretake - Entrar na fila retake",
            "!leaveretake - Sair da fila retake",
            "!retakestatus - Ver status da fila retake"
        ]
        embed.add_field(
            name="🔄 Retake",
            value="\n".join(retake),
            inline=False
        )

        # Comandos Admin (só mostrar se o usuário for admin)
        if ctx.author.guild_permissions.administrator:
            admin = [
                "!clearqueue <tipo> - Limpar fila específica",
                "!forcemap <servidor> <mapa> - Forçar troca de mapa",
                "!kickplayer <servidor> <jogador> - Kickar jogador",
                "!serverinfo <servidor> - Ver info do servidor",
                "!restartserver <servidor> - Reiniciar servidor"
            ]
            embed.add_field(
                name="⚙️ Administração",
                value="\n".join(admin),
                inline=False
            )

        await ctx.send(embed=embed)

    async def show_command_help(self, ctx, command: str):
        """Mostrar ajuda de um comando específico"""
        cmd = self.bot.get_command(command)
        
        if not cmd:
            await ctx.send(f"❌ Comando `{command}` não encontrado!")
            return

        embed = discord.Embed(
            title=f"📖 Ajuda: {cmd.name}",
            color=discord.Color.blue()
        )

        # Descrição do comando
        embed.add_field(
            name="Descrição",
            value=cmd.help or "Sem descrição disponível",
            inline=False
        )

        # Uso do comando
        usage = f"!{cmd.name}"
        if cmd.signature:
            usage += f" {cmd.signature}"
        embed.add_field(
            name="Uso",
            value=f"`{usage}`",
            inline=False
        )

        # Permissões necessárias
        if cmd.checks:
            perms = []
            for check in cmd.checks:
                if hasattr(check, "__qualname__"):
                    if "has_permissions" in check.__qualname__:
                        perms.append("Administrador")
                    elif "has_role" in check.__qualname__:
                        perms.append("Cargo específico")
            if perms:
                embed.add_field(
                    name="Permissões Necessárias",
                    value=", ".join(perms),
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))