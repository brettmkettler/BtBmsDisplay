#!/bin/bash

echo "Fixing J5 UI systemd service configuration..."

# Force stop and disable the current service
sudo systemctl stop j5-ui.service
sudo systemctl disable j5-ui.service

# Remove the old service file
sudo rm -f /etc/systemd/system/j5-ui.service

# Make start_kiosk.sh executable
chmod +x ./start_kiosk.sh
echo "✓ Made start_kiosk.sh executable"

# Get the absolute path to npm
NPM_PATH=$(which npm)
if [ -z "$NPM_PATH" ]; then
    echo "Error: npm not found in PATH"
    exit 1
fi

echo "Using npm at: $NPM_PATH"

# Get the current working directory
WORK_DIR=$(pwd)
echo "Working directory: $WORK_DIR"

# Create the systemd service file with absolute paths
sudo tee /etc/systemd/system/j5-ui.service > /dev/null << EOF
[Unit]
Description=J5 Console UI Service
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=$WORK_DIR
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/bin/bash -c "cd $WORK_DIR && $NPM_PATH run start & sleep 5 && ./start_kiosk.sh"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created with correct npm start command"

# Reload systemd daemon
sudo systemctl daemon-reload
echo "✓ Systemd daemon reloaded"

# Enable the service
sudo systemctl enable j5-ui.service
echo "✓ Service enabled"

# Start the service
sudo systemctl start j5-ui.service
echo "✓ Service started"

echo ""
echo "Service status:"
sudo systemctl status j5-ui.service --no-pager

echo ""
echo "To check logs: sudo journalctl -u j5-ui.service -f"
echo "UI should be available at: http://localhost:3000"