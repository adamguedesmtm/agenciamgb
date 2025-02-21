"""
Dependency Manager for CS2 Server
Author: adamguedesmtm
Created: 2025-02-21 04:46:16
"""

import sys
import pkg_resources
import subprocess
import asyncio
from typing import List, Dict, Optional
from .logger import Logger

class DependencyManager:
    def __init__(self):
        self.logger = Logger('dependency_manager')
        self.requirements_file = "requirements.txt"
        self._installed_packages = {}
        self._load_installed_packages()

    def _load_installed_packages(self):
        """Carregar pacotes instalados"""
        try:
            self._installed_packages = {
                pkg.key: pkg.version
                for pkg in pkg_resources.working_set
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao carregar pacotes instalados: {e}")

    async def check_dependencies(self) -> Dict[str, str]:
        """Verificar status das dependências"""
        try:
            missing = []
            outdated = []
            required = self._read_requirements()

            for package, version in required.items():
                if package not in self._installed_packages:
                    missing.append(package)
                elif version and version != self._installed_packages[package]:
                    outdated.append(package)

            return {
                'missing': missing,
                'outdated': outdated,
                'installed': len(self._installed_packages),
                'required': len(required)
            }
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar dependências: {e}")
            return {}

    async def install_package(self, package: str, version: str = None) -> bool:
        """Instalar pacote específico"""
        try:
            package_spec = f"{package}"
            if version:
                package_spec += f"=={version}"

            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', package_spec,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._load_installed_packages()
                self.logger.logger.info(f"Pacote {package_spec} instalado")
                return True
            else:
                self.logger.logger.error(
                    f"Erro ao instalar {package_spec}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao instalar pacote: {e}")
            return False

    async def update_package(self, package: str) -> bool:
        """Atualizar pacote específico"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '--upgrade', package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._load_installed_packages()
                self.logger.logger.info(f"Pacote {package} atualizado")
                return True
            else:
                self.logger.logger.error(
                    f"Erro ao atualizar {package}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar pacote: {e}")
            return False

    async def uninstall_package(self, package: str) -> bool:
        """Desinstalar pacote"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'uninstall', '-y', package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._load_installed_packages()
                self.logger.logger.info(f"Pacote {package} desinstalado")
                return True
            else:
                self.logger.logger.error(
                    f"Erro ao desinstalar {package}: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao desinstalar pacote: {e}")
            return False

    def _read_requirements(self) -> Dict[str, Optional[str]]:
        """Ler arquivo requirements.txt"""
        try:
            requirements = {}
            with open(self.requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '==' in line:
                            package, version = line.split('==')
                            requirements[package] = version
                        else:
                            requirements[line] = None
            return requirements
            
        except Exception as e:
            self.logger.logger.error(f"Erro ao ler requirements: {e}")
            return {}

    async def update_requirements(self):
        """Atualizar arquivo requirements.txt"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'freeze',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                with open(self.requirements_file, 'w') as f:
                    f.write(stdout.decode())
                self.logger.logger.info("Arquivo requirements.txt atualizado")
                return True
            else:
                self.logger.logger.error(
                    f"Erro ao gerar requirements: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao atualizar requirements: {e}")
            return False

    async def check_updates(self) -> List[Dict]:
        """Verificar atualizações disponíveis"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                updates = []
                for pkg in eval(stdout.decode()):
                    updates.append({
                        'name': pkg['name'],
                        'current_version': pkg['version'],
                        'latest_version': pkg['latest_version']
                    })
                return updates
            else:
                self.logger.logger.error(
                    f"Erro ao verificar atualizações: {stderr.decode()}"
                )
                return []
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao verificar atualizações: {e}")
            return []

    async def install_requirements(self) -> bool:
        """Instalar todas as dependências do requirements.txt"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '-r', self.requirements_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._load_installed_packages()
                self.logger.logger.info("Dependências instaladas com sucesso")
                return True
            else:
                self.logger.logger.error(
                    f"Erro ao instalar dependências: {stderr.decode()}"
                )
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Erro ao instalar dependências: {e}")
            return False