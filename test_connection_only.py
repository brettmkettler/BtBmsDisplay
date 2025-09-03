#!/usr/bin/env python3
"""
Connection Only Test - Verify BLE connection stability without BMS commands
"""

import sys
import time
import binascii

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class ConnectionDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.notifications = []
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.notifications.append({
            'handle': cHandle, 
            'data': hex_data,
            'timestamp': time.time()
        })
        print(f"NOTIFICATION: Handle {cHandle} = {hex_data}")

def test_connection_stability(mac_address: str, device_name: str):
    """Test connection stability without sending BMS commands"""
    
    print(f"\n=== {device_name} Connection Stability Test ===")
    
    peripheral = None
    delegate = ConnectionDelegate()
    
    try:
        # Connect
        print("Connecting...")
        peripheral = Peripheral(mac_address, addrType="public")
        peripheral.setDelegate(delegate)
        print("✓ Connected")
        
        # Enable notifications
        print("Enabling notifications...")
        peripheral.writeCharacteristic(22, b'\x01\x00', False)
        print("✓ Notifications enabled")
        
        # Wait and monitor for 10 seconds without sending commands
        print("Monitoring connection for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            elapsed = time.time() - start_time
            
            # Check for notifications every 0.5 seconds
            if peripheral.waitForNotifications(0.5):
                print(f"  Notification at {elapsed:.1f}s")
            else:
                print(f"  Still connected at {elapsed:.1f}s")
        
        print("✓ Connection remained stable for 10 seconds")
        
        # Summary
        print(f"\nNotifications received: {len(delegate.notifications)}")
        for notif in delegate.notifications:
            print(f"  Handle {notif['handle']}: {notif['data']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
        
    finally:
        if peripheral:
            try:
                peripheral.disconnect()
                print("✓ Disconnected cleanly")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test BLE connection stability')
    parser.add_argument('--left', action='store_true', help='Test LEFT track')
    parser.add_argument('--right', action='store_true', help='Test RIGHT track')
    parser.add_argument('--both', action='store_true', help='Test both tracks')
    
    args = parser.parse_args()
    
    left_mac = 'A4:C1:38:7C:2D:F0'
    right_mac = 'E0:9F:2A:E4:94:1D'
    
    results = {}
    
    if args.left or args.both:
        results['LEFT'] = test_connection_stability(left_mac, 'LEFT')
        if args.both:
            time.sleep(2)
    
    if args.right or args.both:
        results['RIGHT'] = test_connection_stability(right_mac, 'RIGHT')
    
    if not any([args.left, args.right, args.both]):
        print("Use --left, --right, or --both")
        return
    
    print(f"\n=== Final Results ===")
    for device, success in results.items():
        status = "✓ Stable" if success else "✗ Failed"
        print(f"{device}: {status}")

if __name__ == "__main__":
    main()
