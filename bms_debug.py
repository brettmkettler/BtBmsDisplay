#!/usr/bin/env python3
"""
Enhanced BMS BLE Diagnostic Script
Provides detailed service and characteristic discovery for BMS debugging
"""

import sys
import time
import logging
import binascii
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException, Scanner, UUID
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DetailedBMSDebugger:
    """Enhanced BMS debugging with detailed service discovery"""
    
    def __init__(self):
        self.debug_results = {}
        
    def deep_service_discovery(self, mac_address: str) -> Dict[str, Any]:
        """Perform deep service and characteristic discovery"""
        logger.info(f"Starting deep discovery for {mac_address}...")
        
        result = {
            'mac_address': mac_address,
            'connected': False,
            'services': [],
            'all_characteristics': [],
            'writable_characteristics': [],
            'readable_characteristics': [],
            'notify_characteristics': [],
            'error': None
        }
        
        peripheral = None
        
        try:
            # Connect
            logger.info(f"Connecting to {mac_address}...")
            peripheral = Peripheral(mac_address, addrType="public")
            result['connected'] = True
            logger.info("✓ Connected successfully")
            
            # Get all services
            logger.info("Discovering all services...")
            services = peripheral.getServices()
            logger.info(f"Found {len(services)} services")
            
            for service in services:
                service_info = {
                    'uuid': str(service.uuid),
                    'uuid_common_name': self.get_common_service_name(str(service.uuid)),
                    'characteristics': []
                }
                
                logger.info(f"\n--- Service: {service.uuid} ({service_info['uuid_common_name']}) ---")
                
                try:
                    # Get characteristics for this service
                    characteristics = service.getCharacteristics()
                    logger.info(f"  Found {len(characteristics)} characteristics")
                    
                    for char in characteristics:
                        char_info = {
                            'uuid': str(char.uuid),
                            'uuid_common_name': self.get_common_char_name(str(char.uuid)),
                            'handle': char.getHandle(),
                            'properties': char.propertiesToString(),
                            'value_handle': char.valHandle if hasattr(char, 'valHandle') else None
                        }
                        
                        # Add to appropriate lists
                        result['all_characteristics'].append(char_info)
                        service_info['characteristics'].append(char_info)
                        
                        if 'WRITE' in char_info['properties']:
                            result['writable_characteristics'].append(char_info)
                        if 'READ' in char_info['properties'].upper():
                            result['readable_characteristics'].append(char_info)
                        if 'NOTIFY' in char_info['properties']:
                            result['notify_characteristics'].append(char_info)
                        
                        logger.info(f"    Char: {char.uuid} ({char_info['uuid_common_name']})")
                        logger.info(f"          Handle: {char.getHandle()}, Properties: {char.propertiesToString()}")
                        
                        # Try to read value if readable
                        if 'READ' in char_info['properties'].upper():
                            try:
                                value = char.read()
                                hex_value = binascii.hexlify(value).decode('utf-8')
                                char_info['current_value'] = hex_value
                                logger.info(f"          Current value: {hex_value}")
                            except Exception as e:
                                logger.debug(f"          Could not read value: {e}")
                        
                except Exception as e:
                    logger.warning(f"  Error reading characteristics for service {service.uuid}: {e}")
                
                result['services'].append(service_info)
            
            # Summary
            logger.info(f"\n=== Discovery Summary ===")
            logger.info(f"Total characteristics: {len(result['all_characteristics'])}")
            logger.info(f"Writable characteristics: {len(result['writable_characteristics'])}")
            logger.info(f"Readable characteristics: {len(result['readable_characteristics'])}")
            logger.info(f"Notify characteristics: {len(result['notify_characteristics'])}")
            
            # Look for potential BMS characteristics
            potential_bms_chars = []
            for char in result['writable_characteristics']:
                # Common BMS characteristic handles or UUIDs
                if (char['handle'] in [0x15, 0x13, 0x11] or 
                    'fff1' in char['uuid'].lower() or 
                    'fff2' in char['uuid'].lower()):
                    potential_bms_chars.append(char)
            
            if potential_bms_chars:
                logger.info(f"\n=== Potential BMS Characteristics ===")
                for char in potential_bms_chars:
                    logger.info(f"Handle {char['handle']}: {char['uuid']} - {char['properties']}")
            else:
                logger.warning("No obvious BMS characteristics found")
                
        except BTLEException as e:
            logger.error(f"Bluetooth error: {e}")
            result['error'] = f"Bluetooth error: {e}"
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            result['error'] = f"Discovery error: {e}"
        finally:
            if peripheral:
                try:
                    peripheral.disconnect()
                    logger.info("Disconnected")
                except:
                    pass
        
        return result
    
    def test_bms_communication(self, mac_address: str, char_handle: int) -> Dict[str, Any]:
        """Test BMS communication on a specific characteristic handle"""
        logger.info(f"Testing BMS communication on handle {char_handle} for {mac_address}")
        
        result = {
            'mac_address': mac_address,
            'handle': char_handle,
            'commands_sent': [],
            'responses_received': [],
            'success': False,
            'error': None
        }
        
        peripheral = None
        
        try:
            # Connect
            peripheral = Peripheral(mac_address, addrType="public")
            
            # Set up notification delegate
            class TestDelegate(DefaultDelegate):
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
                    logger.info(f"Response on handle {cHandle}: {hex_data}")
            
            delegate = TestDelegate()
            peripheral.setDelegate(delegate)
            
            # BMS command sequences to try
            bms_commands = [
                {
                    'name': 'Basic Info Request (0x03)',
                    'data': b'\xdd\xa5\x03\x00\xff\xfd\x77'
                },
                {
                    'name': 'Cell Voltages Request (0x04)', 
                    'data': b'\xdd\xa5\x04\x00\xff\xfc\x77'
                },
                {
                    'name': 'Hardware Version (0x05)',
                    'data': b'\xdd\xa5\x05\x00\xff\xfb\x77'
                }
            ]
            
            for cmd in bms_commands:
                try:
                    logger.info(f"Sending: {cmd['name']}")
                    peripheral.writeCharacteristic(char_handle, cmd['data'], False)
                    result['commands_sent'].append(cmd['name'])
                    
                    # Wait for response
                    if peripheral.waitForNotifications(3):
                        logger.info(f"✓ Response received for {cmd['name']}")
                        result['success'] = True
                    else:
                        logger.warning(f"No response for {cmd['name']}")
                    
                    time.sleep(1)  # Brief pause between commands
                    
                except Exception as e:
                    logger.error(f"Error sending {cmd['name']}: {e}")
            
            result['responses_received'] = delegate.responses
            
        except Exception as e:
            logger.error(f"Communication test error: {e}")
            result['error'] = str(e)
        finally:
            if peripheral:
                try:
                    peripheral.disconnect()
                except:
                    pass
        
        return result
    
    def get_common_service_name(self, uuid: str) -> str:
        """Get common name for service UUID"""
        common_services = {
            '1800': 'Generic Access',
            '1801': 'Generic Attribute', 
            '180f': 'Battery Service',
            '180a': 'Device Information',
            'fff0': 'Custom Service (Common BMS)',
            'ffe0': 'Custom Service (Common BLE)',
        }
        
        uuid_short = uuid.lower().replace('-', '')[:4]
        return common_services.get(uuid_short, 'Unknown')
    
    def get_common_char_name(self, uuid: str) -> str:
        """Get common name for characteristic UUID"""
        common_chars = {
            '2a00': 'Device Name',
            '2a01': 'Appearance',
            '2a04': 'Peripheral Preferred Connection Parameters',
            '2a05': 'Service Changed',
            '2a19': 'Battery Level',
            '2a29': 'Manufacturer Name',
            '2a24': 'Model Number',
            '2a25': 'Serial Number',
            '2a27': 'Hardware Revision',
            '2a26': 'Firmware Revision',
            'fff1': 'Custom Characteristic 1 (Possible BMS)',
            'fff2': 'Custom Characteristic 2 (Possible BMS)',
            'fff3': 'Custom Characteristic 3 (Possible BMS)',
            'fff4': 'Custom Characteristic 4 (Possible BMS)',
            'ffe1': 'Custom Characteristic (Common BLE)',
        }
        
        uuid_short = uuid.lower().replace('-', '')[:4]
        return common_chars.get(uuid_short, 'Unknown')

def main():
    """Main diagnostic function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced BMS BLE diagnostic tool')
    parser.add_argument('mac', help='MAC address to diagnose')
    parser.add_argument('--test-handle', type=int, help='Test BMS communication on specific handle')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    debugger = DetailedBMSDebugger()
    
    # Run deep discovery
    logger.info(f"=== Enhanced BMS Diagnostic for {args.mac} ===")
    discovery_result = debugger.deep_service_discovery(args.mac)
    
    if not discovery_result['connected']:
        print(f"❌ Failed to connect to {args.mac}")
        if discovery_result['error']:
            print(f"Error: {discovery_result['error']}")
        return
    
    print(f"\n✅ Successfully connected to {args.mac}")
    print(f"Found {len(discovery_result['services'])} services")
    print(f"Found {len(discovery_result['writable_characteristics'])} writable characteristics")
    
    # Test communication if handle specified
    if args.test_handle:
        logger.info(f"\n=== Testing BMS Communication on Handle {args.test_handle} ===")
        comm_result = debugger.test_bms_communication(args.mac, args.test_handle)
        
        print(f"Commands sent: {len(comm_result['commands_sent'])}")
        print(f"Responses received: {len(comm_result['responses_received'])}")
        print(f"Communication success: {comm_result['success']}")
        
        if comm_result['responses_received']:
            print("\nResponses:")
            for resp in comm_result['responses_received']:
                print(f"  Handle {resp['handle']}: {resp['data']}")
    
    # Suggest next steps
    print(f"\n=== Recommendations ===")
    if discovery_result['writable_characteristics']:
        print("Try testing BMS communication with these writable characteristics:")
        for char in discovery_result['writable_characteristics'][:3]:  # Show top 3
            print(f"  python bms_debug.py {args.mac} --test-handle {char['handle']}")
    else:
        print("No writable characteristics found - this may not be a BMS device")

if __name__ == "__main__":
    main()
