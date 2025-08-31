#!/bin/bash

# BtBmsDisplay Service Installation Script
# This script installs and configures the BtBmsDisplay web application and kiosk mode

set -e  # Exit on any error

echo "🚀 Installing BtBmsDisplay Services..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as the seanfuchs user."
   exit 1
fi

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/seanfuchs/Desktop/j5_console/BtBmsDisplay"
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
    chromium-browser \
    curl \
    xorg \
    openbox \
    unclutter

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
    sudo mkdir -p "/home/seanfuchs/Desktop/j5_console"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R seanfuchs:seanfuchs "/home/seanfuchs/Desktop/j5_console"
fi

# Copy project files if not already there
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Copying project files to $PROJECT_DIR..."
    sudo cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
    sudo chown -R seanfuchs:seanfuchs "$PROJECT_DIR"
else
    echo "📋 Already in target directory, ensuring proper ownership..."
    sudo chown -R seanfuchs:seanfuchs "$PROJECT_DIR"
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Build the project
echo "🔨 Building the project..."
npm run build

# Copy service files to systemd
echo "⚙️ Installing systemd service files..."
sudo cp "$PROJECT_DIR/btbms-display.service" "$SERVICE_DIR/"

# Set proper permissions
sudo chmod 644 "$SERVICE_DIR/btbms-display.service"

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable btbms-display.service

# Configure auto-login for seanfuchs user
echo "🔐 Configuring auto-login..."
sudo loginctl enable-linger seanfuchs

# Configure X11 to start kiosk mode
echo "🖥️ Configuring X11 startup..."
cat > /home/seanfuchs/.xsession <<EOF
#!/bin/bash
# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide mouse cursor after 1 second of inactivity
unclutter -idle 1 &

# Start openbox window manager
exec openbox-session
EOF

chmod +x /home/seanfuchs/.xsession

# Create openbox autostart
mkdir -p /home/seanfuchs/.config/openbox
cat > /home/seanfuchs/.config/openbox/autostart <<EOF
# Start the kiosk service
chromium-browser --kiosk --app=http://localhost:3000 &
EOF

# Start services
echo "🚀 Starting services..."
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

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Service Status:"
echo "  • BtBmsDisplay Web App: sudo systemctl status btbms-display.service"
echo ""
echo "🔧 Manual Commands:"
echo "  • Start web app: sudo systemctl start btbms-display.service"
echo "  • View logs: sudo journalctl -u btbms-display.service -f"
echo "  • Test manually: npm start (from $PROJECT_DIR)"
echo ""
echo "🔄 Reboot recommended to ensure all services start properly:"
echo "  sudo reboot"
