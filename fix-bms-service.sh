#!/bin/bash

# Fix BMS API service with correct permissions and paths

echo "=== Fixing BMS API Service ==="

# Stop and disable current service
SERVICE_NAME="j5-bms-api"
sudo systemctl stop ${SERVICE_NAME}.service 2>/dev/null || true
sudo systemctl disable ${SERVICE_NAME}.service 2>/dev/null || true

# Get current directory and user
INSTALL_DIR=$(pwd)
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)

echo "User: $CURRENT_USER"
echo "Installation directory: $INSTALL_DIR"
echo "User home: $USER_HOME"

# Check if dual_bms_service.py exists
if [ ! -f "dual_bms_service.py" ]; then
    echo "Error: dual_bms_service.py not found in current directory."
    exit 1
fi

# Find Python executable (prefer venv if it exists)
PYTHON_EXEC=""
if [ -f "$USER_HOME/Desktop/venv/bin/python" ]; then
    PYTHON_EXEC="$USER_HOME/Desktop/venv/bin/python"
    echo "Using virtual environment Python: $PYTHON_EXEC"
elif [ -f "$USER_HOME/Desktop/venv/bin/python3" ]; then
    PYTHON_EXEC="$USER_HOME/Desktop/venv/bin/python3"
    echo "Using virtual environment Python3: $PYTHON_EXEC"
else
    PYTHON_EXEC=$(which python3)
    echo "Using system Python3: $PYTHON_EXEC"
fi

# Create corrected systemd service file - RUN AS ROOT for Bluetooth access
echo "Creating corrected systemd service file (running as root for Bluetooth)..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=J5 Console BMS API Service
After=network.target bluetooth.target
Wants=network.target bluetooth.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=HOME=/root
ExecStart=$PYTHON_EXEC dual_bms_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo ""
echo "✓ BMS API service '${SERVICE_NAME}' fixed and enabled"
echo "✓ Service now runs as root for Bluetooth access"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "Starting service now..."
sudo systemctl start ${SERVICE_NAME}.service

echo ""
echo "Checking service status..."
sudo systemctl status ${SERVICE_NAME}.service --no-pager
