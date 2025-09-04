#!/bin/bash

# Install BMS API service script
# This script creates a systemd service for the Python BMS API

set -e

echo "=== Installing BMS API Service ==="

# Get current directory
INSTALL_DIR=$(pwd)
SERVICE_NAME="j5-bms-api"

echo "Installation directory: $INSTALL_DIR"

# Check if dual_bms_service.py exists
if [ ! -f "dual_bms_service.py" ]; then
    echo "Error: dual_bms_service.py not found. Make sure you're in the correct directory."
    exit 1
fi

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=J5 Console BMS API Service
After=network.target bluetooth.target
Wants=network.target bluetooth.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=/usr/bin/python3 dual_bms_service.py
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
echo "✓ BMS API service '${SERVICE_NAME}' created and enabled"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "The BMS API will be available at: http://localhost:8000"
echo "Endpoints: /api/batteries, /api/batteries/left, /api/batteries/right"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To start both services (BMS API + UI):"
echo "  sudo systemctl start ${SERVICE_NAME} j5-ui"
