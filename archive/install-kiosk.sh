#!/bin/bash

# J5 Console Kiosk Mode Installation Script
# Sets up automatic kiosk mode with touch support and 2.0 zoom

echo "🚀 Installing J5 Console Kiosk Mode..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash install-kiosk.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$(whoami)}
USER_HOME="/home/$ACTUAL_USER"

echo "📋 Configuration:"
echo "  User: $ACTUAL_USER"
echo "  Home: $USER_HOME"
echo "  Project: $USER_HOME/Desktop/j5_console"
echo ""

# Install required packages
echo "📦 Installing system packages..."
apt update
apt install -y chromium-browser unclutter xdotool xinit xserver-xorg x11-xserver-utils
apt install -y xserver-xorg-input-evdev  # Touch screen support

# Make scripts executable
echo "🔧 Setting up scripts..."
chmod +x "$USER_HOME/Desktop/j5_console/BtBmsDisplay/kiosk-startup.sh"
chmod +x "$USER_HOME/Desktop/j5_console/BtBmsDisplay/.xinitrc"

# Set proper ownership
chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/Desktop/j5_console/BtBmsDisplay/kiosk-startup.sh"
chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/Desktop/j5_console/BtBmsDisplay/.xinitrc"

# Copy xinitrc to user home
cp "$USER_HOME/Desktop/j5_console/BtBmsDisplay/.xinitrc" "$USER_HOME/.xinitrc"
chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.xinitrc"
chmod +x "$USER_HOME/.xinitrc"

# Install systemd services
echo "⚙️ Installing systemd services..."

# Copy service files
cp "$USER_HOME/Desktop/j5_console/BtBmsDisplay/j5-display-kiosk.service" /etc/systemd/system/
cp "$USER_HOME/Desktop/j5_console/BtBmsDisplay/kiosk-x11.service" /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable j5-display-kiosk.service
systemctl enable kiosk-x11.service

# Configure auto-login
echo "👤 Configuring auto-login..."
systemctl set-default multi-user.target

# Add auto-start X11 to bashrc if not already present
if ! grep -q "startx" "$USER_HOME/.bashrc"; then
    echo "" >> "$USER_HOME/.bashrc"
    echo "# Auto-start X11 for J5 Console Kiosk" >> "$USER_HOME/.bashrc"
    echo "if [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then" >> "$USER_HOME/.bashrc"
    echo "    startx" >> "$USER_HOME/.bashrc"
    echo "fi" >> "$USER_HOME/.bashrc"
    chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.bashrc"
fi

echo ""
echo "✅ J5 Console Kiosk Mode installed successfully!"
echo ""
echo "📋 What was configured:"
echo "  ✅ Chromium browser with touch support"
echo "  ✅ 2.0 zoom level for better touch interaction"
echo "  ✅ Auto-start X11 and kiosk mode"
echo "  ✅ Screen blanking disabled"
echo "  ✅ Mouse cursor auto-hide"
echo "  ✅ Systemd services for display and kiosk"
echo ""
echo "🔧 Kiosk Features:"
echo "  • Touch events enabled"
echo "  • 2.0x zoom for larger UI elements"
echo "  • Full-screen mode"
echo "  • Auto-start on boot"
echo "  • Screen power management disabled"
echo ""
echo "🚀 To start services now:"
echo "  sudo systemctl start j5-display-kiosk"
echo "  sudo systemctl start kiosk-x11"
echo ""
echo "🔄 Or reboot to start automatically:"
echo "  sudo reboot"
echo ""
echo "📊 Check status:"
echo "  sudo systemctl status j5-display-kiosk"
echo "  sudo systemctl status kiosk-x11"
