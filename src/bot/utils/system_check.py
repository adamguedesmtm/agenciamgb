"""
System Requirements Check
Author: adamguedesmtm
Created: 2025-02-21
"""

import os
import sys
import platform
from .logger import Logger

def check_system_requirements():
    logger = Logger('system_check')
    requirements = {
        'Python Version': '3.8',
        'Min RAM': 8,  # GB
        'Min Disk': 256  # GB
    }

    # Verificar versão Python
    python_version = platform.python_version()
    if python_version < requirements['Python Version']:
        error = f"Python {requirements['Python Version']}+ required"
        logger.logger.error(error)
        raise SystemError(error)

    # Verificar RAM
    total_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3)
    if total_ram < requirements['Min RAM']:
        error = f"Minimum {requirements['Min RAM']}GB RAM required"
        logger.logger.error(error)
        raise SystemError(error)

    # Verificar espaço em disco
    disk = os.statvfs('/')
    total_disk = (disk.f_blocks * disk.f_frsize) / (1024**3)
    if total_disk < requirements['Min Disk']:
        error = f"Minimum {requirements['Min Disk']}GB disk space required"
        logger.logger.error(error)
        raise SystemError(error)

    logger.logger.info("System requirements check passed")