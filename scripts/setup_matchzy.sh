#!/bin/bash

# Run initial setup
./setup/initial_setup.sh

# Install CS2 server
./scripts/install_cs2_server.sh

# Install CS Demo Manager
./scripts/install_cs_demo_manager.sh

# Start services
./scripts/start_cs2_server.sh

echo "MatchZY setup complete."