#!/bin/bash

CATEGORY=$1

if [ -z "$CATEGORY" ]; then
  echo "Usage: start_cs2_server.sh <category>"
  exit 1
fi

# Start the CS2 server with the specified category
echo "Starting CS2 server for category: $CATEGORY"
cs2-server --category "$CATEGORY"