#!/bin/bash
# Script de configuração inicial

echo "Executando configuração inicial..."

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y git docker docker-compose

# Executar scripts de configuração adicionais
./setup_cron_job.sh
./run_all.sh