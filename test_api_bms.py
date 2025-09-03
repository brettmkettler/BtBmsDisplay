#!/usr/bin/env python3
"""
Test BMS Reader directly to verify it works like the detailed test
"""

import sys
import time
from bms_reader import OverkillBMSReader

def test_bms_reader():
    """Test the BMS reader directly"""
    
    print("=== Testing BMS Reader Directly ===")
    
    # Create BMS reader
    reader = OverkillBMSReader()
    
    # Connect to devices
    print("Connecting to devices...")
    connections = reader.connect_all_devices()
    
    for track, connected in connections.items():
        status = "✓ Connected" if connected else "✗ Failed"
        print(f"{track.upper()} track: {status}")
    
    # Try reading data
    print("\nAttempting to read BMS data...")
    
    for track in ['left', 'right']:
        if connections.get(track, False):
            print(f"\nReading {track.upper()} track...")
            success = reader.read_bms_data(track)
            
            if success:
                print(f"✓ {track.upper()} data read successfully")
                
                # Check if we have battery data
                batteries = reader.get_battery_data()
                track_batteries = [b for b in batteries if b.track == track]
                
                if track_batteries:
                    battery = track_batteries[0]
                    print(f"  Voltage: {battery.voltage}V")
                    print(f"  Current: {battery.current}A")
                    print(f"  SOC: {battery.soc}%")
                    print(f"  Cells: {battery.cell_voltages}")
                else:
                    print(f"  No battery data object created")
            else:
                print(f"✗ {track.upper()} data read failed")
                status = reader.get_connection_status()[track]
                print(f"  Error: {status.error_message}")
    
    # Cleanup
    reader.disconnect_all_devices()
    print("\n✓ Disconnected all devices")

if __name__ == "__main__":
    test_bms_reader()
