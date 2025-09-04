#!/bin/bash

# Install UI and setup service script
# This script installs dependencies and creates a systemd service for the UI

set -e

echo "=== Installing UI Dependencies and Setting up Service ==="

# Get current directory
INSTALL_DIR=$(pwd)
SERVICE_NAME="j5-ui"

echo "Installation directory: $INSTALL_DIR"

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Make sure you're in the correct directory."
    exit 1
fi

npm install

# Build the UI
echo "Building UI..."
npm run build

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=J5 Console UI Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo ""
echo "✓ UI dependencies installed"
echo "✓ UI built successfully"
echo "✓ Service '${SERVICE_NAME}' created and enabled"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "The UI will be available at: http://localhost:3000"
echo "Kiosk will automatically start and open the UI in fullscreen mode"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
