#!/usr/bin/env python3
"""
Single BMS Test with Detailed Notification Debugging
Tests one BMS device at a time to isolate issues
"""

import sys
import time
import logging
import binascii

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class DebugDelegate(DefaultDelegate):
    """Debug delegate with detailed logging"""
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.responses = []
        print("Debug delegate initialized")
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({
            'handle': cHandle,
            'data': hex_data,
            'timestamp': time.time()
        })
        print(f"NOTIFICATION: Handle {cHandle}, Data: {hex_data}")
        logger.info(f"Notification received on handle {cHandle}: {hex_data}")

def test_single_bms(mac_address: str, device_name: str):
    """Test a single BMS device with detailed debugging"""
    
    print(f"\n=== Testing {device_name} BMS: {mac_address} ===")
    
    peripheral = None
    delegate = DebugDelegate()
    
    try:
        # Step 1: Connect
        print("Step 1: Connecting...")
        peripheral = Peripheral(mac_address, addrType="public")
        peripheral.setDelegate(delegate)
        print("✓ Connected and delegate set")
        
        # Step 2: Enable notifications
        print("Step 2: Enabling notifications...")
        try:
            peripheral.writeCharacteristic(22, b'\x01\x00', False)
            print("✓ Notifications enabled on handle 22")
        except Exception as e:
            print(f"⚠ Could not enable notifications on handle 22: {e}")
        
        # Step 3: Send BMS command
        print("Step 3: Sending BMS command...")
        command = b'\xdd\xa5\x04\x00\xff\xfc\x77'
        print(f"Command: {binascii.hexlify(command).decode('utf-8')}")
        
        peripheral.writeCharacteristic(21, command, False)
        print("✓ Command sent to handle 21")
        
        # Step 4: Wait for response with detailed monitoring
        print("Step 4: Waiting for response...")
        start_time = time.time()
        timeout = 5
        
        while time.time() - start_time < timeout:
            if peripheral.waitForNotifications(0.5):
                print(f"✓ Notification received after {time.time() - start_time:.1f}s")
                break
            else:
                elapsed = time.time() - start_time
                print(f"  Waiting... {elapsed:.1f}s")
        else:
            print(f"⚠ No response after {timeout}s")
        
        # Step 5: Summary
        print(f"\n--- {device_name} Results ---")
        print(f"Responses received: {len(delegate.responses)}")
        
        if delegate.responses:
            for i, resp in enumerate(delegate.responses):
                print(f"  {i+1}. Handle {resp['handle']}: {resp['data']}")
            return True
        else:
            print("No responses received")
            return False
            
    except Exception as e:
        print(f"✗ Error testing {device_name}: {e}")
        return False
        
    finally:
        if peripheral:
            try:
                peripheral.disconnect()
                print(f"✓ Disconnected from {device_name}")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test single BMS device')
    parser.add_argument('--left', action='store_true', help='Test LEFT track BMS')
    parser.add_argument('--right', action='store_true', help='Test RIGHT track BMS')
    parser.add_argument('--both', action='store_true', help='Test both BMS devices')
    
    args = parser.parse_args()
    
    left_mac = 'A4:C1:38:7C:2D:F0'
    right_mac = 'E0:9F:2A:E4:94:1D'
    
    results = {}
    
    if args.left or args.both:
        results['left'] = test_single_bms(left_mac, 'LEFT')
        time.sleep(2)  # Pause between tests
    
    if args.right or args.both:
        results['right'] = test_single_bms(right_mac, 'RIGHT')
    
    if not any([args.left, args.right, args.both]):
        print("Please specify --left, --right, or --both")
        return
    
    print(f"\n=== Final Results ===")
    for device, success in results.items():
        status = "✓ Working" if success else "✗ Failed"
        print(f"{device.upper()} track: {status}")

if __name__ == "__main__":
    main()
