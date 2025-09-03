#!/usr/bin/env python3
"""
Immediate Response Test - Respond to '00' notification immediately
"""

import sys
import time
import binascii

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

class ImmediateDelegate(DefaultDelegate):
    def __init__(self, peripheral):
        DefaultDelegate.__init__(self)
        self.peripheral = peripheral
        self.notifications = []
        self.responded_to_handshake = False
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.notifications.append({
            'handle': cHandle, 
            'data': hex_data,
            'timestamp': time.time()
        })
        print(f"RX: Handle {cHandle} = {hex_data}")
        
        # Respond immediately to '00' handshake
        if hex_data == '00' and not self.responded_to_handshake:
            print("  -> Responding to handshake immediately")
            try:
                # Try different immediate responses
                responses = [
                    b'\xdd\xa5\x04\x00\xff\xfc\x77',  # Original BMS command
                    b'\x00',                           # Echo back
                    b'\x01',                           # Simple ACK
                    b'\xdd\xa5\x03\x00\xff\xfd\x77'   # Alternative command
                ]
                
                for i, response in enumerate(responses):
                    try:
                        self.peripheral.writeCharacteristic(21, response, False)
                        print(f"  ✓ Sent response {i+1}: {binascii.hexlify(response).decode('utf-8')}")
                        self.responded_to_handshake = True
                        break
                    except Exception as e:
                        print(f"  ✗ Response {i+1} failed: {e}")
                        if "disconnected" in str(e).lower():
                            break
                        
            except Exception as e:
                print(f"  ✗ Failed to respond: {e}")

def test_immediate_response(mac_address: str, device_name: str):
    """Test immediate response to handshake notification"""
    
    print(f"\n=== {device_name} Immediate Response Test ===")
    
    peripheral = None
    
    try:
        # Connect
        print("Connecting...")
        peripheral = Peripheral(mac_address, addrType="public")
        
        # Create delegate with peripheral reference
        delegate = ImmediateDelegate(peripheral)
        peripheral.setDelegate(delegate)
        print("✓ Connected with immediate response delegate")
        
        # Enable notifications
        print("Enabling notifications...")
        peripheral.writeCharacteristic(22, b'\x01\x00', False)
        print("✓ Notifications enabled")
        
        # Wait for handshake and response
        print("Waiting for handshake and testing immediate response...")
        start_time = time.time()
        
        for i in range(20):  # 20 x 0.5s = 10s total
            try:
                if peripheral.waitForNotifications(0.5):
                    elapsed = time.time() - start_time
                    print(f"  Activity at {elapsed:.1f}s")
                else:
                    elapsed = time.time() - start_time
                    if elapsed > 10:
                        break
                    print(f"  Monitoring... {elapsed:.1f}s")
            except Exception as e:
                print(f"  ✗ Error during monitoring: {e}")
                break
        
        # Summary
        print(f"\nNotifications received: {len(delegate.notifications)}")
        for notif in delegate.notifications:
            print(f"  Handle {notif['handle']}: {notif['data']}")
        
        print(f"Responded to handshake: {delegate.responded_to_handshake}")
        
        return len(delegate.notifications) > 1  # More than just the handshake
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
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
    
    parser = argparse.ArgumentParser(description='Test immediate response to BMS handshake')
    parser.add_argument('--left', action='store_true', help='Test LEFT track')
    parser.add_argument('--right', action='store_true', help='Test RIGHT track')
    
    args = parser.parse_args()
    
    left_mac = 'A4:C1:38:7C:2D:F0'
    right_mac = 'E0:9F:2A:E4:94:1D'
    
    if args.left:
        success = test_immediate_response(left_mac, 'LEFT')
        print(f"LEFT result: {'✓ Success' if success else '✗ Failed'}")
    elif args.right:
        success = test_immediate_response(right_mac, 'RIGHT')
        print(f"RIGHT result: {'✓ Success' if success else '✗ Failed'}")
    else:
        print("Use --left or --right")

if __name__ == "__main__":
    main()
