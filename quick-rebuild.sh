#!/bin/bash

echo "=== Quick Rebuild Script ==="
echo "Fixing client build directory issue and rebuilding entire project..."

# Stop the UI service first
echo "Stopping j5-ui service..."
sudo systemctl stop j5-ui

# Remove any existing build artifacts
echo "Cleaning build artifacts..."
sudo rm -rf dist/
sudo rm -rf client/dist/

# Fix ownership issues that might prevent building
echo "Fixing ownership and permissions..."
sudo chown -R $(whoami):$(whoami) .
chmod -R u+w .

# Install/update dependencies
echo "Installing dependencies..."
npm install

# Update browserslist database
echo "Updating browserslist..."
npx update-browserslist-db@latest

# Build the project (this builds both client and server)
echo "Building project..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Verify client dist directory exists
    if [ -d "client/dist" ]; then
        echo "✅ Client build directory created successfully"
        ls -la client/dist/
    else
        echo "❌ Client build directory still missing!"
        exit 1
    fi
    
    # Verify server dist exists
    if [ -d "dist" ]; then
        echo "✅ Server build directory created successfully"
        ls -la dist/
    else
        echo "❌ Server build directory missing!"
        exit 1
    fi
    
    # Restart the UI service
    echo "Restarting j5-ui service..."
    sudo systemctl start j5-ui
    
    # Wait and check status
    sleep 5
    echo "Checking service status..."
    sudo systemctl status j5-ui --no-pager -l
    
    echo ""
    echo "=== Service Logs (last 10 lines) ==="
    sudo journalctl -u j5-ui -n 10 --no-pager
    
else
    echo "❌ Build failed! Check the error messages above."
    exit 1
fi

echo ""
echo "=== Rebuild Complete ==="
echo "If service is still failing, check logs with: sudo journalctl -u j5-ui -f"
echo "UI should be available at: http://localhost:3000"
