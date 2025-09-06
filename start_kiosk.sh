#!/bin/bash

# Set up X11 display
export DISPLAY=:0
export XAUTHORITY=/home/seanfuchs/.Xauthority

# Wait for X server to be ready
sleep 2

# Launch Chrome in kiosk mode with proper parameters
chromium-browser --kiosk --no-sandbox --disable-web-security --disable-features=VizDisplayCompositor --user-data-dir=/tmp/chrome-kiosk --enable-touch-events --force-device-scale-factor=2.1 --disable-dev-shm-usage --disable-gpu --no-first-run --disable-default-apps --disable-infobars --disable-session-crashed-bubble --disable-translate http://localhost:3000