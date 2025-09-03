#!/usr/bin/env python3
"""
BMS Connection Test Script
Tests Bluetooth BLE connection to Overkill Solar BMS devices using bluepy3.btle.
Provides detailed diagnostics and connection verification.
"""

import sys
import time
import logging
import binascii
import struct
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException, Scanner
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BMSTestDelegate(DefaultDelegate):
    """Test delegate for BMS notifications"""
    
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.notifications_received = 0
        self.last_data = None
        
    def handleNotification(self, cHandle, data):
        self.notifications_received += 1
        self.last_data = data
        hex_data = binascii.hexlify(data).decode('utf-8')
        logger.info(f"Notification #{self.notifications_received} on handle {cHandle}: {hex_data}")
        
        # Try to parse common BMS data patterns
        if 'dd04' in hex_data:
            logger.info("  -> Cell voltage data detected")
        elif 'dd03' in hex_data:
            logger.info("  -> Pack info data detected")
        elif '77' in hex_data:
            logger.info("  -> Status data detected")

class BMSConnectionTester:
    """BMS connection testing utility"""
    
    def __init__(self):
        self.test_results = {}
        
    def scan_for_devices(self, timeout: int = 10) -> Dict[str, Any]:
        """Scan for BLE devices"""
        logger.info(f"Scanning for BLE devices (timeout: {timeout}s)...")
        
        try:
            scanner = Scanner()
            devices = scanner.scan(timeout)
            
            found_devices = []
            for device in devices:
                device_info = {
                    'address': device.addr,
                    'rssi': device.rssi,
                    'connectable': device.connectable,
                    'name': None
                }
                
                # Get device name if available
                for (adtype, desc, value) in device.getScanData():
                    if desc == "Complete Local Name" or desc == "Shortened Local Name":
                        device_info['name'] = value
                        break
                
                found_devices.append(device_info)
                logger.info(f"Found device: {device.addr} (RSSI: {device.rssi}dBm, Name: {device_info['name']})")
            
            return {
                'success': True,
                'devices': found_devices,
                'count': len(found_devices)
            }
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'devices': [],
                'count': 0
            }
    
    def test_connection(self, mac_address: str, timeout: int = 15) -> Dict[str, Any]:
        """Test connection to a specific BMS device"""
        logger.info(f"Testing connection to {mac_address}...")
        
        result = {
            'mac_address': mac_address,
            'connected': False,
            'services_discovered': False,
            'characteristics_found': [],
            'notifications_received': 0,
            'data_received': False,
            'error': None,
            'connection_time': None
        }
        
        peripheral = None
        start_time = time.time()
        
        try:
            # Attempt connection
            logger.info(f"Connecting to {mac_address}...")
            peripheral = Peripheral(mac_address, addrType="public")
            result['connected'] = True
            result['connection_time'] = round(time.time() - start_time, 2)
            logger.info(f"✓ Connected successfully in {result['connection_time']}s")
            
            # Set up delegate
            delegate = BMSTestDelegate()
            peripheral.setDelegate(delegate)
            
            # Discover services
            logger.info("Discovering services...")
            services = peripheral.getServices()
            result['services_discovered'] = True
            logger.info(f"✓ Found {len(services)} services")
            
            # Find characteristics
            for service in services:
                logger.info(f"Service: {service.uuid}")
                try:
                    characteristics = service.getCharacteristics()
                    for char in characteristics:
                        char_info = {
                            'uuid': str(char.uuid),
                            'handle': char.getHandle(),
                            'properties': char.propertiesToString()
                        }
                        result['characteristics_found'].append(char_info)
                        logger.info(f"  Characteristic: {char.uuid} (Handle: {char.getHandle()}) - {char.propertiesToString()}")
                except Exception as e:
                    logger.warning(f"Error reading characteristics for service {service.uuid}: {e}")
            
            # Test BMS communication if we found the right characteristic
            bms_char_handle = None
            for char in result['characteristics_found']:
                # Look for writable characteristic (typically handle 0x15 for BMS)
                if 'WRITE' in char['properties']:
                    bms_char_handle = char['handle']
                    break
            
            if bms_char_handle:
                logger.info(f"Testing BMS communication on handle {bms_char_handle}...")
                
                # Try to request pack info (0x03 command)
                try:
                    peripheral.writeCharacteristic(bms_char_handle, b'\xdd\xa5\x03\x00\xff\xfd\x77', False)
                    logger.info("✓ Sent pack info request")
                    
                    # Wait for response
                    if peripheral.waitForNotifications(3):
                        result['notifications_received'] = delegate.notifications_received
                        result['data_received'] = delegate.last_data is not None
                        logger.info(f"✓ Received {delegate.notifications_received} notifications")
                    else:
                        logger.warning("No notifications received")
                        
                except Exception as e:
                    logger.error(f"Error sending BMS command: {e}")
                    result['error'] = f"BMS communication error: {e}"
            else:
                logger.warning("No writable characteristic found for BMS communication")
                result['error'] = "No suitable characteristic found"
            
        except BTLEException as e:
            logger.error(f"Bluetooth error: {e}")
            result['error'] = f"Bluetooth error: {e}"
        except Exception as e:
            logger.error(f"Connection error: {e}")
            result['error'] = f"Connection error: {e}"
        finally:
            if peripheral:
                try:
                    peripheral.disconnect()
                    logger.info("Disconnected")
                except:
                    pass
        
        return result
    
    def run_full_test(self, target_macs: Optional[list] = None) -> Dict[str, Any]:
        """Run complete BMS connection test"""
        logger.info("=== BMS Connection Test Started ===")
        
        # Default MAC addresses if none provided
        if not target_macs:
            target_macs = [
                'A4:C1:38:7C:2D:F0',  # Left track
                'E0:9F:2A:E4:94:1D'   # Right track
            ]
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'scan_results': {},
            'connection_tests': {},
            'summary': {}
        }
        
        # 1. Scan for devices
        logger.info("\n--- Step 1: Scanning for BLE devices ---")
        scan_results = self.scan_for_devices(timeout=10)
        test_results['scan_results'] = scan_results
        
        if scan_results['success']:
            logger.info(f"Scan completed: {scan_results['count']} devices found")
            
            # Check if target devices were found
            found_targets = []
            for device in scan_results['devices']:
                if device['address'].upper() in [mac.upper() for mac in target_macs]:
                    found_targets.append(device['address'])
            
            if found_targets:
                logger.info(f"✓ Target BMS devices found: {found_targets}")
            else:
                logger.warning(f"⚠ Target BMS devices not found in scan. Targets: {target_macs}")
        else:
            logger.error("Scan failed")
        
        # 2. Test connections to target devices
        logger.info("\n--- Step 2: Testing BMS connections ---")
        for i, mac in enumerate(target_macs):
            track_name = 'left' if i == 0 else 'right'
            logger.info(f"\nTesting {track_name} track BMS: {mac}")
            
            connection_result = self.test_connection(mac)
            test_results['connection_tests'][track_name] = connection_result
            
            if connection_result['connected']:
                logger.info(f"✓ {track_name} track: Connection successful")
                if connection_result['data_received']:
                    logger.info(f"✓ {track_name} track: BMS data received")
                else:
                    logger.warning(f"⚠ {track_name} track: Connected but no BMS data")
            else:
                logger.error(f"✗ {track_name} track: Connection failed - {connection_result['error']}")
        
        # 3. Generate summary
        logger.info("\n--- Test Summary ---")
        successful_connections = sum(1 for result in test_results['connection_tests'].values() if result['connected'])
        data_receiving = sum(1 for result in test_results['connection_tests'].values() if result['data_received'])
        
        test_results['summary'] = {
            'total_targets': len(target_macs),
            'successful_connections': successful_connections,
            'data_receiving': data_receiving,
            'all_connected': successful_connections == len(target_macs),
            'any_data': data_receiving > 0
        }
        
        logger.info(f"Connections: {successful_connections}/{len(target_macs)}")
        logger.info(f"Data receiving: {data_receiving}/{len(target_macs)}")
        
        if test_results['summary']['all_connected'] and test_results['summary']['any_data']:
            logger.info("🎉 All tests passed! BMS system is working correctly.")
        elif test_results['summary']['any_data']:
            logger.info("✅ Partial success: Some BMS devices are working.")
        else:
            logger.error("❌ Tests failed: No BMS data received.")
        
        logger.info("=== BMS Connection Test Completed ===")
        return test_results

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test BMS Bluetooth connection')
    parser.add_argument('--mac', action='append', help='MAC address to test (can be used multiple times)')
    parser.add_argument('--scan-only', action='store_true', help='Only scan for devices, don\'t test connections')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = BMSConnectionTester()
    
    if args.scan_only:
        # Just scan for devices
        results = tester.scan_for_devices(timeout=15)
        print(f"\nScan Results: {results['count']} devices found")
        for device in results['devices']:
            print(f"  {device['address']} - {device['name']} (RSSI: {device['rssi']}dBm)")
    else:
        # Run full test
        target_macs = args.mac if args.mac else None
        results = tester.run_full_test(target_macs)
        
        # Print detailed results
        print(f"\n=== Detailed Results ===")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Scan found {results['scan_results']['count']} devices")
        
        for track, result in results['connection_tests'].items():
            print(f"\n{track.upper()} Track ({result['mac_address']}):")
            print(f"  Connected: {result['connected']}")
            if result['connected']:
                print(f"  Connection time: {result['connection_time']}s")
                print(f"  Services discovered: {result['services_discovered']}")
                print(f"  Characteristics found: {len(result['characteristics_found'])}")
                print(f"  Notifications received: {result['notifications_received']}")
                print(f"  Data received: {result['data_received']}")
            if result['error']:
                print(f"  Error: {result['error']}")

if __name__ == "__main__":
    main()
