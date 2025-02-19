#!/bin/bash
# Script para executar todos os scripts de configuração

echo "Executando todos os scripts de configuração..."

# Executar scripts de configuração
./initial_setup.sh
./setup_cron_job.sh
./other_setup_scripts.sh