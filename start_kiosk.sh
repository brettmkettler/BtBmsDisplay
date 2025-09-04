#!/bin/bash

# Create a temporary user data directory for Chrome
USER_DATA_DIR="/tmp/chrome-kiosk-$(date +%s)"
mkdir -p "$USER_DATA_DIR"

# Start Chrome in kiosk mode with proper flags
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
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-background-networking \
  --autoplay-policy=no-user-gesture-required \
  --no-first-run \
  --fast \
  --fast-start \
  --disable-default-apps \
  --disable-popup-blocking \
  --disable-prompt-on-repost \
  --disable-hang-monitor \
  --disable-logging \
  --silent-debugger-extension-api \
  --disable-extensions \
  --disable-plugins \
  --disable-translate \
  --disable-background-mode \
  --disable-add-to-shelf \
  --disable-dev-shm-usage \
  http://localhost:3000

# Clean up user data directory on exit
trap "rm -rf '$USER_DATA_DIR'" EXIT