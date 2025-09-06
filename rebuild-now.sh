#!/bin/bash

echo "Rebuilding with updated vite.ts..."

# Stop the service
sudo systemctl stop j5-ui

# Remove old compiled code
sudo rm -rf dist/

# Fix permissions
sudo chown -R $(whoami):$(whoami) .

# Rebuild
npm run build

# Start service
sudo systemctl start j5-ui

# Check status
sleep 2
sudo systemctl status j5-ui --no-pager -l
