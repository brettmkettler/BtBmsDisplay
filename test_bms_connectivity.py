#!/usr/bin/env python3
"""
Quick BMS connectivity test - checks if devices are reachable
"""

import time
import signal
import sys

try:
    from bluepy3.btle import Peripheral, BTLEException, Scanner
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

# BMS device addresses
BMS_DEVICES = {
    "LEFT": "A4:C1:38:7C:2D:F0",
    "RIGHT": "E0:9F:2A:E4:94:1D"
}

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Connection timeout")

def test_device_connection(name, mac_address, timeout=10):
    """Test connection to a single BMS device with timeout"""
    print(f"\nTesting {name} ({mac_address})...")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        print(f"  Attempting connection (timeout: {timeout}s)...")
        peripheral = Peripheral(mac_address, addrType="public")
        
        # Cancel timeout
        signal.alarm(0)
        
        print(f"  ✓ Connected successfully!")
        
        # Try to get services
        try:
            services = peripheral.getServices()
            print(f"  ✓ Found {len(services)} services")
            for service in services:
                print(f"    - Service: {service.uuid}")
        except Exception as e:
            print(f"  ⚠ Could not enumerate services: {e}")
        
        # Disconnect
        peripheral.disconnect()
        print(f"  ✓ Disconnected cleanly")
        return True
        
    except TimeoutError:
        signal.alarm(0)
        print(f"  ✗ Connection timeout after {timeout}s")
        return False
    except BTLEException as e:
        signal.alarm(0)
        print(f"  ✗ Bluetooth error: {e}")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"  ✗ Unexpected error: {e}")
        return False

def scan_for_devices():
    """Scan for BLE devices"""
    print("Scanning for BLE devices...")
    try:
        scanner = Scanner()
        devices = scanner.scan(5.0)  # 5 second scan
        
        print(f"Found {len(devices)} devices:")
        target_found = []
        
        for dev in devices:
            name = dev.getValueText(9) or "Unknown"
            if dev.addr.upper() in [addr.upper() for addr in BMS_DEVICES.values()]:
                target_found.append(dev.addr.upper())
                print(f"  ✓ TARGET: {dev.addr} ({name}) RSSI: {dev.rssi}dB")
            else:
                print(f"    {dev.addr} ({name}) RSSI: {dev.rssi}dB")
        
        return target_found
        
    except Exception as e:
        print(f"Scan failed: {e}")
        return []

def main():
    print("=== BMS Connectivity Test ===")
    
    # First scan for devices
    found_devices = scan_for_devices()
    
    if not found_devices:
        print("\n⚠ No target BMS devices found in scan")
        print("This could mean:")
        print("  - Devices are powered off")
        print("  - Devices are out of range")
        print("  - Bluetooth interference")
        print("\nTrying direct connection anyway...")
    
    # Test each device
    results = {}
    for name, mac_address in BMS_DEVICES.items():
        results[name] = test_device_connection(name, mac_address, timeout=15)
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n=== Results ===")
    for name, success in results.items():
        status = "✓ REACHABLE" if success else "✗ UNREACHABLE"
        print(f"{name}: {status}")
    
    if any(results.values()):
        print("\n✓ At least one device is reachable")
        print("The dual_bms_service.py should work with timeout fixes")
    else:
        print("\n✗ No devices are reachable")
        print("Check:")
        print("  - BMS devices are powered on")
        print("  - Bluetooth is enabled: sudo systemctl status bluetooth")
        print("  - User permissions: groups $USER (should include 'bluetooth')")
        print("  - Reset Bluetooth: sudo systemctl restart bluetooth")

if __name__ == "__main__":
    main()
