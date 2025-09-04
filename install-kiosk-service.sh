#!/bin/bash

# Install Kiosk service script
# This script creates a systemd service for the kiosk display

set -e

echo "=== Installing Kiosk Service ==="

# Get current directory
INSTALL_DIR=$(pwd)
SERVICE_NAME="j5-kiosk"

echo "Installation directory: $INSTALL_DIR"

# Check if start_kiosk.sh exists
if [ ! -f "start_kiosk.sh" ]; then
    echo "Error: start_kiosk.sh not found. Make sure you're in the correct directory."
    exit 1
fi

# Make start_kiosk.sh executable
chmod +x start_kiosk.sh

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=J5 Console Kiosk Display
After=graphical-session.target j5-ui.service
Wants=j5-ui.service
Requires=graphical-session.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
ExecStart=$INSTALL_DIR/start_kiosk.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOF

# Reload systemd and enable service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo ""
echo "✓ Kiosk service '${SERVICE_NAME}' created and enabled"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "The kiosk will automatically start Chromium in fullscreen mode"
echo "pointing to http://localhost:3000"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To start all services (BMS API + UI + Kiosk):"
echo "  sudo systemctl start j5-bms-api j5-ui ${SERVICE_NAME}"
