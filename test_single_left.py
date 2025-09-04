#!/usr/bin/env python3
"""
Test single LEFT BMS connection to isolate the issue
"""

import sys
import time
import logging
import binascii
import struct
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BatteryData:
    """Battery data structure"""
    track: str
    voltage: float = 0.0
    current: float = 0.0
    remaining_capacity: float = 0.0
    total_capacity: float = 0.0
    soc: float = 0.0
    cycles: int = 0
    cell_voltages: List[float] = None
    last_update: Optional[str] = None

    def __post_init__(self):
        if self.cell_voltages is None:
            self.cell_voltages = []

class JBDBMSDelegate(DefaultDelegate):
    """JBD BMS notification delegate with data parsing"""
    
    def __init__(self, track: str):
        DefaultDelegate.__init__(self)
        self.track = track
        self.responses = []
        self.battery_data = BatteryData(track=track)
        self.partial_message = b''
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data).decode('utf-8')
        self.responses.append({
            'handle': cHandle,
            'data': hex_data,
            'timestamp': datetime.now().isoformat()
        })
        print(f"BMS {self.track} RX: Handle {cHandle} = {hex_data}")
        
        # Skip handshake
        if hex_data == '00':
            return
            
        # Handle JBD split messages
        if hex_data.startswith('dd') and len(hex_data) < 40:
            # First part of split message
            self.partial_message = data
            print(f"BMS {self.track} PARTIAL: {hex_data}")
            return
            
        # Combine with partial if exists
        if self.partial_message:
            combined_data = self.partial_message + data
            combined_hex = binascii.hexlify(combined_data).decode('utf-8')
            print(f"BMS {self.track} COMBINED: {combined_hex}")
            self.process_bms_data(combined_data, combined_hex)
            self.partial_message = b''
        else:
            self.process_bms_data(data, hex_data)
    
    def process_bms_data(self, data, hex_string):
        """Process BMS data using parse_bms_data.py logic"""
        try:
            if hex_string.find('dd03') != -1:
                # Pack info
                self.parse_pack_info(data)
            elif hex_string.find('dd04') != -1:
                # Cell voltages
                self.parse_cell_voltages(data)
        except Exception as e:
            logger.error(f"Error processing BMS data for {self.track}: {e}")
    
    def parse_pack_info(self, data):
        """Parse pack info response (0x03) - from parse_bms_data.py"""
        if len(data) < 20:
            return
            
        try:
            # Skip header (4 bytes), parse pack data
            i = 4
            volts, amps, remain, capacity, cycles, mdate, balance1, balance2 = struct.unpack_from('>HhHHHHHH', data, i)
            
            self.battery_data.voltage = volts / 100.0
            self.battery_data.current = amps / 100.0
            self.battery_data.remaining_capacity = remain / 100.0
            self.battery_data.total_capacity = capacity / 100.0
            self.battery_data.soc = (remain / capacity * 100) if capacity > 0 else 0
            self.battery_data.cycles = cycles
            self.battery_data.last_update = datetime.now().isoformat()
            
            print(f"✓ {self.track} Pack: {self.battery_data.voltage:.2f}V, {self.battery_data.current:.2f}A, {self.battery_data.soc:.1f}%")
            
        except Exception as e:
            logger.error(f"Error parsing pack info for {self.track}: {e}")
    
    def parse_cell_voltages(self, data):
        """Parse cell voltage response (0x04) - from parse_bms_data.py"""
        if len(data) < 20:
            return
            
        try:
            # Skip header (4 bytes), parse cell voltages
            i = 4
            cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8 = struct.unpack_from('>HHHHHHHH', data, i)
            
            cells = [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8]
            # Convert to volts and filter out zero cells
            self.battery_data.cell_voltages = [c / 1000.0 for c in cells if c > 0]
            self.battery_data.last_update = datetime.now().isoformat()
            
            print(f"✓ {self.track} Cells: {[f'{c:.3f}V' for c in self.battery_data.cell_voltages]}")
            
        except Exception as e:
            logger.error(f"Error parsing cell voltages for {self.track}: {e}")

class JBDBMSReader:
    """JBD BMS Reader using working connection logic"""
    
    def __init__(self, mac_address: str, track: str):
        self.mac_address = mac_address
        self.track = track
        self.peripheral = None
        self.delegate = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect using working logic from original script"""
        try:
            print(f"Connecting to {self.track} track: {self.mac_address}")
            
            # Step 1: Connect
            self.peripheral = Peripheral(self.mac_address, addrType="public")
            
            # Step 2: Set delegate
            self.delegate = JBDBMSDelegate(self.track)
            self.peripheral.setDelegate(self.delegate)
            
            # Step 3: Enable notifications
            try:
                self.peripheral.writeCharacteristic(22, b'\x01\x00', False)
                print(f"✓ {self.track} notifications enabled on handle 22")
            except Exception as e:
                # Try other handles
                for handle in [23, 24, 25]:
                    try:
                        self.peripheral.writeCharacteristic(handle, b'\x01\x00', False)
                        print(f"✓ {self.track} notifications enabled on handle {handle}")
                        break
                    except:
                        continue
            
            self.connected = True
            print(f"✓ {self.track} connected successfully")
            return True
            
        except Exception as e:
            print(f"✗ {self.track} connection failed: {e}")
            return False
    
    def read_data(self) -> bool:
        """Read BMS data using sequential command approach"""
        if not self.connected or not self.peripheral:
            return False
        
        # JBD BMS commands from working script
        commands = [
            {
                'name': 'Basic Info (0x03)',
                'data': b'\xdd\xa5\x03\x00\xff\xfd\x77'
            },
            {
                'name': 'Cell Voltages (0x04)', 
                'data': b'\xdd\xa5\x04\x00\xff\xfc\x77'
            }
        ]
        
        for i, cmd in enumerate(commands):
            print(f"Sending {cmd['name']} to {self.track}...")
            
            try:
                # Send command
                self.peripheral.writeCharacteristic(21, cmd['data'], False)
                
                # Wait for response
                start_time = time.time()
                while time.time() - start_time < 3:
                    if self.peripheral.waitForNotifications(0.5):
                        print(f"✓ {self.track} response received")
                        break
                else:
                    print(f"⚠ {self.track} no response to {cmd['name']}")
                
                time.sleep(0.5)  # Brief pause between commands
                
            except BTLEException as e:
                if "disconnected" in str(e).lower() and i == 0:
                    # First command disconnected, reconnect for second
                    print(f"⚠ {self.track} disconnected on first command, reconnecting...")
                    if self.reconnect():
                        continue
                    else:
                        return False
                else:
                    print(f"✗ {self.track} error: {e}")
                    return False
        
        return True
    
    def reconnect(self) -> bool:
        """Reconnect after disconnection"""
        try:
            self.peripheral = Peripheral(self.mac_address, addrType="public")
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.writeCharacteristic(22, b'\x01\x00', False)
            print(f"✓ {self.track} reconnected")
            return True
        except Exception as e:
            print(f"✗ {self.track} reconnection failed: {e}")
            self.connected = False
            return False
    
    def get_battery_data(self) -> Optional[BatteryData]:
        """Get parsed battery data"""
        if self.delegate and self.delegate.battery_data.last_update:
            return self.delegate.battery_data
        return None
    
    def disconnect(self):
        """Disconnect from device"""
        if self.peripheral:
            try:
                self.peripheral.disconnect()
                print(f"✓ {self.track} disconnected")
            except:
                pass
        self.connected = False

def test_left_bms_repeatedly():
    """Test LEFT BMS multiple times with delays"""
    LEFT_MAC = "A4:C1:38:7C:2D:F0"
    
    for attempt in range(5):
        print(f"\n=== Attempt {attempt + 1}/5 ===")
        
        reader = JBDBMSReader(LEFT_MAC, 'left')
        
        try:
            if reader.connect():
                if reader.read_data():
                    battery = reader.get_battery_data()
                    if battery:
                        print(f"\n--- LEFT Battery Data ---")
                        print(f"Voltage: {battery.voltage:.2f}V")
                        print(f"Current: {battery.current:.2f}A")
                        print(f"SOC: {battery.soc:.1f}%")
                        print(f"Cells: {[f'{c:.3f}V' for c in battery.cell_voltages]}")
                    else:
                        print(f"✗ No battery data received")
                else:
                    print(f"✗ Data read failed")
            else:
                print(f"✗ Connection failed")
        
        finally:
            reader.disconnect()
        
        # Wait between attempts
        if attempt < 4:
            print(f"Waiting 15 seconds before next attempt...")
            time.sleep(15)

if __name__ == "__main__":
    test_left_bms_repeatedly()
