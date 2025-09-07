#!/bin/bash

# Fix Kiosk Permissions Script
# Ensures start_kiosk.sh has execute permissions even after reboot

echo "=== Fixing Kiosk Permissions Issue ==="

# Set execute permissions on the script
chmod +x start_kiosk.sh
echo "✓ Set execute permissions on start_kiosk.sh"

# Update the systemd service to ensure permissions are set
sudo tee /etc/systemd/system/j5-kiosk.service > /dev/null << EOF
[Unit]
Description=J5 Kiosk Service
After=graphical-session.target j5-ui.service
Wants=graphical-session.target
Requires=j5-ui.service

[Service]
Type=simple
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$(pwd)
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$(whoami)/.Xauthority
# Set execute permissions before running
ExecStartPre=/bin/chmod +x $(pwd)/start_kiosk.sh
ExecStart=$(pwd)/start_kiosk.sh
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

# Reload systemd and restart service
sudo systemctl daemon-reload
sudo systemctl enable j5-kiosk
echo "✓ Updated systemd service to set permissions automatically"

echo "✓ Kiosk permissions issue fixed"
echo "The service will now set execute permissions automatically on startup"
