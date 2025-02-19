#!/bin/bash

# setup/setup_cron_job.sh
# Script para configurar um cron job para executar check_server_status.sh a cada minuto

# Adiciona um cron job para executar check_server_status.sh a cada minuto
(crontab -l 2>/dev/null; echo "* * * * * /bin/bash /var/www/agenciamgb/scripts/check_server_status.sh") | crontab -