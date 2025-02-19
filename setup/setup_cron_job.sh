#!/bin/bash
# Script para configurar cron jobs

echo "Configurando cron jobs..."

# Adicionar cron job para processar demos a cada hora
(crontab -l 2>/dev/null; echo "0 * * * * /path/to/process_demos.php") | crontab -