#!/bin/bash

# Simple kiosk service installer - runs start_kiosk.sh on boot

echo "Installing simple kiosk service..."

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make start_kiosk.sh executable
chmod +x "$SCRIPT_DIR/start_kiosk.sh"

# Create systemd service file
sudo tee /etc/systemd/system/simple-kiosk.service > /dev/null << EOF
[Unit]
Description=Simple Kiosk Service
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=pi
Group=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=$SCRIPT_DIR/start_kiosk.sh
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable simple-kiosk.service

echo "Simple kiosk service installed successfully!"
echo "The service will start automatically on boot."
echo ""
echo "Manual control commands:"
echo "  Start:   sudo systemctl start simple-kiosk"
echo "  Stop:    sudo systemctl stop simple-kiosk"
echo "  Status:  sudo systemctl status simple-kiosk"
echo "  Logs:    sudo journalctl -u simple-kiosk -f"
