#!/bin/bash

# Update package lists
sudo apt-get update

# Install necessary packages
sudo apt-get install -y cs2-server

# Configure CS2 server
sudo cp cs2-server-config /etc/cs2-server/config

echo "CS2 server installed and configured."