#!/bin/bash

# BtBmsDisplay Service Uninstall Script
# This script removes the BtBmsDisplay services and configurations

set -e  # Exit on any error

echo "🗑️ Uninstalling BtBmsDisplay Services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Variables
SERVICE_DIR="/etc/systemd/system"
PROJECT_DIR="$HOME/BtBmsDisplay"

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1"
}

# Stop and disable services
echo "🛑 Stopping and disabling services..."

if service_exists "btbms-display.service"; then
    echo "  • Stopping btbms-display.service..."
    sudo systemctl stop btbms-display.service || true
    echo "  • Disabling btbms-display.service..."
    sudo systemctl disable btbms-display.service || true
fi

if service_exists "btbms-bluetooth.service"; then
    echo "  • Stopping btbms-bluetooth.service..."
    sudo systemctl stop btbms-bluetooth.service || true
    echo "  • Disabling btbms-bluetooth.service..."
    sudo systemctl disable btbms-bluetooth.service || true
fi

# Remove service files
echo "🗂️ Removing service files..."
if [ -f "$SERVICE_DIR/btbms-display.service" ]; then
    sudo rm "$SERVICE_DIR/btbms-display.service"
    echo "  • Removed btbms-display.service"
fi

if [ -f "$SERVICE_DIR/btbms-bluetooth.service" ]; then
    sudo rm "$SERVICE_DIR/btbms-bluetooth.service"
    echo "  • Removed btbms-bluetooth.service"
fi

# Remove Bluetooth BMS configurations
echo "🔵 Removing Bluetooth BMS configurations..."

# Remove udev rule
if [ -f "/etc/udev/rules.d/99-bluetooth.rules" ]; then
    sudo rm "/etc/udev/rules.d/99-bluetooth.rules"
    echo "  • Removed 99-bluetooth.rules"
fi

# Reload udev rules
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Remove user from bluetooth group
echo "👤 Removing user from bluetooth group..."
sudo gpasswd -d $USER bluetooth || echo "  • User was not in bluetooth group"

# Remove performance optimizations from sysctl.conf
echo "⚡ Removing Bluetooth performance optimizations..."
sudo sed -i '/net.core.rmem_default = 262144/d' /etc/sysctl.conf || true
sudo sed -i '/net.core.rmem_max = 16777216/d' /etc/sysctl.conf || true
sudo sysctl -p

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

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

# Ask user about Bluetooth packages
echo ""
read -p "Do you want to remove Bluetooth BMS packages? (libbluetooth-dev, build tools, etc.) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔵 Removing Bluetooth BMS packages..."
    sudo apt remove -y \
        libbluetooth-dev \
        libudev-dev \
        build-essential \
        python3-dev || true
    echo "  • Removed Bluetooth development packages"
    echo "  • Note: bluetooth and bluez were left installed as they may be used by other applications"
else
    echo "  • Bluetooth BMS packages kept"
fi

# Kill any remaining processes
echo "🔄 Cleaning up any remaining processes..."
pkill -f "npm.*start" || true
pkill -f "node.*dist/index.js" || true
pkill -f "noble" || true
pkill -f "hcitool" || true

echo ""
echo "✅ BtBmsDisplay services uninstalled successfully!"
echo ""
echo "📋 What was removed:"
echo "  • btbms-display.service (systemd service)"
echo "  • btbms-bluetooth.service (systemd service)"
echo "  • 99-bluetooth.rules (udev rule)"
echo "  • User removed from bluetooth group"
echo "  • Bluetooth performance optimizations"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  • Project files"
    echo "  • Bluetooth BMS packages"
fi
echo ""
echo "📋 What was kept:"
echo "  • Core Bluetooth service (bluetooth.service)"
echo "  • BlueZ stack (may be used by other applications)"
echo "  • Node.js and npm"
echo ""
echo "🔄 Reboot recommended to ensure all changes take effect:"
echo "  sudo reboot"
