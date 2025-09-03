#!/usr/bin/env python3
"""
Detailed BMS Test with explicit error handling and notification setup
"""

import sys
import time
import logging
import binascii
from datetime import datetime

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

# Force detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetailedBMSDelegate(DefaultDelegate):
    """Detailed delegate with explicit logging"""
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.responses = []
        logger.info("BMS Delegate initialized")
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({
            'handle': cHandle,
            'data': hex_data,
            'timestamp': datetime.now().isoformat()
        })
        print(f"NOTIFICATION RECEIVED - Handle: {cHandle}, Data: {hex_data}")
        logger.info(f"BMS Response on handle {cHandle}: {hex_data}")

def detailed_bms_test(mac_address: str):
    """Detailed BMS test with step-by-step logging"""
    
    print(f"=== Detailed BMS Test for {mac_address} ===")
    
    peripheral = None
    delegate = DetailedBMSDelegate()
    
    try:
        # Step 1: Connect
        print("Step 1: Connecting to device...")
        logger.info(f"Attempting connection to {mac_address}")
        peripheral = Peripheral(mac_address, addrType="public")
        print("✓ Connected successfully")
        
        # Step 2: Set delegate
        print("Step 2: Setting up notification delegate...")
        peripheral.setDelegate(delegate)
        print("✓ Delegate set")
        
        # Step 3: Enable notifications on handle 21
        print("Step 3: Enabling notifications...")
        try:
            # Enable notifications by writing to Client Characteristic Configuration Descriptor
            # Handle 21 + 1 = 22 is typically the CCCD handle
            peripheral.writeCharacteristic(22, b'\x01\x00', False)
            print("✓ Notifications enabled on handle 22")
        except Exception as e:
            print(f"⚠ Could not enable notifications on handle 22: {e}")
            # Try other common CCCD handles
            for cccd_handle in [23, 24, 25]:
                try:
                    peripheral.writeCharacteristic(cccd_handle, b'\x01\x00', False)
                    print(f"✓ Notifications enabled on handle {cccd_handle}")
                    break
                except:
                    continue
        
        # Step 4: Send BMS commands
        bms_commands = [
            {
                'name': 'Basic Info (0x03)',
                'data': b'\xdd\xa5\x03\x00\xff\xfd\x77'
            },
            {
                'name': 'Cell Voltages (0x04)', 
                'data': b'\xdd\xa5\x04\x00\xff\xfc\x77'
            }
        ]
        
        for i, cmd in enumerate(bms_commands):
            print(f"\nStep {4+i}: Testing {cmd['name']}")
            logger.info(f"Sending command: {binascii.hexlify(cmd['data']).decode('utf-8')}")
            
            try:
                # Send command
                print(f"  Sending command to handle 21...")
                peripheral.writeCharacteristic(21, cmd['data'], False)
                print(f"  ✓ Command sent successfully")
                
                # Wait for response with detailed timeout handling
                print(f"  Waiting for response (5 seconds)...")
                start_time = time.time()
                
                while time.time() - start_time < 5:
                    if peripheral.waitForNotifications(0.5):
                        print(f"  ✓ Notification received!")
                        break
                    else:
                        print(f"  . Still waiting... ({time.time() - start_time:.1f}s)")
                else:
                    print(f"  ⚠ No response after 5 seconds")
                
                time.sleep(1)  # Pause between commands
                
            except Exception as e:
                print(f"  ✗ Error sending command: {e}")
                logger.error(f"Command error: {e}")
                
                # Check if connection is still alive
                try:
                    # Try a simple write to test connection
                    peripheral.writeCharacteristic(21, b'\x00', False)
                    print(f"  Connection still alive")
                except:
                    print(f"  Connection lost, attempting reconnect...")
                    try:
                        peripheral = Peripheral(mac_address, addrType="public")
                        peripheral.setDelegate(delegate)
                        print(f"  ✓ Reconnected")
                    except Exception as reconnect_error:
                        print(f"  ✗ Reconnection failed: {reconnect_error}")
                        break
        
        # Step 6: Summary
        print(f"\n=== Test Summary ===")
        print(f"Total responses received: {len(delegate.responses)}")
        
        if delegate.responses:
            print("Responses:")
            for i, resp in enumerate(delegate.responses):
                print(f"  {i+1}. Handle {resp['handle']}: {resp['data']}")
            return True
        else:
            print("No BMS responses received")
            return False
            
    except BTLEException as e:
        print(f"✗ Bluetooth error: {e}")
        logger.error(f"Bluetooth error: {e}")
        return False
    except Exception as e:
        print(f"✗ General error: {e}")
        logger.error(f"General error: {e}")
        return False
    finally:
        if peripheral:
            try:
                print("Disconnecting...")
                peripheral.disconnect()
                print("✓ Disconnected")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Detailed BMS communication test')
    parser.add_argument('mac', help='MAC address of BMS device')
    
    args = parser.parse_args()
    
    success = detailed_bms_test(args.mac)
    
    if success:
        print("\n🎉 BMS communication working!")
    else:
        print("\n❌ BMS communication failed")
        print("\nTroubleshooting steps:")
        print("1. Ensure BMS device is powered on")
        print("2. Check device is in range")
        print("3. Verify MAC address is correct")
        print("4. Try power cycling the BMS device")

if __name__ == "__main__":
    main()
