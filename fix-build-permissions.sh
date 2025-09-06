#!/bin/bash

echo "Fixing build permissions and rebuilding..."

# Stop the UI service
echo "Stopping j5-ui service..."
sudo systemctl stop j5-ui

# Remove dist directory with sudo to handle permission issues
echo "Removing dist directory..."
sudo rm -rf dist/

# Fix ownership to current user
echo "Fixing ownership..."
sudo chown -R $(whoami):$(whoami) .

# Set proper write permissions
echo "Setting permissions..."
chmod -R u+w .

# Update browserslist database
echo "Updating browserslist..."
npx update-browserslist-db@latest

# Rebuild the project
echo "Rebuilding project..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build successful!"
    
    # Restart the UI service
    echo "Restarting j5-ui service..."
    sudo systemctl start j5-ui
    
    # Wait a moment and check status
    sleep 3
    echo "Checking service status..."
    sudo systemctl status j5-ui --no-pager -l
else
    echo "Build failed! Check the error messages above."
    exit 1
fi

echo "Build permissions fixed and project rebuilt!"
echo "If service is still failing, check logs with: sudo journalctl -u j5-ui -f"
