#!/bin/bash

echo "Comprehensive Bluetooth Reset"
echo "============================="

# Kill any existing Bluetooth processes
echo "Stopping Bluetooth processes..."
sudo pkill -f bluetoothd
sudo pkill -f hcitool
sudo pkill -f gatttool
sudo pkill -f python.*btle

# Stop Bluetooth service
echo "Stopping Bluetooth service..."
sudo systemctl stop bluetooth

# Reset HCI interface
echo "Resetting HCI interface..."
sudo hciconfig hci0 down
sleep 2
sudo hciconfig hci0 reset
sleep 2
sudo hciconfig hci0 up
sleep 2

# Restart Bluetooth service
echo "Starting Bluetooth service..."
sudo systemctl start bluetooth
sleep 3

# Check Bluetooth status
echo "Checking Bluetooth status..."
sudo hciconfig -a

# Test basic scanning with hcitool
echo ""
echo "Testing basic BLE scan..."
timeout 10s sudo hcitool lescan | head -20

echo ""
echo "Bluetooth reset complete. Try scanning again."
