#!/bin/bash

# Wait for X server to be available
sleep 5

# Set up display environment
export DISPLAY=:0
export XAUTHORITY=/home/$(whoami)/.Xauthority

# Create user data directory for Chromium
USER_DATA_DIR="/tmp/chromium-kiosk-$(whoami)"
mkdir -p "$USER_DATA_DIR"

# Launch Chromium in kiosk mode with proper configuration
chromium-browser \
  --kiosk \
  --no-sandbox \
  --disable-web-security \
  --user-data-dir="$USER_DATA_DIR" \
  --disable-features=VizDisplayCompositor \
  --enable-touch-events \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --autoplay-policy=no-user-gesture-required \
  http://localhost:3000