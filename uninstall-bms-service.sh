#!/bin/bash

# Uninstall BMS API service script
# This script removes the systemd service for the Python BMS API

set -e

echo "=== Uninstalling BMS API Service ==="

SERVICE_NAME="j5-bms-api"

# Check if service exists
if [ ! -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "Service '${SERVICE_NAME}' is not installed."
    exit 0
fi

# Stop the service if it's running
echo "Stopping service..."
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true

# Disable the service
echo "Disabling service..."
sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || true

# Remove the service file
echo "Removing service file..."
sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Reset failed state if any
sudo systemctl reset-failed ${SERVICE_NAME} 2>/dev/null || true

echo ""
echo "✓ BMS API service '${SERVICE_NAME}' has been completely removed"
echo ""
echo "The service is no longer installed and will not start automatically."
echo ""
