#!/usr/bin/env python3
"""
Parse BMS Data Response
Analyze the received BMS data to understand its structure
"""

import struct
import binascii

def parse_bms_response(hex_data: str):
    """Parse BMS response data"""
    
    print(f"=== BMS Data Analysis ===")
    print(f"Raw hex data: {hex_data}")
    print(f"Data length: {len(hex_data)} characters ({len(hex_data)//2} bytes)")
    
    # Convert hex string to bytes
    try:
        data = binascii.unhexlify(hex_data)
        print(f"Byte data: {data}")
        print(f"Byte length: {len(data)}")
        
        # Analyze header
        if len(data) >= 4:
            header = data[:4]
            print(f"\nHeader analysis:")
            print(f"  Bytes 0-3: {binascii.hexlify(header).decode('utf-8')}")
            
            # Check for common BMS patterns
            if data[0] == 0xdd and data[1] == 0x03:
                print(f"  -> BMS Pack Info Response (0x03)")
                parse_pack_info(data)
            elif data[0] == 0xdd and data[1] == 0x04:
                print(f"  -> BMS Cell Voltage Response (0x04)")
                parse_cell_voltages(data)
            else:
                print(f"  -> Unknown response type")
                parse_generic(data)
        
    except Exception as e:
        print(f"Error parsing data: {e}")

def parse_pack_info(data):
    """Parse pack info response (0x03)"""
    print(f"\n=== Pack Info Parsing ===")
    
    if len(data) < 20:
        print(f"Data too short for pack info")
        return
    
    try:
        # Skip header (4 bytes), parse pack data
        i = 4
        volts, amps, remain, capacity, cycles, mdate, balance1, balance2 = struct.unpack_from('>HhHHHHHH', data, i)
        
        print(f"Pack voltage: {volts / 100.0:.2f}V")
        print(f"Pack current: {amps / 100.0:.2f}A")
        print(f"Remaining capacity: {remain / 100.0:.2f}Ah")
        print(f"Total capacity: {capacity / 100.0:.2f}Ah")
        print(f"Charge level: {(remain / capacity * 100) if capacity > 0 else 0:.1f}%")
        print(f"Cycle count: {cycles}")
        print(f"Manufacture date: {mdate}")
        print(f"Balance status 1: 0x{balance1:04x}")
        print(f"Balance status 2: 0x{balance2:04x}")
        
    except Exception as e:
        print(f"Error parsing pack info: {e}")

def parse_cell_voltages(data):
    """Parse cell voltage response (0x04)"""
    print(f"\n=== Cell Voltage Parsing ===")
    
    if len(data) < 20:
        print(f"Data too short for cell voltages")
        return
    
    try:
        # Skip header (4 bytes), parse cell voltages
        i = 4
        cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8 = struct.unpack_from('>HHHHHHHH', data, i)
        
        cells = [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8]
        
        print(f"Cell voltages:")
        for i, cell_mv in enumerate(cells):
            if cell_mv > 0:  # Only show active cells
                cell_v = cell_mv / 1000.0
                print(f"  Cell {i+1}: {cell_v:.3f}V ({cell_mv}mV)")
        
        # Calculate pack voltage from cells
        active_cells = [c for c in cells if c > 0]
        if active_cells:
            total_mv = sum(active_cells)
            print(f"Total pack voltage (from cells): {total_mv / 1000.0:.3f}V")
            print(f"Average cell voltage: {(total_mv / len(active_cells)) / 1000.0:.3f}V")
            print(f"Active cell count: {len(active_cells)}")
        
    except Exception as e:
        print(f"Error parsing cell voltages: {e}")

def parse_generic(data):
    """Generic parsing for unknown data"""
    print(f"\n=== Generic Data Parsing ===")
    
    # Show bytes in different formats
    print(f"Hex bytes: {' '.join(f'{b:02x}' for b in data)}")
    print(f"Decimal bytes: {' '.join(str(b) for b in data)}")
    
    # Try to find voltage-like values (16-bit big endian)
    print(f"\n16-bit values (big endian):")
    for i in range(0, len(data)-1, 2):
        if i + 1 < len(data):
            value = struct.unpack('>H', data[i:i+2])[0]
            voltage = value / 1000.0
            print(f"  Bytes {i}-{i+1}: {value} (as voltage: {voltage:.3f}V)")

def main():
    # Parse the received BMS data
    received_data = "dd03001d053500001a25215300072b0f00000000"
    parse_bms_response(received_data)
    
    print(f"\n" + "="*50)
    print(f"CONCLUSION:")
    print(f"The BMS is responding with pack info data on handle 17.")
    print(f"This suggests the device uses a different notification handle")
    print(f"than expected, but the data format appears to be standard.")

if __name__ == "__main__":
    main()
