#!/usr/bin/env python3
"""
Alternative BLE Discovery Test
Tests multiple approaches to BLE service discovery for troubleshooting
"""

import sys
import time
import logging
import binascii
from datetime import datetime

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException, Scanner, UUID
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection_methods(mac_address: str):
    """Test different connection and discovery methods"""
    
    print(f"=== Testing Multiple Discovery Methods for {mac_address} ===\n")
    
    # Method 1: Standard connection with delays
    print("--- Method 1: Standard Connection with Delays ---")
    try:
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        # Add delay before service discovery
        print("Waiting 3 seconds before service discovery...")
        time.sleep(3)
        
        services = peripheral.getServices()
        print(f"Services found: {len(services)}")
        
        if len(services) > 0:
            for i, service in enumerate(services):
                print(f"  Service {i+1}: {service.uuid}")
                try:
                    chars = service.getCharacteristics()
                    print(f"    Characteristics: {len(chars)}")
                    for j, char in enumerate(chars):
                        print(f"      Char {j+1}: {char.uuid} (Handle: {char.getHandle()}) - {char.propertiesToString()}")
                except Exception as e:
                    print(f"    Error getting characteristics: {e}")
        
        peripheral.disconnect()
        print("Disconnected\n")
        
    except Exception as e:
        print(f"✗ Method 1 failed: {e}\n")
    
    # Method 2: Manual service discovery by UUID
    print("--- Method 2: Manual Service Discovery ---")
    try:
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        # Try common BMS service UUIDs
        common_service_uuids = [
            "fff0",  # Common BMS service
            "ffe0",  # Common BLE service
            "1800",  # Generic Access
            "1801",  # Generic Attribute
            "180f",  # Battery Service
            "180a"   # Device Information
        ]
        
        found_services = []
        for uuid_str in common_service_uuids:
            try:
                service = peripheral.getServiceByUUID(UUID(uuid_str))
                found_services.append(service)
                print(f"✓ Found service: {uuid_str}")
                
                # Get characteristics
                try:
                    chars = service.getCharacteristics()
                    print(f"  Characteristics: {len(chars)}")
                    for char in chars:
                        print(f"    {char.uuid} (Handle: {char.getHandle()}) - {char.propertiesToString()}")
                except Exception as e:
                    print(f"  Error getting characteristics: {e}")
                    
            except Exception:
                # Service not found, continue
                pass
        
        print(f"Total services found manually: {len(found_services)}")
        peripheral.disconnect()
        print("Disconnected\n")
        
    except Exception as e:
        print(f"✗ Method 2 failed: {e}\n")
    
    # Method 3: Direct characteristic access by handle
    print("--- Method 3: Direct Characteristic Handle Testing ---")
    try:
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        # Test common BMS characteristic handles
        test_handles = [0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f]
        
        working_handles = []
        for handle in test_handles:
            try:
                # Try to read the characteristic properties
                # This is a simple test to see if the handle exists
                peripheral.writeCharacteristic(handle, b'\x01\x00', False)
                working_handles.append(handle)
                print(f"✓ Handle {handle} (0x{handle:02x}) appears to be writable")
            except Exception:
                # Handle doesn't exist or not writable
                pass
        
        print(f"Found {len(working_handles)} potentially writable handles: {[hex(h) for h in working_handles]}")
        
        # Test BMS communication on working handles
        if working_handles:
            print("\nTesting BMS communication on found handles:")
            
            class TestDelegate(DefaultDelegate):
                def __init__(self):
                    DefaultDelegate.__init__(self)
                    self.responses = []
                
                def handleNotification(self, cHandle, data):
                    hex_data = binascii.hexlify(data).decode('utf-8')
                    self.responses.append((cHandle, hex_data))
                    print(f"  Response on handle {cHandle}: {hex_data}")
            
            delegate = TestDelegate()
            peripheral.setDelegate(delegate)
            
            for handle in working_handles[:3]:  # Test first 3 handles
                try:
                    print(f"  Testing BMS command on handle {handle} (0x{handle:02x})...")
                    # Send basic info request
                    peripheral.writeCharacteristic(handle, b'\xdd\xa5\x03\x00\xff\xfd\x77', False)
                    
                    if peripheral.waitForNotifications(2):
                        print(f"    ✓ Got response on handle {handle}!")
                    else:
                        print(f"    No response on handle {handle}")
                        
                except Exception as e:
                    print(f"    Error testing handle {handle}: {e}")
        
        peripheral.disconnect()
        print("Disconnected\n")
        
    except Exception as e:
        print(f"✗ Method 3 failed: {e}\n")
    
    # Method 4: Low-level discovery
    print("--- Method 4: Low-level Discovery ---")
    try:
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        # Try to get device information
        try:
            # Read device name if available
            device_name_char = peripheral.getCharacteristics(uuid=UUID(0x2A00))
            if device_name_char:
                name = device_name_char[0].read().decode('utf-8', errors='ignore')
                print(f"Device name: {name}")
        except:
            print("Could not read device name")
        
        # Try to discover all handles by brute force
        print("Scanning all handles from 1 to 50...")
        valid_handles = []
        
        for handle in range(1, 51):
            try:
                # Try to read from handle
                data = peripheral.readCharacteristic(handle)
                valid_handles.append(handle)
                hex_data = binascii.hexlify(data).decode('utf-8') if data else "empty"
                print(f"  Handle {handle} (0x{handle:02x}): {hex_data}")
            except:
                # Handle doesn't exist or not readable
                pass
        
        print(f"Found {len(valid_handles)} readable handles")
        
        peripheral.disconnect()
        print("Disconnected\n")
        
    except Exception as e:
        print(f"✗ Method 4 failed: {e}\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Alternative BLE discovery test')
    parser.add_argument('mac', help='MAC address to test')
    
    args = parser.parse_args()
    
    test_connection_methods(args.mac)
    
    print("=== Summary ===")
    print("If any method found services/characteristics, use those handles for BMS communication.")
    print("If all methods failed, the device may not be a standard BLE device or may require pairing.")

if __name__ == "__main__":
    main()
