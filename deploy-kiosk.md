# J5 Console Display - Raspberry Pi Kiosk Deployment

## Prerequisites

### System Requirements
- Raspberry Pi 4 (recommended) or Pi 3B+
- Raspberry Pi OS Lite or Desktop
- Node.js 18+ and npm
- Chromium browser for kiosk mode

### Installation Steps

## 1. Install Node.js
```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

## 2. Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y chromium-browser unclutter xdotool

# For kiosk mode
sudo apt install -y xinit xserver-xorg x11-xserver-utils
```

## 3. Deploy Application
```bash
# Clone/copy the BtBmsDisplay folder to Pi
cd /home/pi
git clone <your-repo> j5_console
cd j5_console/BtBmsDisplay

# Install dependencies
npm install

# Build production version
npm run build

# Create systemd service for the app
sudo nano /etc/systemd/system/j5-display.service
```

## 4. Systemd Service Configuration
Create `/etc/systemd/system/j5-display.service`:

```ini
[Unit]
Description=J5 Console Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/j5_console/BtBmsDisplay
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

## 5. Kiosk Mode Setup

### Auto-start X11 and Chromium
Create `/home/pi/.xinitrc`:
```bash
#!/bin/bash
xset -dpms     # disable DPMS (Energy Star) features.
xset s off     # disable screen saver
xset s noblank # don't blank the video device
unclutter &    # hide mouse cursor
chromium-browser --noerrdialogs --disable-infobars --kiosk http://localhost:3000
```

### Auto-login and start X11
```bash
# Enable auto-login
sudo raspi-config
# Navigate to: 3 Boot Options -> B1 Desktop / CLI -> B2 Console Autologin

# Add to ~/.bashrc to auto-start X11
echo "if [ -z \"\$DISPLAY\" ] && [ \"\$(tty)\" = \"/dev/tty1\" ]; then startx; fi" >> ~/.bashrc
```

## 6. Configure Port Separation

Since j5_console.py runs on port 5000, modify BtBmsDisplay to use port 3000:

### Update package.json scripts:
```json
{
  "scripts": {
    "dev": "NODE_ENV=development PORT=3000 tsx server/index.ts",
    "start": "NODE_ENV=production PORT=3000 node dist/index.js"
  }
}
```

### Update server/index.ts:
```typescript
const port = parseInt(process.env.PORT || '3000', 10);
```

## 7. Enable Services
```bash
# Enable and start the display service
sudo systemctl enable j5-display.service
sudo systemctl start j5-display.service

# Check status
sudo systemctl status j5-display.service
```

## 8. Integration with j5_console.py

The display app can communicate with j5_console.py API on port 5000:

### Add API client to BtBmsDisplay:
```typescript
// In client/src/lib/j5-api.ts
const J5_API_BASE = 'http://localhost:5000';

export const j5Api = {
  getSystemStatus: () => fetch(`${J5_API_BASE}/api/system/status`),
  controlDoor: (door: string, action: string) => 
    fetch(`${J5_API_BASE}/api/door/${door}?action=${action}`, { method: 'POST' }),
  controlLED: (led: string, state: string) => 
    fetch(`${J5_API_BASE}/api/digital/${led}?state=${state}`, { method: 'POST' })
};
```

## 9. Screen Configuration

### For touch screen setup:
```bash
# Install touch screen drivers if needed
sudo apt install -y xserver-xorg-input-evdev

# Configure display rotation if needed
sudo nano /boot/config.txt
# Add: display_rotate=1  # for 90 degrees
```

## 10. Troubleshooting

### View logs:
```bash
# Display service logs
sudo journalctl -u j5-display.service -f

# System logs
sudo journalctl -f
```

### Manual testing:
```bash
# Test the app manually
cd /home/pi/j5_console/BtBmsDisplay
npm start

# Test in browser
chromium-browser --kiosk http://localhost:3000
```

## Network Configuration

### For remote access during development:
```bash
# Allow external connections (development only)
# Modify server/index.ts to bind to 0.0.0.0:3000
server.listen({
  port: 3000,
  host: "0.0.0.0",
  reusePort: true,
});
```

## Security Considerations

- The kiosk will auto-start and run full-screen
- No keyboard/mouse access in kiosk mode
- SSH access should be enabled for remote management
- Consider firewall rules for production deployment
