#!/bin/bash

# J5 Console Kiosk Mode X11 Startup
# Auto-starts the display in kiosk mode with touch support

# Disable power management and screen blanking
xset -dpms
xset s off
xset s noblank

# Hide mouse cursor after 1 second of inactivity
unclutter -idle 1 &

# Wait for services to be ready
sleep 3

# Start the kiosk
exec /home/seanfuchs/Desktop/j5_console/BtBmsDisplay/kiosk-startup.sh
