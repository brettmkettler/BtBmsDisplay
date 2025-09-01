#!/bin/bash

# BtBmsDisplay Service Installation Script
# This script installs and configures the BtBmsDisplay web application

set -e  # Exit on any error

echo "🚀 Installing BtBmsDisplay Services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$HOME/BtBmsDisplay"
SERVICE_DIR="/etc/systemd/system"

echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Project directory: $PROJECT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update system packages
echo "📦 Updating system packages..."
sudo apt update

# Install required system packages
echo "📦 Installing required packages..."
sudo apt install -y \
    nodejs \
    npm \
    curl

# Install Bluetooth dependencies for BMS integration
echo "🔵 Installing Bluetooth BMS dependencies..."
sudo apt install -y \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libudev-dev \
    build-essential \
    python3-dev

# Configure Bluetooth service
echo "🔵 Configuring Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add user to bluetooth group
echo "👤 Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Create udev rule for BLE access
echo "⚙️ Creating udev rule for BLE access..."
echo 'KERNEL=="hci0", GROUP="bluetooth", MODE="0664"' | sudo tee /etc/udev/rules.d/99-bluetooth.rules

# Add additional udev rules for noble BLE access
echo "⚙️ Creating additional BLE permission rules..."
sudo tee /etc/udev/rules.d/99-noble.rules << 'EOF'
# Allow users in bluetooth group to access BLE without root
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0002", MODE="0664", GROUP="bluetooth"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d6b", ATTRS{idProduct}=="0003", MODE="0664", GROUP="bluetooth"
KERNEL=="hci[0-9]*", GROUP="bluetooth", MODE="0664"
ACTION=="add", KERNEL=="hci[0-9]*", RUN+="/bin/hciconfig %k up"
EOF

# Set capabilities for Node.js to access Bluetooth without root
echo "🔐 Setting Node.js capabilities for Bluetooth access..."
NODE_PATH=$(which node)
sudo setcap 'cap_net_raw,cap_net_admin+eip' $NODE_PATH

# Reload udev rules
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# Install Node.js 18+ if needed
if ! command_exists node; then
    echo "📦 Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Verify Node.js version
NODE_VERSION=$(node --version)
echo "✅ Node.js version: $NODE_VERSION"

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 Creating project directory..."
    mkdir -p "$PROJECT_DIR"
fi

# Copy project files if not already there
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Copying project files to $PROJECT_DIR..."
    cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
    chown -R $USER:$USER "$PROJECT_DIR"
else
    echo "📋 Already in target directory, ensuring proper ownership..."
    chown -R $USER:$USER "$PROJECT_DIR"
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Build the project
echo "🔨 Building the project..."
npm run build

# Create Bluetooth BMS service
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

# Update service file with current user
echo "⚙️ Updating service file with current user..."
sed -i "s/User=seanfuchs/User=$USER/g" "$PROJECT_DIR/btbms-display.service"
sed -i "s/Group=seanfuchs/Group=$USER/g" "$PROJECT_DIR/btbms-display.service"
sed -i "s|WorkingDirectory=/home/seanfuchs/BtBmsDisplay|WorkingDirectory=$PROJECT_DIR|g" "$PROJECT_DIR/btbms-display.service"

# Copy service files to systemd
echo "⚙️ Installing systemd service files..."
sudo cp "$PROJECT_DIR/btbms-display.service" "$SERVICE_DIR/"

# Set proper permissions
sudo chmod 644 "$SERVICE_DIR/btbms-display.service"
sudo chmod 644 "$SERVICE_DIR/btbms-bluetooth.service"

# Apply performance optimizations for Bluetooth (only if not already present)
echo "⚡ Applying Bluetooth performance optimizations..."
if ! grep -q "net.core.rmem_default = 262144" /etc/sysctl.conf; then
    echo 'net.core.rmem_default = 262144' | sudo tee -a /etc/sysctl.conf
fi
if ! grep -q "net.core.rmem_max = 16777216" /etc/sysctl.conf; then
    echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
fi
sudo sysctl -p

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable btbms-bluetooth.service
sudo systemctl enable btbms-display.service

# Start services
echo "🚀 Starting services..."
sudo systemctl start btbms-bluetooth.service
sudo systemctl start btbms-display.service

# Wait for web service to be ready
echo "⏳ Waiting for web service to start..."
sleep 10

# Check if web service is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ BtBmsDisplay web service is running on port 3000"
else
    echo "⚠️ Web service may not be ready yet. Check with: sudo systemctl status btbms-display.service"
fi

# Check Bluetooth status
echo "🔍 Checking Bluetooth status..."
if systemctl is-active --quiet bluetooth; then
    echo "✅ Bluetooth service is running"
    if hciconfig hci0 > /dev/null 2>&1; then
        echo "✅ Bluetooth adapter (hci0) is available"
    else
        echo "⚠️  Bluetooth adapter not found - may require reboot"
    fi
else
    echo "❌ Bluetooth service is not running"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Service Status:"
echo "  • BtBmsDisplay Web App: sudo systemctl status btbms-display.service"
echo "  • Bluetooth BMS Service: sudo systemctl status btbms-bluetooth.service"
echo ""
echo "🌐 Access the application:"
echo "  • Open web browser to: http://localhost:3000"
echo "  • Or from another device: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "🔧 Manual Commands:"
echo "  • Start web app: sudo systemctl start btbms-display.service"
echo "  • View logs: sudo journalctl -u btbms-display.service -f"
echo "  • Test manually: npm start (from $PROJECT_DIR)"
echo "  • Check BMS status: curl http://localhost:3000/api/bms/status"
echo ""
echo "🔵 Bluetooth BMS Integration:"
echo "  • Real BMS data is enabled by default"
echo "  • BMS MAC addresses: A4:C1:38:7C:2D:F0 (left), E0:9F:2A:E4:94:1D (right)"
echo "  • Check Bluetooth: sudo systemctl status bluetooth"
echo "  • Scan for devices: sudo hcitool lescan"
echo ""
echo "🔄 Reboot recommended to ensure all services start properly:"
echo "  sudo reboot"
