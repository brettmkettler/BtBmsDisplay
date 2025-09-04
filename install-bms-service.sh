#!/bin/bash

# Install BMS API service script
# This script creates a systemd service for the Python BMS API

set -e

echo "=== Installing BMS API Service ==="

# Get current directory
INSTALL_DIR=$(pwd)
SERVICE_NAME="j5-bms-api"
VENV_PATH="/home/seanfuchs/Desktop/venv"

echo "Installation directory: $INSTALL_DIR"
echo "Virtual environment: $VENV_PATH"

# Add user to bluetooth group
echo "Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Check if dual_bms_service.py exists
if [ ! -f "dual_bms_service.py" ]; then
    echo "Error: dual_bms_service.py not found. Make sure you're in the correct directory."
    exit 1
fi

# Fix file permissions
echo "Setting file permissions..."
chmod +r dual_bms_service.py
chmod +x dual_bms_service.py

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
Group=bluetooth
WorkingDirectory=${INSTALL_DIR}
Environment=PYTHONPATH=${INSTALL_DIR}
Environment=PATH=${VENV_PATH}/bin:\$PATH
Environment=PYTHONUNBUFFERED=1
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=${VENV_PATH}/bin/python dual_bms_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN

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
