"""
Hierarchical Role System
Author: adamguedesmtm
Created: 2025-02-21 14:12:25
"""

from typing import Dict, List, Optional, Tuple
import discord
from .logger import Logger
from .metrics import MetricsManager
from .stats_manager import StatsManager

class RoleSystem:
    def __init__(self, 
                 stats_manager: StatsManager,
                 logger: Optional[Logger] = None,
                 metrics: Optional[MetricsManager] = None):
        self.stats_manager = stats_manager
        self.logger = logger or Logger('role_system')
        self.metrics = metrics

        # Roles Genéricas (Múltiplos jogadores podem ter)
        self.generic_roles = {
            # Roles de Nível (Baseadas em horas jogadas)
            'Novice 🌱': {'hours_played': 10, 'priority': 1, 'color': 0x98FB98},
            'Regular 🌿': {'hours_played': 50, 'priority': 2, 'color': 0x32CD32},
            'Veteran 🌳': {'hours_played': 200, 'priority': 3, 'color': 0x228B22},
            'Elite 🎮': {'hours_played': 500, 'priority': 4, 'color': 0x006400},
            
            # Roles de K/D
            'Recruit ⭐': {'kd_ratio': 0.8, 'priority': 1, 'color': 0xC0C0C0},
            'Soldier ⭐⭐': {'kd_ratio': 1.0, 'priority': 2, 'color': 0xB8860B},
            'Warrior ⭐⭐⭐': {'kd_ratio': 1.5, 'priority': 3, 'color': 0xDAA520},
            'Legend ⭐⭐⭐⭐': {'kd_ratio': 2.0, 'priority': 4, 'color': 0xFFD700},
            
            # Roles de Precisão
            'Shooter 🎯': {'hs_ratio': 0.3, 'priority': 1, 'color': 0xADD8E6},
            'Marksman 🎯🎯': {'hs_ratio': 0.5, 'priority': 2, 'color': 0x87CEEB},
            'Sniper 🎯🎯🎯': {'hs_ratio': 0.7, 'priority': 3, 'color': 0x4169E1},
            
            # Roles de Utilidade
            'Support 🛠️': {'utility_score': 50, 'priority': 1, 'color': 0xDDA0DD},
            'Tactician 🛠️🛠️': {'utility_score': 100, 'priority': 2, 'color': 0xBA55D3},
            'Strategist 🛠️🛠️🛠️': {'utility_score': 200, 'priority': 3, 'color': 0x9400D3}
        }

        # Roles Únicas (Só o melhor jogador pode ter)
        self.unique_roles = {
            # Roles de Combate
            'Kill Leader 👑': {'metric': 'kills', 'priority': 5, 'color': 0xFF0000},
            'Headshot King 🎯': {'metric': 'headshots', 'priority': 5, 'color': 0xFFD700},
            'Clutch Master 🏆': {'metric': 'clutches_won', 'priority': 5, 'color': 0x9400D3},
            'Entry Fragger Supreme ⚡': {'metric': 'entry_kills', 'priority': 5, 'color': 0x32CD32},
            
            # Roles de Utilidade
            'Flash God 💡': {'metric': 'enemies_flashed', 'priority': 5, 'color': 0xFFFF00},
            'Smoke Lord 💨': {'metric': 'smokes_thrown', 'priority': 5, 'color': 0x808080},
            'Molotov King 🔥': {'metric': 'molotovs_thrown', 'priority': 5, 'color': 0xFF4500},
            
            # Roles de Objetivo
            'Plant Master 💣': {'metric': 'bombs_planted', 'priority': 5, 'color': 0xDC143C},
            'Defuse Expert 🔧': {'metric': 'bombs_defused', 'priority': 5, 'color': 0x00FF00},
            
            # Roles Especiais
            'MVP Champion 🏅': {'metric': 'mvps', 'priority': 6, 'color': 0xFFD700},
            'Damage Dealer 💥': {'metric': 'damage_dealt', 'priority': 6, 'color': 0xFF8C00},
            'Accuracy God 🎯': {'metric': 'accuracy', 'priority': 6, 'color': 0x4169E1}
        }

    async def update_roles(self, guild: discord.Guild):
        """Atualizar roles dinamicamente."""
        try:
            all_stats = await self.stats_manager.get_all_players_stats()

            for member in guild.members:
                if str(member.id) in all_stats:
                    stats = all_stats[str(member.id)]

                    # Remover roles antigas
                    current_roles = [r for r in member.roles if r.name in self.generic_roles or r.name in self.unique_roles]
                    await member.remove_roles(*current_roles)

                    # Adicionar roles genéricas
                    generic_roles = []
                    for role_name, requirements in self.generic_roles.items():
                        if self._meets_requirements(stats, requirements):
                            generic_roles.append(await self._get_or_create_role(guild, role_name, requirements))

                    # Adicionar roles únicas
                    unique_roles = []
                    for role_name, metric in self.unique_roles.items():
                        top_player = await self.stats_manager.get_top_player(metric)
                        if top_player and top_player['id'] == member.id:
                            unique_roles.append(await self._get_or_create_role(guild, role_name, {'color': 0xFFD700}))

                    # Aplicar roles
                    await member.add_roles(*generic_roles, *unique_roles)
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar roles: {e}")
            
    async def _update_generic_roles(self, member: discord.Member, guild: discord.Guild, stats: Dict):
        """Atualizar roles genéricas de um membro"""
        try:
            current_roles = []

            for role_name, requirements in self.generic_roles.items():
                if self._meets_requirements(stats, requirements):
                    role = await self._get_or_create_role(guild, role_name, requirements)
                    current_roles.append((role, requirements['priority']))

            # Manter apenas a role de maior prioridade para cada categoria
            final_roles = self._filter_highest_priority_roles(current_roles)
            
            # Atualizar roles do membro
            current_generic_roles = [r for r in member.roles if r.name in self.generic_roles]
            roles_to_remove = set(current_generic_roles) - set(r[0] for r in final_roles)
            roles_to_add = set(r[0] for r in final_roles) - set(current_generic_roles)

            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            if roles_to_add:
                await member.add_roles(*roles_to_add)

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar roles genéricas: {e}")

    async def _update_unique_roles(self, guild: discord.Guild, all_stats: Dict):
        """Atualizar roles únicas baseado em rankings"""
        try:
            for role_name, role_info in self.unique_roles.items():
                metric = role_info['metric']
                
                # Ordenar jogadores pela métrica
                sorted_players = sorted(
                    all_stats.items(),
                    key=lambda x: x[1].get(metric, 0),
                    reverse=True
                )

                # Obter top 3 jogadores
                top_players = sorted_players[:3]
                
                if not top_players:
                    continue

                # Criar roles para top 3
                roles = {
                    0: (f"{role_name}", role_info['color']),
                    1: (f"{role_name} Runner-up 🥈", self._adjust_color(role_info['color'], 0.8)),
                    2: (f"{role_name} Third Place 🥉", self._adjust_color(role_info['color'], 0.6))
                }

                # Atribuir roles
                for idx, (player_id, _) in enumerate(top_players):
                    member = guild.get_member(int(player_id))
                    if member:
                        role_name, color = roles[idx]
                        role = await self._get_or_create_role(guild, role_name, {'color': color, 'priority': role_info['priority']})
                        
                        # Remover outras roles da mesma categoria
                        for r in member.roles:
                            if any(r.name.startswith(base_name) for base_name in self.unique_roles.keys()):
                                await member.remove_roles(r)
                        
                        # Adicionar nova role
                        await member.add_roles(role)

        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar roles únicas: {e}")

    def _meets_requirements(self, stats: Dict, requirements: Dict) -> bool:
        """Verificar se jogador atende aos requisitos da role"""
        for stat, value in requirements.items():
            if stat in ['priority', 'color']:
                continue
            if stat not in stats or stats[stat] < value:
                return False
        return True

    def _filter_highest_priority_roles(self, roles: List[Tuple[discord.Role, int]]) -> List[Tuple[discord.Role, int]]:
        """Filtrar apenas as roles de maior prioridade para cada categoria"""
        categories = {}
        for role, priority in roles:
            category = self._get_role_category(role.name)
            if category not in categories or categories[category][1] < priority:
                categories[category] = (role, priority)
        return list(categories.values())

    def _get_role_category(self, role_name: str) -> str:
        """Obter categoria da role baseado no nome"""
        if '⭐' in role_name:
            return 'combat'
        if '🌱' in role_name or '🌿' in role_name or '🌳' in role_name:
            return 'level'
        if '🎯' in role_name:
            return 'accuracy'
        if '🛠️' in role_name:
            return 'utility'
        return 'other'

    def _adjust_color(self, color: int, factor: float) -> int:
        """Ajustar cor para versões mais claras/escuras"""
        r = int(((color >> 16) & 0xFF) * factor)
        g = int(((color >> 8) & 0xFF) * factor)
        b = int((color & 0xFF) * factor)
        return (r << 16) + (g << 8) + b

    async def _get_or_create_role(self, guild: discord.Guild, role_name: str, 
                                 role_info: Dict) -> discord.Role:
        """Obter role existente ou criar nova"""
        try:
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = await guild.create_role(
                    name=role_name,
                    color=discord.Color(role_info['color']),
                    hoist=True,
                    mentionable=True
                )
                await role.edit(position=role_info['priority'])
                self.logger.logger.info(f"Role criada: {role_name}")
            return role
        except Exception as e:
            self.logger.logger.error(f"Erro ao criar/obter role: {e}")
            return None