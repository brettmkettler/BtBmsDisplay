#!/usr/bin/env python3
"""
Minimal BMS Test - No waiting periods to avoid disconnection
"""

import sys
import time
import binascii

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class QuickDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.responses = []
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({'handle': cHandle, 'data': hex_data})
        print(f"RX: Handle {cHandle} = {hex_data}")

def test_minimal_bms(mac_address: str, device_name: str):
    """Minimal test with no waiting periods"""
    
    print(f"\n=== Minimal {device_name} Test ===")
    
    peripheral = None
    delegate = QuickDelegate()
    
    try:
        # Connect
        peripheral = Peripheral(mac_address, addrType="public")
        peripheral.setDelegate(delegate)
        print("✓ Connected")
        
        # Enable notifications immediately
        peripheral.writeCharacteristic(22, b'\x01\x00', False)
        print("✓ Notifications enabled")
        
        # Check for immediate response
        if peripheral.waitForNotifications(0.1):
            print("✓ Initial notification received")
        
        # Send command immediately without delay
        command = b'\xdd\xa5\x04\x00\xff\xfc\x77'
        print(f"Sending: {binascii.hexlify(command).decode('utf-8')}")
        peripheral.writeCharacteristic(21, command, False)
        print("✓ Command sent")
        
        # Quick response check
        for i in range(10):  # 10 x 0.3s = 3s total
            if peripheral.waitForNotifications(0.3):
                print(f"✓ Response after {(i+1)*0.3:.1f}s")
                break
        else:
            print("⚠ No response")
        
        print(f"Total responses: {len(delegate.responses)}")
        for resp in delegate.responses:
            print(f"  Handle {resp['handle']}: {resp['data']}")
            
        return len(delegate.responses) > 1  # More than just the initial '00'
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
        
    finally:
        if peripheral:
            try:
                peripheral.disconnect()
                print("✓ Disconnected")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Minimal BMS test')
    parser.add_argument('--left', action='store_true', help='Test LEFT track')
    parser.add_argument('--right', action='store_true', help='Test RIGHT track')
    
    args = parser.parse_args()
    
    left_mac = 'A4:C1:38:7C:2D:F0'
    right_mac = 'E0:9F:2A:E4:94:1D'
    
    if args.left:
        success = test_minimal_bms(left_mac, 'LEFT')
        print(f"LEFT result: {'✓ Success' if success else '✗ Failed'}")
    elif args.right:
        success = test_minimal_bms(right_mac, 'RIGHT')
        print(f"RIGHT result: {'✓ Success' if success else '✗ Failed'}")
    else:
        print("Use --left or --right")

if __name__ == "__main__":
    main()
