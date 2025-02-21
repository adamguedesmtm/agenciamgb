"""
Permission Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:46:16
"""
import json
from typing import Dict, List, Set, Optional
from .logger import Logger

class PermissionManager:
    def __init__(self):
        self.logger = Logger('permission_manager')
        self._roles = {}
        self._user_roles = {}
        self._permissions = set()

    def add_role(self, role_name: str, permissions: List[str]):
        """Adicionar novo cargo"""
        try:
            self._roles[role_name] = set(permissions)
            self.logger.logger.info(f"Cargo {role_name} adicionado")
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar cargo: {e}")

    def remove_role(self, role_name: str):
        """Remover cargo"""
        try:
            if role_name in self._roles:
                del self._roles[role_name]
                # Remover cargo dos usuários
                for user_id in list(self._user_roles.keys()):
                    self._user_roles[user_id].discard(role_name)
                self.logger.logger.info(f"Cargo {role_name} removido")
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover cargo: {e}")

    def assign_role(self, user_id: str, role_name: str):
        """Atribuir cargo a usuário"""
        try:
            if role_name not in self._roles:
                raise ValueError(f"Cargo {role_name} não existe")

            if user_id not in self._user_roles:
                self._user_roles[user_id] = set()

            self._user_roles[user_id].add(role_name)
            self.logger.logger.info(f"Cargo {role_name} atribuído ao usuário {user_id}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao atribuir cargo: {e}")

    def revoke_role(self, user_id: str, role_name: str):
        """Revogar cargo de usuário"""
        try:
            if user_id in self._user_roles:
                self._user_roles[user_id].discard(role_name)
                self.logger.logger.info(f"Cargo {role_name} revogado do usuário {user_id}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao revogar cargo: {e}")

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Verificar se usuário tem permissão"""
        try:
            if user_id not in self._user_roles:
                return False

            user_roles = self._user_roles[user_id]
            for role in user_roles:
                if role in self._roles and permission in self._roles[role]:
                    return True
            return False
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar permissão: {e}")
            return False

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Obter todas as permissões do usuário"""
        try:
            if user_id not in self._user_roles:
                return set()

            permissions = set()
            for role in self._user_roles[user_id]:
                if role in self._roles:
                    permissions.update(self._roles[role])
            return permissions
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter permissões: {e}")
            return set()

    def get_role_permissions(self, role_name: str) -> Set[str]:
        """Obter permissões de um cargo"""
        try:
            return self._roles.get(role_name, set())
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter permissões do cargo: {e}")
            return set()

    def get_user_roles(self, user_id: str) -> Set[str]:
        """Obter cargos do usuário"""
        try:
            return self._user_roles.get(user_id, set())
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter cargos do usuário: {e}")
            return set()

    def add_permission_to_role(self, role_name: str, permission: str):
        """Adicionar permissão a cargo"""
        try:
            if role_name in self._roles:
                self._roles[role_name].add(permission)
                self._permissions.add(permission)
                self.logger.logger.info(
                    f"Permissão {permission} adicionada ao cargo {role_name}"
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao adicionar permissão: {e}")

    def remove_permission_from_role(self, role_name: str, permission: str):
        """Remover permissão de cargo"""
        try:
            if role_name in self._roles:
                self._roles[role_name].discard(permission)
                self.logger.logger.info(
                    f"Permissão {permission} removida do cargo {role_name}"
                )
        except Exception as e:
            self.logger.logger.error(f"Erro ao remover permissão: {e}")

    def get_all_roles(self) -> Dict[str, Set[str]]:
        """Obter todos os cargos e suas permissões"""
        try:
            return self._roles.copy()
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter cargos: {e}")
            return {}

    def get_all_permissions(self) -> Set[str]:
        """Obter todas as permissões registradas"""
        try:
            return self._permissions.copy()
        except Exception as e:
            self.logger.logger.error(f"Erro ao obter permissões: {e}")
            return set()

    def clear_user_roles(self, user_id: str):
        """Remover todos os cargos de um usuário"""
        try:
            if user_id in self._user_roles:
                del self._user_roles[user_id]
                self.logger.logger.info(f"Cargos do usuário {user_id} removidos")
        except Exception as e:
            self.logger.logger.error(f"Erro ao limpar cargos: {e}")

    def save_to_file(self, filename: str):
        """Salvar configurações em arquivo"""
        try:
            data = {
                'roles': {
                    role: list(perms)
                    for role, perms in self._roles.items()
                },
                'user_roles': {
                    user: list(roles)
                    for user, roles in self._user_roles.items()
                },
                'permissions': list(self._permissions)
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            self.logger.logger.info(f"Configurações salvas em {filename}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao salvar configurações: {e}")

    def load_from_file(self, filename: str):
        """Carregar configurações de arquivo"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self._roles = {
                role: set(perms)
                for role, perms in data['roles'].items()
            }
            self._user_roles = {
                user: set(roles)
                for user, roles in data['user_roles'].items()
            }
            self._permissions = set(data['permissions'])
            
            self.logger.logger.info(f"Configurações carregadas de {filename}")
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar configurações: {e}")
    def initialize_default_roles(self):
        """Inicializar cargos padrão"""
        try:
            # Admin
            self.add_role('admin', [
                'manage_server',
                'manage_users',
                'manage_roles',
                'manage_bans',
                'manage_maps',
                'view_logs',
                'manage_config',
                'restart_server'
            ])

            # Moderador
            self.add_role('mod', [
                'manage_users',
                'manage_bans',
                'view_logs'
            ])

            # VIP
            self.add_role('vip', [
                'reserved_slot',
                'custom_tags',
                'vote_map'
            ])

            self.logger.logger.info("Cargos padrão inicializados")
        except Exception as e:
            self.logger.logger.error(f"Erro ao inicializar cargos padrão: {e}")