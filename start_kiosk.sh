#!/bin/bash

#WORKING VERSION

# Set up X11 display and authorization
export DISPLAY=:0

# Configure X11 authorization properly
if [ -f "/home/seanfuchs/.Xauthority" ]; then
    export XAUTHORITY="/home/seanfuchs/.Xauthority"
fi

# Allow X11 connections for current user
xhost +local:$(whoami) 2>/dev/null || true

# Configure D-Bus session properly
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
fi

# Wait for X server to be ready
sleep 3

# Clean up any existing Chrome processes
pkill -f chromium-browser || true
sleep 1

# Create user data directory in home folder with proper permissions
CHROME_DATA_DIR="/home/seanfuchs/.chrome-kiosk"
mkdir -p "$CHROME_DATA_DIR"
chmod 755 "$CHROME_DATA_DIR"

# Launch Chrome in kiosk mode with fixed flags for Raspberry Pi
chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    --disable-features=TranslateUI,VizDisplayCompositor \
    --no-first-run \
    --disable-default-apps \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --force-device-scale-factor=2.1 \
    --user-data-dir="$CHROME_DATA_DIR" \
    --enable-touch-events \
    http://localhost:3000