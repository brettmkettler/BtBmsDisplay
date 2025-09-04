#!/usr/bin/env python3

import sys
import time
import subprocess

try:
    from bluepy3.btle import Scanner, DefaultDelegate, Peripheral, ADDR_TYPE_PUBLIC
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

def reset_bluetooth():
    """Reset Bluetooth stack"""
    print("Resetting Bluetooth stack...")
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)
        time.sleep(2)
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'down'], check=True)
        time.sleep(1)
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=True)
        time.sleep(2)
        print("✓ Bluetooth stack reset")
    except Exception as e:
        print(f"⚠ Bluetooth reset failed: {e}")

def scan_for_devices():
    """Scan for BLE devices"""
    print("\nScanning for BLE devices...")
    scanner = Scanner().withDelegate(ScanDelegate())
    
    try:
        devices = scanner.scan(10.0)  # Scan for 10 seconds
        
        target_macs = ["A4:C1:38:7C:2D:F0", "E0:9F:2A:E4:94:1D"]
        found_targets = []
        
        print(f"\nFound {len(devices)} devices:")
        for dev in devices:
            mac = dev.addr.upper()
            name = dev.getValueText(9) or "Unknown"
            rssi = dev.rssi
            
            if mac in [m.upper() for m in target_macs]:
                found_targets.append(dev)
                print(f"🎯 TARGET: {mac} - {name} (RSSI: {rssi})")
            else:
                print(f"   {mac} - {name} (RSSI: {rssi})")
        
        return found_targets
        
    except Exception as e:
        print(f"✗ Scan failed: {e}")
        return []

def test_connection(device):
    """Test connection to a specific device"""
    print(f"\nTesting connection to {device.addr}...")
    
    try:
        # Connect to device
        peripheral = Peripheral(device.addr, addrType=ADDR_TYPE_PUBLIC)
        print(f"✓ Connected to {device.addr}")
        
        # Get services
        services = peripheral.getServices()
        print(f"Found {len(services)} services:")
        
        for service in services:
            print(f"  Service: {service.uuid}")
            
            # Get characteristics for each service
            try:
                characteristics = service.getCharacteristics()
                for char in characteristics:
                    props = []
                    if char.supportsRead():
                        props.append("READ")
                    if char.supportsWrite():
                        props.append("WRITE")
                    if char.supportsNotify():
                        props.append("NOTIFY")
                    
                    print(f"    Char: {char.uuid} ({', '.join(props)})")
            except Exception as e:
                print(f"    Error getting characteristics: {e}")
        
        peripheral.disconnect()
        print(f"✓ Disconnected from {device.addr}")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def main():
    print("BMS Device Scanner")
    print("=" * 50)
    
    # Reset Bluetooth first
    reset_bluetooth()
    
    # Scan for devices
    found_devices = scan_for_devices()
    
    if not found_devices:
        print("\n❌ No target BMS devices found!")
        print("Make sure devices are:")
        print("  - Powered on")
        print("  - In pairing/discoverable mode")
        print("  - Within range")
        return
    
    print(f"\n✓ Found {len(found_devices)} target device(s)")
    
    # Test each found device
    for device in found_devices:
        success = test_connection(device)
        if success:
            print(f"✅ {device.addr} is working properly")
        else:
            print(f"❌ {device.addr} has connection issues")

if __name__ == "__main__":
    main()
