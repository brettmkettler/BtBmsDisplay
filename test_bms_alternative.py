#!/usr/bin/env python3
"""
Alternative BMS Command Test
Try different command approaches to avoid disconnection
"""

import sys
import time
import logging
import binascii

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class TestDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.responses = []
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({
            'handle': cHandle,
            'data': hex_data,
            'timestamp': time.time()
        })
        print(f"NOTIFICATION: Handle {cHandle}, Data: {hex_data}")

def test_alternative_commands(mac_address: str, device_name: str):
    """Test alternative BMS command approaches"""
    
    print(f"\n=== Testing {device_name} BMS with Alternative Commands ===")
    
    peripheral = None
    delegate = TestDelegate()
    
    try:
        # Connect
        print("Connecting...")
        peripheral = Peripheral(mac_address, addrType="public")
        peripheral.setDelegate(delegate)
        print("✓ Connected")
        
        # Test different notification enable approaches
        print("\nTesting notification setup...")
        
        # Try multiple CCCD handles
        for cccd_handle in [22, 23, 24, 25]:
            try:
                peripheral.writeCharacteristic(cccd_handle, b'\x01\x00', False)
                print(f"✓ Notifications enabled on handle {cccd_handle}")
                time.sleep(0.5)
                break
            except Exception as e:
                print(f"⚠ Handle {cccd_handle} failed: {e}")
        
        # Wait for any initial notifications
        print("Waiting for initial notifications...")
        peripheral.waitForNotifications(2)
        
        # Test different command handles and approaches
        command_tests = [
            {
                'name': 'Original approach (handle 21)',
                'handle': 21,
                'command': b'\xdd\xa5\x04\x00\xff\xfc\x77'
            },
            {
                'name': 'Alternative handle (handle 17)',
                'handle': 17,
                'command': b'\xdd\xa5\x04\x00\xff\xfc\x77'
            },
            {
                'name': 'Simple read command',
                'handle': 21,
                'command': b'\x01'
            },
            {
                'name': 'Different BMS command (0x05)',
                'handle': 21,
                'command': b'\xdd\xa5\x05\x00\xff\xfb\x77'
            }
        ]
        
        for test in command_tests:
            print(f"\n--- {test['name']} ---")
            
            try:
                print(f"Sending to handle {test['handle']}: {binascii.hexlify(test['command']).decode('utf-8')}")
                peripheral.writeCharacteristic(test['handle'], test['command'], False)
                print("✓ Command sent")
                
                # Wait for response
                start_time = time.time()
                timeout = 3
                
                while time.time() - start_time < timeout:
                    if peripheral.waitForNotifications(0.5):
                        print(f"✓ Response received after {time.time() - start_time:.1f}s")
                        break
                    else:
                        print(f"  Waiting... {time.time() - start_time:.1f}s")
                else:
                    print(f"⚠ No response after {timeout}s")
                
                time.sleep(1)  # Pause between commands
                
            except Exception as e:
                print(f"✗ Command failed: {e}")
                if "disconnected" in str(e).lower():
                    print("Device disconnected - stopping tests")
                    break
        
        # Summary
        print(f"\n--- {device_name} Summary ---")
        print(f"Total responses: {len(delegate.responses)}")
        
        if delegate.responses:
            for i, resp in enumerate(delegate.responses):
                print(f"  {i+1}. Handle {resp['handle']}: {resp['data']}")
            return True
        else:
            print("No responses received")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
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
    
    parser = argparse.ArgumentParser(description='Test alternative BMS commands')
    parser.add_argument('--left', action='store_true', help='Test LEFT track BMS')
    parser.add_argument('--right', action='store_true', help='Test RIGHT track BMS')
    
    args = parser.parse_args()
    
    left_mac = 'A4:C1:38:7C:2D:F0'
    right_mac = 'E0:9F:2A:E4:94:1D'
    
    if args.left:
        test_alternative_commands(left_mac, 'LEFT')
    elif args.right:
        test_alternative_commands(right_mac, 'RIGHT')
    else:
        print("Please specify --left or --right")

if __name__ == "__main__":
    main()
