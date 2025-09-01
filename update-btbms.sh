#!/bin/bash

# BtBmsDisplay Update Script
# This script updates the application with latest changes

set -e  # Exit on any error

echo "🔄 Updating BtBmsDisplay..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Variables
PROJECT_DIR="$HOME/BtBmsDisplay"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found at $PROJECT_DIR"
    echo "   Please run install-btbms-services.sh first"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR"

echo "📁 Working in: $PROJECT_DIR"

# Check if git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Cannot pull updates."
    echo "   Please reinstall using install-btbms-services.sh"
    exit 1
fi

# Stop the service before updating
echo "🛑 Stopping BtBmsDisplay service..."
sudo systemctl stop btbms-display.service || true

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Check if package.json changed
if git diff HEAD~1 HEAD --name-only | grep -q "package.json\|package-lock.json"; then
    echo "📦 Package files changed, updating dependencies..."
    npm install
else
    echo "📦 Installing/updating dependencies..."
    npm install
fi

# Rebuild the application
echo "🔨 Building the application..."
npm run build

# Copy updated service file if it exists
if [ -f "btbms-display.service" ]; then
    echo "⚙️ Updating systemd service file..."
    sudo cp btbms-display.service /etc/systemd/system/
    sudo systemctl daemon-reload
fi

# Start the service
echo "🚀 Starting BtBmsDisplay service..."
sudo systemctl start btbms-display.service

# Wait a moment for service to start
sleep 5

# Check service status
if systemctl is-active --quiet btbms-display.service; then
    echo "✅ BtBmsDisplay service is running"
    
    # Test web service
    if curl -s http://localhost:3000 > /dev/null; then
        echo "✅ Web application is accessible at http://localhost:3000"
    else
        echo "⚠️ Web service may not be ready yet"
    fi
else
    echo "❌ Service failed to start. Check logs:"
    echo "   sudo journalctl -u btbms-display.service -f"
    exit 1
fi

echo ""
echo "🎉 Update complete!"
echo ""
echo "🔧 Useful commands:"
echo "  • Check service status: sudo systemctl status btbms-display.service"
echo "  • View logs: sudo journalctl -u btbms-display.service -f"
echo "  • Check BMS status: curl http://localhost:3000/api/bms/status"
echo "  • Access web app: http://localhost:3000"
