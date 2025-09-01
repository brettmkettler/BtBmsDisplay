# BMS Bluetooth Integration Setup - Raspberry Pi 5

This guide covers setting up real Bluetooth BLE connectivity to your Overkill Solar BMS units on Raspberry Pi 5.

## Hardware Requirements

- **Raspberry Pi 5** with built-in Bluetooth
- **Overkill Solar BMS Units:**
  - Left Track BMS: `A4:C1:38:7C:2D:F0`
  - Right Track BMS: `E0:9F:2A:E4:94:1D`
- **Supported BMS Models:**
  - JBD-SP04S020 (120A 4s 12V)
  - JBD-SP10S009 (100A 8s 24V)  
  - JBD-SP25S003 (100A 16s 48V)

## Prerequisites

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Bluetooth dependencies
sudo apt install -y bluetooth bluez libbluetooth-dev libudev-dev

# Install Node.js build tools
sudo apt install -y build-essential python3-dev

# Ensure Bluetooth service is running
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Bluetooth Permissions

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Create udev rule for noble (if needed)
echo 'KERNEL=="hci0", GROUP="bluetooth", MODE="0664"' | sudo tee /etc/udev/rules.d/99-bluetooth.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 3. Node.js Setup

```bash
# Install dependencies
npm install

# The following packages are automatically installed:
# - @noble/noble: Modern BLE library for Node.js
# - buffer: Buffer polyfill for Node.js
```

## Configuration

### 1. BMS MAC Addresses

The system is pre-configured with your BMS MAC addresses:
- **Left Track BMS:** `A4:C1:38:7C:2D:F0`
- **Right Track BMS:** `E0:9F:2A:E4:94:1D`

To update these addresses, modify `/server/bms-integration.ts`:

```typescript
export const bmsIntegration = new BMSIntegration({
  leftTrackMac: 'A4:C1:38:7C:2D:F0',   // Your left track MAC
  rightTrackMac: 'E0:9F:2A:E4:94:1D',  // Your right track MAC
  pollInterval: 2000,                   // Data polling interval (ms)
  batteryCount: 4,                      // Batteries per track
  connectionTimeout: 15000,             // Connection timeout (ms)
  scanTimeout: 30000,                   // BLE scan timeout (ms)
  maxReconnectAttempts: 5              // Max reconnection attempts
});
```

### 2. Bluetooth Service Configuration

Create a systemd service for reliable Bluetooth startup:

```bash
# Create service file
sudo tee /etc/systemd/system/btbms-bluetooth.service << 'EOF'
[Unit]
Description=Bluetooth BMS Service
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 5 && hciconfig hci0 up'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl enable btbms-bluetooth.service
```

## Running the Application

### 1. Development Mode

```bash
# Start in development mode with BLE enabled
npm run dev
```

### 2. Production Mode

```bash
# Build and start in production
npm run build
npm start
```

### 3. Service Mode (Recommended)

Use the existing systemd services:

```bash
# Install services
sudo ./install-btbms-services.sh

# Check service status
sudo systemctl status btbms-display.service
sudo systemctl status btbms-kiosk.service

# View logs
sudo journalctl -u btbms-display.service -f
```

## Testing and Verification

### 1. Check Bluetooth Status

```bash
# Verify Bluetooth is working
sudo systemctl status bluetooth
hciconfig -a

# Scan for BLE devices (should see your BMS units)
sudo hcitool lescan
```

### 2. Application Endpoints

Access these endpoints to verify functionality:

- **Battery Data:** `GET /api/batteries`
- **BMS Status:** `GET /api/bms/status`
- **System Info:** `GET /api/system`

### 3. WebSocket Connection

The application provides real-time updates via WebSocket at `/ws`. Connection status and battery data are automatically broadcast every 2 seconds.

## Troubleshooting

### 1. Bluetooth Issues

```bash
# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check for interference
sudo hcitool dev
sudo rfkill list
```

### 2. Permission Issues

```bash
# Verify user permissions
groups $USER

# Fix permissions if needed
sudo chmod 666 /dev/ttyAMA0
sudo usermod -a -G dialout,bluetooth $USER
```

### 3. Connection Problems

```bash
# Check application logs
sudo journalctl -u btbms-display.service -f

# Monitor BLE scanning
sudo btmon

# Test BMS connectivity manually
sudo gatttool -b A4:C1:38:7C:2D:F0 -I
```

### 4. Performance Optimization

For optimal performance on Raspberry Pi 5:

```bash
# Increase Bluetooth buffer sizes
echo 'net.core.rmem_default = 262144' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

## API Reference

### BMS Status Response

```json
{
  "connected": true,
  "tracks": {
    "left": true,
    "right": false
  },
  "devices": {
    "a4:c1:38:7c:2d:f0": {
      "track": "left",
      "connected": true,
      "reconnectAttempts": 0,
      "lastData": "2025-08-31T19:50:00.000Z"
    }
  },
  "config": {
    "leftTrackMac": "A4:C1:38:7C:2D:F0",
    "rightTrackMac": "E0:9F:2A:E4:94:1D",
    "pollInterval": 2000,
    "batteryCount": 4
  }
}
```

### Battery Data Response

```json
[
  {
    "batteryNumber": 1,
    "voltage": 3.25,
    "amperage": 12.5,
    "chargeLevel": 75,
    "temperature": 25,
    "status": "normal",
    "track": "left",
    "trackPosition": 1
  }
]
```

## Security Considerations

1. **Network Security:** Ensure the Pi is on a secure network
2. **Bluetooth Security:** BMS units use basic BLE security
3. **API Access:** Consider adding authentication for production use
4. **Firewall:** Configure iptables if needed:

```bash
# Allow local access only
sudo iptables -A INPUT -p tcp --dport 3000 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 3000 -j DROP
```

## Support

For issues or questions:
1. Check the application logs: `sudo journalctl -u btbms-display.service -f`
2. Verify BMS connectivity with the `/api/bms/status` endpoint
3. Ensure Bluetooth permissions are correct
4. Verify BMS units are powered and within range (typically 10-30 feet)
