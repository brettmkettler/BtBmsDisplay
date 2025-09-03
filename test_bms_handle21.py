#!/usr/bin/env python3
"""
Test BMS Communication on Handle 21 (0x15)
Simple test to verify BMS data retrieval using the correct handle
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BMSTestDelegate(DefaultDelegate):
    """Delegate to handle BMS notifications"""
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.responses = []
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({
            'handle': cHandle,
            'data': hex_data,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"BMS Response on handle {cHandle}: {hex_data}")
        
        # Parse common BMS data patterns
        if 'dd04' in hex_data:
            logger.info("  -> Cell voltage data detected")
        elif 'dd03' in hex_data:
            logger.info("  -> Pack info data detected")
        elif '77' in hex_data:
            logger.info("  -> Status data detected")

def test_bms_communication(mac_address: str):
    """Test BMS communication on handle 21"""
    
    logger.info(f"Testing BMS communication with {mac_address} on handle 21 (0x15)")
    
    peripheral = None
    delegate = BMSTestDelegate()
    
    try:
        # Connect
        logger.info("Connecting...")
        peripheral = Peripheral(mac_address, addrType="public")
        peripheral.setDelegate(delegate)
        logger.info("✓ Connected successfully")
        
        # BMS commands to test
        bms_commands = [
            {
                'name': 'Basic Info Request (0x03)',
                'data': b'\xdd\xa5\x03\x00\xff\xfd\x77',
                'description': 'Pack voltage, current, capacity, etc.'
            },
            {
                'name': 'Cell Voltages Request (0x04)', 
                'data': b'\xdd\xa5\x04\x00\xff\xfc\x77',
                'description': 'Individual cell voltages'
            },
            {
                'name': 'Hardware Version (0x05)',
                'data': b'\xdd\xa5\x05\x00\xff\xfb\x77',
                'description': 'BMS hardware/firmware info'
            }
        ]
        
        successful_commands = 0
        
        for i, cmd in enumerate(bms_commands):
            logger.info(f"\n--- Test {i+1}: {cmd['name']} ---")
            logger.info(f"Description: {cmd['description']}")
            
            try:
                # Send command
                logger.info("Sending BMS command...")
                peripheral.writeCharacteristic(21, cmd['data'], False)
                
                # Wait for response
                logger.info("Waiting for response...")
                if peripheral.waitForNotifications(3):
                    logger.info("✓ Response received!")
                    successful_commands += 1
                else:
                    logger.warning("⚠ No response received")
                
                # Brief pause between commands
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"✗ Error sending {cmd['name']}: {e}")
                # Try to reconnect if connection lost
                if "disconnected" in str(e).lower():
                    logger.info("Attempting to reconnect...")
                    try:
                        peripheral = Peripheral(mac_address, addrType="public")
                        peripheral.setDelegate(delegate)
                        logger.info("✓ Reconnected")
                    except:
                        logger.error("Failed to reconnect")
                        break
        
        # Summary
        logger.info(f"\n=== Test Results ===")
        logger.info(f"Commands sent: {len(bms_commands)}")
        logger.info(f"Successful responses: {successful_commands}")
        logger.info(f"Total responses received: {len(delegate.responses)}")
        
        if delegate.responses:
            logger.info("\nAll responses:")
            for i, resp in enumerate(delegate.responses):
                logger.info(f"  {i+1}. Handle {resp['handle']}: {resp['data']}")
        
        if successful_commands > 0:
            logger.info("🎉 BMS communication is working!")
            return True
        else:
            logger.error("❌ No successful BMS communication")
            return False
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False
        
    finally:
        if peripheral:
            try:
                peripheral.disconnect()
                logger.info("Disconnected")
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test BMS communication on handle 21')
    parser.add_argument('mac', help='MAC address of BMS device')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = test_bms_communication(args.mac)
    
    if success:
        print("\n✅ BMS communication test PASSED")
        print("Your BMS device is working correctly with handle 21 (0x15)")
        print("The original bms_reader.py should work with bluepy3")
    else:
        print("\n❌ BMS communication test FAILED")
        print("Check device power, range, and MAC address")

if __name__ == "__main__":
    main()
