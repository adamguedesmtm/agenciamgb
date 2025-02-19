#!/bin/bash

# Update package lists
sudo apt-get update

# Install necessary packages
sudo apt-get install -y cs-demo-manager

# Configure demo manager
sudo cp demo-manager-config /etc/cs-demo-manager/config

echo "CS Demo Manager installed and configured."