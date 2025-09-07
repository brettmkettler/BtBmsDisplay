#!/bin/bash

# # Set up X11 display
# export DISPLAY=:0
# export XAUTHORITY=/home/seanfuchs/.Xauthority

# # Wait for X server to be ready
# sleep 2

# Clean up any existing Chrome processes
pkill -f chromium-browser || true

# # Create user data directory in home folder
# CHROME_DATA_DIR="/home/seanfuchs/.chrome-kiosk"
# mkdir -p "$CHROME_DATA_DIR"

# Launch Chrome in kiosk mode with proper parameters
chromium-browser --kiosk --no-sandbox --disable-web-security --enable-touch-events --force-device-scale-factor=2.1 --disable-translate http://localhost:3000