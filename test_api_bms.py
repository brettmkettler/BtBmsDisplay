#!/usr/bin/env python3
"""
Test BMS Reader directly to verify it works like the detailed test
"""

import sys
import time
from bms_reader import OverkillBMSReader

def test_bms_reader():
    """Test the BMS reader directly"""
    
    print("=== Testing BMS Reader Directly (RIGHT TRACK ONLY) ===")
    
    # Create BMS reader with config - only RIGHT track
    config = {
        'left_track_mac': None,  # Disable LEFT track
        'right_track_mac': 'E0:9F:2A:E4:94:1D',
        'connection_timeout': 15,
        'poll_interval': 2
    }
    reader = OverkillBMSReader(config)
    
    # Connect to RIGHT device only
    print("Connecting to RIGHT track only...")
    
    # Manually connect just RIGHT track
    try:
        success = reader.connect_device('right')
        print(f"RIGHT track: {'✓ Connected' if success else '✗ Failed'}")
        
        if success:
            print("\nAttempting to read BMS data from RIGHT track...")
            read_success = reader.read_bms_data('right')
            
            if read_success:
                print("✓ RIGHT data read successfully")
                
                # Check if we have battery data
                batteries = reader.get_battery_data()
                right_batteries = [b for b in batteries if b.track == 'right']
                
                if right_batteries:
                    battery = right_batteries[0]
                    print(f"  Voltage: {battery.voltage}V")
                    print(f"  Current: {battery.current}A")
                    print(f"  SOC: {battery.soc}%")
                    print(f"  Cells: {battery.cell_voltages}")
                else:
                    print("  No battery data object created")
            else:
                print("✗ RIGHT data read failed")
                status = reader.get_connection_status()['right']
                print(f"  Error: {status.get('error_message', 'Unknown error')}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    # Cleanup
    reader.disconnect_all()
    print("\n✓ Disconnected all devices")

if __name__ == "__main__":
    test_bms_reader()
