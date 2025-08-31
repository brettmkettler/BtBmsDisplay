#!/bin/bash

# Bluetooth BMS Cleanup Script for Raspberry Pi 5
# This script removes Bluetooth BMS configurations and dependencies

set -e  # Exit on any error

echo "🔵 Cleaning up Bluetooth BMS Integration..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as the seanfuchs user."
   exit 1
fi

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1"
}

# Stop and disable Bluetooth BMS service
echo "🛑 Stopping and disabling Bluetooth BMS service..."
if service_exists "btbms-bluetooth.service"; then
    echo "  • Stopping btbms-bluetooth.service..."
    sudo systemctl stop btbms-bluetooth.service || true
    echo "  • Disabling btbms-bluetooth.service..."
    sudo systemctl disable btbms-bluetooth.service || true
fi

# Remove Bluetooth BMS service file
echo "🗂️ Removing Bluetooth BMS service file..."
if [ -f "/etc/systemd/system/btbms-bluetooth.service" ]; then
    sudo rm "/etc/systemd/system/btbms-bluetooth.service"
    echo "  • Removed btbms-bluetooth.service"
fi

# Remove udev rule
echo "⚙️ Removing udev rule..."
if [ -f "/etc/udev/rules.d/99-bluetooth.rules" ]; then
    sudo rm "/etc/udev/rules.d/99-bluetooth.rules"
    echo "  • Removed 99-bluetooth.rules"
fi

# Reload udev rules
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Remove user from bluetooth group
echo "👤 Removing user from bluetooth group..."
sudo gpasswd -d $USER bluetooth || echo "  • User was not in bluetooth group"

# Remove performance optimizations from sysctl.conf
echo "⚡ Removing performance optimizations..."
sudo sed -i '/net.core.rmem_default = 262144/d' /etc/sysctl.conf || true
sudo sed -i '/net.core.rmem_max = 16777216/d' /etc/sysctl.conf || true

# Apply sysctl changes
sudo sysctl -p

# Ask user about Bluetooth packages
echo ""
read -p "Do you want to remove Bluetooth packages? (bluetooth, bluez, etc.) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Removing Bluetooth packages..."
    sudo apt remove -y \
        libbluetooth-dev \
        libudev-dev || true
    echo "  • Removed Bluetooth development packages"
    echo "  • Note: bluetooth and bluez were left installed as they may be used by other applications"
else
    echo "  • Bluetooth packages kept"
fi

# Ask user about build tools
echo ""
read -p "Do you want to remove build tools? (build-essential, python3-dev) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Removing build tools..."
    sudo apt remove -y build-essential python3-dev || true
    echo "  • Removed build tools"
else
    echo "  • Build tools kept"
fi

# Kill any BLE-related processes
echo "🔄 Cleaning up any BLE processes..."
pkill -f "noble" || true
pkill -f "hcitool" || true

echo ""
echo "✅ Bluetooth BMS cleanup complete!"
echo ""
echo "📋 What was removed:"
echo "  • btbms-bluetooth.service (systemd service)"
echo "  • 99-bluetooth.rules (udev rule)"
echo "  • User removed from bluetooth group"
echo "  • Performance optimizations removed"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  • Bluetooth development packages"
fi
echo ""
echo "📋 What was kept:"
echo "  • Core Bluetooth service (bluetooth.service)"
echo "  • BlueZ stack (may be used by other applications)"
echo ""
echo "🔧 Manual cleanup (if needed):"
echo "  • Reset Bluetooth: sudo systemctl restart bluetooth"
echo "  • Check status: sudo systemctl status bluetooth"
echo ""
echo "🔄 Logout/login recommended for group changes to take effect"
