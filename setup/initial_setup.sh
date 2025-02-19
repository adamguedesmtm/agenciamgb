#!/bin/bash

# Update package lists
sudo apt-get update

# Install basic packages
sudo apt-get install -y curl wget git

# Set up firewall
sudo ufw allow OpenSSH
sudo ufw enable

# Set up SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Set up dynamic DNS
sudo apt-get install -y ddclient
sudo cp ddclient.conf /etc/ddclient.conf

echo "Initial setup complete."