#!/bin/bash

# BtBmsDisplay Service Uninstall Script
# This script removes the BtBmsDisplay services and configurations

set -e  # Exit on any error

echo "🗑️ Uninstalling BtBmsDisplay Services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as the seanfuchs user."
   exit 1
fi

# Variables
SERVICE_DIR="/etc/systemd/system"
PROJECT_DIR="/home/seanfuchs/j5_console/BtBmsDisplay"

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1"
}

# Stop and disable services
echo "🛑 Stopping and disabling services..."

if service_exists "btbms-kiosk.service"; then
    echo "  • Stopping btbms-kiosk.service..."
    sudo systemctl stop btbms-kiosk.service || true
    echo "  • Disabling btbms-kiosk.service..."
    sudo systemctl disable btbms-kiosk.service || true
fi

if service_exists "btbms-display.service"; then
    echo "  • Stopping btbms-display.service..."
    sudo systemctl stop btbms-display.service || true
    echo "  • Disabling btbms-display.service..."
    sudo systemctl disable btbms-display.service || true
fi

# Remove service files
echo "🗂️ Removing service files..."
if [ -f "$SERVICE_DIR/btbms-display.service" ]; then
    sudo rm "$SERVICE_DIR/btbms-display.service"
    echo "  • Removed btbms-display.service"
fi

if [ -f "$SERVICE_DIR/btbms-kiosk.service" ]; then
    sudo rm "$SERVICE_DIR/btbms-kiosk.service"
    echo "  • Removed btbms-kiosk.service"
fi

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Remove auto-login configuration
echo "🔐 Removing auto-login configuration..."
if [ -f "/etc/lightdm/lightdm.conf.d/01-autologin.conf" ]; then
    sudo rm "/etc/lightdm/lightdm.conf.d/01-autologin.conf"
    echo "  • Removed auto-login configuration"
fi

# Remove X11 configuration files
echo "🖥️ Removing X11 configuration..."
if [ -f "/home/seanfuchs/.xsession" ]; then
    rm "/home/seanfuchs/.xsession"
    echo "  • Removed .xsession"
fi

if [ -d "/home/seanfuchs/.config/openbox" ]; then
    rm -rf "/home/seanfuchs/.config/openbox"
    echo "  • Removed openbox configuration"
fi

# Ask user about project files
echo ""
echo "📁 Project files are located at: $PROJECT_DIR"
read -p "Do you want to remove the project files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$PROJECT_DIR" ]; then
        echo "🗑️ Removing project files..."
        rm -rf "$PROJECT_DIR"
        echo "  • Removed $PROJECT_DIR"
    fi
else
    echo "  • Project files kept at $PROJECT_DIR"
fi

# Ask user about system packages
echo ""
read -p "Do you want to remove installed system packages? (chromium, openbox, etc.) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Removing system packages..."
    sudo apt remove -y chromium-browser openbox lightdm unclutter || true
    echo "  • Removed system packages"
    echo "  • Note: Node.js and npm were left installed as they may be used by other applications"
else
    echo "  • System packages kept"
fi

# Kill any remaining processes
echo "🔄 Cleaning up any remaining processes..."
pkill -f "chromium.*localhost:3000" || true
pkill -f "npm.*start" || true
pkill -f "node.*dist/index.js" || true

echo ""
echo "✅ BtBmsDisplay services uninstalled successfully!"
echo ""
echo "📋 What was removed:"
echo "  • btbms-display.service (systemd service)"
echo "  • btbms-kiosk.service (systemd service)"
echo "  • Auto-login configuration"
echo "  • X11 kiosk configuration"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  • Project files"
fi
echo ""
echo "🔄 Reboot recommended to ensure all changes take effect:"
echo "  sudo reboot"
