#!/bin/bash

# J5 Console Kiosk Mode Uninstall Script
# Removes kiosk mode configuration and services

echo "🗑️ Uninstalling J5 Console Kiosk Mode..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash uninstall-kiosk.sh"
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

# Stop and disable services
echo "🛑 Stopping kiosk services..."
systemctl stop kiosk-x11.service 2>/dev/null || true
systemctl stop j5-display-kiosk.service 2>/dev/null || true

echo "❌ Disabling kiosk services..."
systemctl disable kiosk-x11.service 2>/dev/null || true
systemctl disable j5-display-kiosk.service 2>/dev/null || true

# Remove service files
echo "🗂️ Removing service files..."
rm -f /etc/systemd/system/kiosk-x11.service
rm -f /etc/systemd/system/j5-display-kiosk.service

# Reload systemd
systemctl daemon-reload

# Remove xinitrc from user home
echo "🔧 Removing X11 configuration..."
if [ -f "$USER_HOME/.xinitrc" ]; then
    rm -f "$USER_HOME/.xinitrc"
    echo "  ❌ Removed $USER_HOME/.xinitrc"
fi

# Remove auto-start X11 from bashrc
echo "👤 Removing auto-login configuration..."
if [ -f "$USER_HOME/.bashrc" ]; then
    # Create a backup
    cp "$USER_HOME/.bashrc" "$USER_HOME/.bashrc.backup"
    
    # Remove the auto-start X11 section
    sed -i '/# Auto-start X11 for J5 Console Kiosk/,+4d' "$USER_HOME/.bashrc"
    
    # Ensure proper ownership
    chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.bashrc"
    chown $ACTUAL_USER:$ACTUAL_USER "$USER_HOME/.bashrc.backup"
    
    echo "  ❌ Removed auto-start X11 from .bashrc"
    echo "  ✅ Backup saved as .bashrc.backup"
fi

# Reset to default target (optional - user can choose)
echo "🎯 Resetting system target..."
systemctl set-default graphical.target

# Kill any running Chromium processes
echo "🌐 Stopping Chromium processes..."
pkill -f chromium-browser 2>/dev/null || true
pkill -f "chromium.*kiosk" 2>/dev/null || true

# Kill X11 processes if running
echo "🖥️ Stopping X11 processes..."
pkill -f "startx" 2>/dev/null || true

echo ""
echo "✅ J5 Console Kiosk Mode uninstalled successfully!"
echo ""
echo "📋 What was removed:"
echo "  ❌ Kiosk mode services stopped and disabled"
echo "  ❌ Systemd service files deleted"
echo "  ❌ X11 auto-start configuration removed"
echo "  ❌ .xinitrc file removed"
echo "  ❌ Running Chromium/X11 processes stopped"
echo ""
echo "📁 Files that remain untouched:"
echo "  ✅ BtBmsDisplay application code"
echo "  ✅ kiosk-startup.sh script (in project folder)"
echo "  ✅ .xinitrc script (in project folder)"
echo "  ✅ Service files (in project folder)"
echo "  ✅ All your project data"
echo ""
echo "🔄 To run display manually:"
echo "  cd ~/Desktop/j5_console/BtBmsDisplay"
echo "  npm start"
echo "  # Then open browser to http://localhost:3000"
echo ""
echo "🚀 To reinstall kiosk mode:"
echo "  cd ~/Desktop/j5_console/BtBmsDisplay"
echo "  sudo bash install-kiosk.sh"
echo ""
echo "⚠️ Note: You may need to reboot to fully reset the display system."
