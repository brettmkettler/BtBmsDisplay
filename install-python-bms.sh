#!/bin/bash

# Python BMS Installation Script
# Installs Python BMS API server and updates the existing Node.js app to use it

set -e  # Exit on any error

echo "🐍 Installing Python BMS System..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$HOME/BtBmsDisplay"
SERVICE_DIR="/etc/systemd/system"

echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Project directory: $PROJECT_DIR"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install Python dependencies
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for Bluetooth
echo "🔵 Installing Bluetooth dependencies..."
sudo apt install -y \
    bluetooth \
    bluez \
    libbluetooth-dev \
    python3-dev \
    build-essential

# Create project directory if needed
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Creating project directory..."
    mkdir -p "$PROJECT_DIR"
fi

# Copy files if not already there
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Copying project files to $PROJECT_DIR..."
    cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
    chown -R $USER:$USER "$PROJECT_DIR"
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Test Python BMS reader
echo "🧪 Testing Python BMS reader..."
timeout 10s python3 bms_reader.py || echo "BMS reader test completed (timeout expected)"

# Update service files with current user
echo "⚙️ Updating service files with current user..."
sed -i "s/User=seanfuchs/User=$USER/g" "$PROJECT_DIR/bms-python.service"
sed -i "s/Group=seanfuchs/Group=$USER/g" "$PROJECT_DIR/bms-python.service"
sed -i "s|WorkingDirectory=/home/seanfuchs/BtBmsDisplay|WorkingDirectory=$PROJECT_DIR|g" "$PROJECT_DIR/bms-python.service"

sed -i "s/User=seanfuchs/User=$USER/g" "$PROJECT_DIR/btbms-display.service"
sed -i "s/Group=seanfuchs/Group=$USER/g" "$PROJECT_DIR/btbms-display.service"
sed -i "s|WorkingDirectory=/home/seanfuchs/BtBmsDisplay|WorkingDirectory=$PROJECT_DIR|g" "$PROJECT_DIR/btbms-display.service"

# Install Node.js dependencies and rebuild
echo "📦 Installing Node.js dependencies..."
npm install

echo "🔨 Building the project..."
npm run build

# Stop existing services
echo "🛑 Stopping existing services..."
sudo systemctl stop btbms-display.service || true
sudo systemctl stop bms-python.service || true

# Install systemd service files
echo "⚙️ Installing systemd service files..."
sudo cp "$PROJECT_DIR/bms-python.service" "$SERVICE_DIR/"
sudo cp "$PROJECT_DIR/btbms-display.service" "$SERVICE_DIR/"

# Set proper permissions
sudo chmod 644 "$SERVICE_DIR/bms-python.service"
sudo chmod 644 "$SERVICE_DIR/btbms-display.service"

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable bms-python.service
sudo systemctl enable btbms-display.service

# Start Python BMS service first
echo "🚀 Starting Python BMS service..."
sudo systemctl start bms-python.service

# Wait for Python service to be ready
echo "⏳ Waiting for Python BMS service to initialize..."
sleep 5

# Check Python service status
if systemctl is-active --quiet bms-python.service; then
    echo "✅ Python BMS service is running"
else
    echo "⚠️ Python BMS service may not be ready yet"
    sudo systemctl status bms-python.service
fi

# Start Node.js web service
echo "🚀 Starting Node.js web service..."
sudo systemctl start btbms-display.service

# Wait for web service to be ready
echo "⏳ Waiting for web service to start..."
sleep 10

# Check if web service is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Web service is running on port 3000"
else
    echo "⚠️ Web service may not be ready yet. Check with: sudo systemctl status btbms-display.service"
fi

# Check Python API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Python BMS API is responding on port 8000"
else
    echo "⚠️ Python BMS API may not be ready yet. Check with: sudo systemctl status bms-python.service"
fi

echo ""
echo "🎉 Python BMS Installation complete!"
echo ""
echo "📋 Service Status:"
echo "  • Python BMS API: sudo systemctl status bms-python.service"
echo "  • Node.js Web App: sudo systemctl status btbms-display.service"
echo ""
echo "🌐 Access the application:"
echo "  • Web Interface: http://localhost:3000"
echo "  • Python BMS API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Manual Commands:"
echo "  • View Python logs: sudo journalctl -u bms-python.service -f"
echo "  • View Web logs: sudo journalctl -u btbms-display.service -f"
echo "  • Test Python API: curl http://localhost:8000/api/batteries"
echo "  • Restart services: sudo systemctl restart bms-python.service btbms-display.service"
echo ""
echo "🔵 Python BMS Integration:"
echo "  • Uses Python bleak library for reliable BLE communication"
echo "  • Automatic BMS device discovery and connection"
echo "  • Real-time data polling every 2 seconds"
echo "  • Web UI polls Python API instead of direct BLE"
echo ""
