#!/usr/bin/env python3
"""
Simple BMS Reader Import and Connection Test
Tests imports and basic connection without infinite loops
"""

import sys
import time

print("Testing BMS reader imports...")

try:
    from bms_reader import OverkillBMSReader
    print("✓ BMS reader import successful")
except Exception as e:
    print(f"✗ BMS reader import failed: {e}")
    sys.exit(1)

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
    print("✓ bluepy3 import successful")
except Exception as e:
    print(f"✗ bluepy3 import failed: {e}")
    sys.exit(1)

print("\nTesting BMS reader initialization...")

config = {
    'left_track_mac': 'A4:C1:38:7C:2D:F0',
    'right_track_mac': 'E0:9F:2A:E4:94:1D',
    'connection_timeout': 15,
    'poll_interval': 2
}

try:
    reader = OverkillBMSReader(config)
    print("✓ BMS reader initialization successful")
except Exception as e:
    print(f"✗ BMS reader initialization failed: {e}")
    sys.exit(1)

print("\nTesting BMS connection (without infinite loop)...")

try:
    results = reader.connect_all_devices()
    print(f"Connection results: {results}")
    
    # Get status
    status = reader.get_connection_status()
    print(f"Connection status: {status}")
    
    # Try one read cycle without infinite loop
    if any(results.values()):
        print("\nTesting single read cycle...")
        for track in ['left', 'right']:
            if reader.connection_status[track].connected:
                success = reader.read_bms_data(track)
                print(f"{track} track read: {success}")
        
        # Check for any data
        batteries = reader.get_all_batteries()
        print(f"Battery data received: {len(batteries)} batteries")
        if batteries:
            for battery in batteries:
                print(f"  Battery {battery['batteryNumber']}: {battery['voltage']}V, {battery['chargeLevel']}%")
    
    print("\n✓ BMS test completed successfully")
    
except Exception as e:
    print(f"✗ BMS connection test failed: {e}")
    import traceback
    traceback.print_exc()

finally:
    try:
        reader.disconnect_all()
        print("✓ Disconnected from all devices")
    except:
        pass

print("\nTest complete.")
