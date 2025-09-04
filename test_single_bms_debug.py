#!/usr/bin/env python3
"""
Debug script to test single BMS connection with detailed error reporting
"""

import sys
import time
import logging
import binascii
from datetime import datetime

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException, Scanner
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scan_for_devices():
    """Scan for BLE devices"""
    print("Scanning for BLE devices...")
    try:
        scanner = Scanner()
        devices = scanner.scan(10.0)
        
        target_macs = ["A4:C1:38:7C:2D:F0", "E0:9F:2A:E4:94:1D"]
        
        print(f"Found {len(devices)} devices:")
        for dev in devices:
            status = "*** TARGET ***" if dev.addr.upper() in [m.upper() for m in target_macs] else ""
            print(f"  {dev.addr} ({dev.addrType}) RSSI={dev.rssi} {status}")
            
        return devices
    except Exception as e:
        print(f"Scan failed: {e}")
        return []

def test_connection(mac_address, track):
    """Test connection to single BMS with detailed logging"""
    print(f"\n=== Testing {track} track: {mac_address} ===")
    
    try:
        print("Step 1: Creating Peripheral connection...")
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        print("Step 2: Getting services...")
        services = peripheral.getServices()
        print(f"✓ Found {len(services)} services")
        
        for svc in services:
            print(f"  Service: {svc.uuid}")
            try:
                chars = svc.getCharacteristics()
                for char in chars:
                    props = []
                    if char.supportsRead(): props.append("READ")
                    if char.supportsWrite(): props.append("WRITE")
                    if char.supportsNotify(): props.append("NOTIFY")
                    print(f"    Char: {char.uuid} Handle:{char.getHandle()} Props:{','.join(props)}")
            except Exception as e:
                print(f"    Error reading characteristics: {e}")
        
        print("Step 3: Testing notification setup...")
        try:
            # Try different handles for notifications
            for handle in [22, 23, 24, 25]:
                try:
                    peripheral.writeCharacteristic(handle, b'\x01\x00', False)
                    print(f"✓ Notifications enabled on handle {handle}")
                    break
                except Exception as e:
                    print(f"  Handle {handle} failed: {e}")
        except Exception as e:
            print(f"✗ Notification setup failed: {e}")
        
        print("Step 4: Testing BMS commands...")
        try:
            # Try sending basic info command
            cmd_data = b'\xdd\xa5\x03\x00\xff\xfd\x77'
            peripheral.writeCharacteristic(21, cmd_data, False)
            print(f"✓ Command sent: {binascii.hexlify(cmd_data).decode()}")
            
            # Wait for response
            print("Waiting for response...")
            for i in range(10):
                if peripheral.waitForNotifications(1.0):
                    print("✓ Received notification")
                else:
                    print(f"  No response ({i+1}/10)")
                    
        except Exception as e:
            print(f"✗ Command failed: {e}")
        
        print("Step 5: Disconnecting...")
        peripheral.disconnect()
        print("✓ Disconnected")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

class DebugDelegate(DefaultDelegate):
    def __init__(self, track):
        DefaultDelegate.__init__(self)
        self.track = track
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        print(f"NOTIFICATION {self.track}: Handle {cHandle} = {hex_data}")

if __name__ == "__main__":
    print("=== BMS Debug Tool ===")
    
    # Step 1: Scan for devices
    devices = scan_for_devices()
    
    # Step 2: Test connections
    LEFT_MAC = "A4:C1:38:7C:2D:F0"
    RIGHT_MAC = "E0:9F:2A:E4:94:1D"
    
    print(f"\nTesting LEFT track...")
    left_result = test_connection(LEFT_MAC, "LEFT")
    
    time.sleep(2)
    
    print(f"\nTesting RIGHT track...")
    right_result = test_connection(RIGHT_MAC, "RIGHT")
    
    print(f"\n=== Results ===")
    print(f"LEFT track:  {'✓ Success' if left_result else '✗ Failed'}")
    print(f"RIGHT track: {'✓ Success' if right_result else '✗ Failed'}")
