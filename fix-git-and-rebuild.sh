#!/bin/bash

echo "Fixing git permissions and rebuilding..."

# Fix git permissions
echo "Fixing git permissions..."
sudo chown -R $(whoami):$(whoami) .git/

# Stop the service
echo "Stopping j5-ui service..."
sudo systemctl stop j5-ui

# Remove old compiled code
echo "Removing old dist..."
sudo rm -rf dist/

# Fix all permissions
echo "Fixing file permissions..."
sudo chown -R $(whoami):$(whoami) .

# Rebuild with updated vite.ts
echo "Rebuilding project..."
npm run build

# Start service
echo "Starting j5-ui service..."
sudo systemctl start j5-ui

# Check status
echo "Checking service status..."
sleep 3
sudo systemctl status j5-ui --no-pager -l

echo "Done! If service is running, the import.meta.dirname issue should be fixed."
