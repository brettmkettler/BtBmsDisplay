#!/bin/bash

# J5 Console Kiosk Mode Startup Script
# Starts Chromium in kiosk mode with touch support and 2.0 zoom

# Wait for network to be ready
sleep 5

# Disable screen blanking and power management
xset -dpms
xset s off
xset s noblank

# Hide mouse cursor
unclutter -idle 1 &

# Start Chromium in kiosk mode with touch and zoom settings
chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-restore-session-state \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --touch-events=enabled \
  --force-device-scale-factor=2.0 \
  --enable-features=OverlayScrollbar \
  --start-fullscreen \
  --window-position=0,0 \
  --window-size=1920,1080 \
  http://localhost:3000
