#!/bin/bash

# Bluetooth BMS Setup Script for Raspberry Pi 5
# This script installs and configures Bluetooth dependencies for BMS integration

set -e  # Exit on any error

echo "🔵 Setting up Bluetooth BMS Integration for Raspberry Pi 5..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as the seanfuchs user."
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install Bluetooth dependencies
echo "🔵 Installing Bluetooth dependencies..."
sudo apt install -y \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libudev-dev \
    build-essential \
    python3-dev

# Ensure Bluetooth service is running
echo "🔵 Configuring Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add user to bluetooth group
echo "👤 Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Create udev rule for noble
echo "⚙️ Creating udev rule for BLE access..."
echo 'KERNEL=="hci0", GROUP="bluetooth", MODE="0664"' | sudo tee /etc/udev/rules.d/99-bluetooth.rules

# Reload udev rules
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Create systemd service for reliable Bluetooth startup
echo "⚙️ Creating Bluetooth BMS service..."
sudo tee /etc/systemd/system/btbms-bluetooth.service << 'EOF'
[Unit]
Description=Bluetooth BMS Service
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 5 && hciconfig hci0 up'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the Bluetooth BMS service
echo "✅ Enabling Bluetooth BMS service..."
sudo systemctl enable btbms-bluetooth.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Performance optimization for Raspberry Pi 5
echo "⚡ Applying performance optimizations..."
echo 'net.core.rmem_default = 262144' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf

# Apply sysctl changes
sudo sysctl -p

# Check Bluetooth status
echo "🔍 Checking Bluetooth status..."
if systemctl is-active --quiet bluetooth; then
    echo "✅ Bluetooth service is running"
    
    # Check if hci0 is available
    if hciconfig hci0 > /dev/null 2>&1; then
        echo "✅ Bluetooth adapter (hci0) is available"
        
        # Show Bluetooth adapter info
        echo "📋 Bluetooth adapter information:"
        hciconfig hci0 | grep -E "(BD Address|UP RUNNING)"
    else
        echo "⚠️  Bluetooth adapter not found - may require reboot"
    fi
else
    echo "❌ Bluetooth service is not running"
fi

# Check user groups
echo "👤 User groups:"
groups $USER | grep -q bluetooth && echo "✅ User is in bluetooth group" || echo "⚠️  User not in bluetooth group (requires logout/login)"

echo ""
echo "🎉 Bluetooth BMS setup complete!"
echo ""
echo "📋 What was configured:"
echo "  • Bluetooth and BlueZ packages installed"
echo "  • User added to bluetooth group"
echo "  • udev rules created for BLE access"
echo "  • btbms-bluetooth.service created and enabled"
echo "  • Network buffer sizes optimized"
echo ""
echo "🔧 Next steps:"
echo "  1. Log out and log back in (or reboot) for group changes to take effect"
echo "  2. Install Node.js dependencies: npm install"
echo "  3. Start the BMS application: npm run dev"
echo ""
echo "🔍 Testing commands:"
echo "  • Check Bluetooth: sudo systemctl status bluetooth"
echo "  • Scan for devices: sudo hcitool lescan"
echo "  • Check BMS status: curl http://localhost:3000/api/bms/status"
echo ""
echo "🔄 Reboot recommended to ensure all changes take effect:"
echo "  sudo reboot"
