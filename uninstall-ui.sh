#!/bin/bash

# Uninstall UI service script
# This script removes the systemd service and cleans up

set -e

SERVICE_NAME="j5-ui"

echo "=== Uninstalling J5 Console UI Service ==="

# Stop the service if running
echo "Stopping ${SERVICE_NAME} service..."
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || echo "Service was not running"

# Disable the service
echo "Disabling ${SERVICE_NAME} service..."
sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || echo "Service was not enabled"

# Remove service file
echo "Removing service file..."
sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Reset failed state if any
sudo systemctl reset-failed ${SERVICE_NAME} 2>/dev/null || true

echo ""
echo "✓ Service '${SERVICE_NAME}' stopped and disabled"
echo "✓ Service file removed"
echo "✓ Systemd daemon reloaded"
echo ""
echo "Optional cleanup (run manually if desired):"
echo "  Remove node_modules:  rm -rf node_modules"
echo "  Remove build files:   rm -rf dist"
echo "  Remove lock file:     rm -f package-lock.json"
echo ""
echo "UI service has been completely uninstalled."
