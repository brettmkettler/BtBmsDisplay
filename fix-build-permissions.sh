#!/bin/bash

echo "Fixing build permissions..."

# Stop the UI service first
sudo systemctl stop j5-ui.service

# Remove the dist directory completely and recreate it
if [ -d "dist" ]; then
    echo "Removing existing dist directory..."
    sudo rm -rf dist
fi

# Create new dist directory with proper permissions
mkdir -p dist
chmod 755 dist

# Fix ownership of the entire project directory
echo "Fixing ownership..."
sudo chown -R $(whoami):$(whoami) .

# Make sure all files are writable by owner
chmod -R u+w .

echo "✓ Permissions fixed"

# Update browserslist database
echo "Updating browserslist database..."
npx update-browserslist-db@latest

# Build the project
echo "Building project..."
npm run build

if [ $? -eq 0 ]; then
    echo "✓ Build successful"
    
    # Start the UI service
    sudo systemctl start j5-ui.service
    echo "✓ UI service started"
    
    echo ""
    echo "Service status:"
    sudo systemctl status j5-ui.service --no-pager
else
    echo "✗ Build failed"
    exit 1
fi
