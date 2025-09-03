#!/usr/bin/env python3
"""
Overkill Solar BMS Reader
Connects to Overkill Solar BMS units via Bluetooth BLE using bluepy3.btle and extracts battery data.
Based on JBD BMS protocol implementation.
Optimized for Raspberry Pi 5.
"""

import asyncio
import struct
import json
import logging
import binascii
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BatteryData:
    """Battery data structure matching the UI schema"""
    batteryNumber: int
    voltage: float
    amperage: float
    chargeLevel: float
    temperature: Optional[float] = None
    status: str = 'normal'
    track: str = 'left'
    trackPosition: int = 1

@dataclass
class BMSStatus:
    """BMS connection status"""
    connected: bool
    mac_address: str
    track: str
    last_update: Optional[str] = None
    error_message: Optional[str] = None

class BMSDelegate(DefaultDelegate):
    """BLE notification delegate for BMS data"""
    
    def __init__(self, bms_reader, track):
        DefaultDelegate.__init__(self)
        self.bms_reader = bms_reader
        self.track = track
        self.cell_voltages = []
        self.pack_info = {}
        
    def handleNotification(self, cHandle, data):
        hex_data = binascii.hexlify(data)
        text_string = hex_data.decode('utf-8')
        
        try:
            if text_string.find('dd04') != -1:  # Cell voltages (1-8 cells)
                self.process_cell_voltages(data)
            elif text_string.find('dd03') != -1:  # Pack info
                self.process_pack_info(data)
            elif text_string.find('77') != -1 and (len(text_string) == 28 or len(text_string) == 36):
                self.process_pack_status(data)
        except Exception as e:
            logger.error(f"Error processing BMS notification for {self.track}: {e}")
    
    def process_cell_voltages(self, data):
        """Process cell voltage data"""
        try:
            i = 4  # Skip header bytes 0-3
            cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8 = struct.unpack_from('>HHHHHHHH', data, i)
            self.cell_voltages = [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8]
            
            logger.debug(f"{self.track} track cell voltages: {self.cell_voltages}")
            self.update_battery_data()
            
        except Exception as e:
            logger.error(f"Error processing cell voltages for {self.track}: {e}")
    
    def process_pack_info(self, data):
        """Process pack information data"""
        try:
            i = 4  # Skip header bytes 0-3
            volts, amps, remain, capacity, cycles, mdate, balance1, balance2 = struct.unpack_from('>HhHHHHHH', data, i)
            
            self.pack_info = {
                'volts': volts / 100.0,
                'amps': amps / 100.0,
                'capacity': capacity / 100.0,
                'remain': remain / 100.0,
                'cycles': cycles,
                'watts': (volts / 100.0) * (amps / 100.0),
                'charge_level': (remain / capacity * 100) if capacity > 0 else 0
            }
            
            logger.debug(f"{self.track} track pack info: {self.pack_info}")
            self.update_battery_data()
            
        except Exception as e:
            logger.error(f"Error processing pack info for {self.track}: {e}")
    
    def process_pack_status(self, data):
        """Process pack status data"""
        try:
            i = 0
            protect, vers, percent, fet, cells, sensors, temp1, temp2, b77 = struct.unpack_from('>HBBBBBHHB', data, i)
            
            temp1_c = (temp1 - 2731) / 10.0 if temp1 > 0 else None
            temp2_c = (temp2 - 2731) / 10.0 if temp2 > 0 else None
            
            self.pack_info.update({
                'protect': protect,
                'percent': percent,
                'fet': fet,
                'cells': cells,
                'temp1': temp1_c,
                'temp2': temp2_c
            })
            
            logger.debug(f"{self.track} track status: protect={protect}, percent={percent}, temp1={temp1_c}°C")
            self.update_battery_data()
            
        except Exception as e:
            logger.error(f"Error processing pack status for {self.track}: {e}")
    
    def update_battery_data(self):
        """Update battery data in the BMS reader"""
        if not self.cell_voltages or not self.pack_info:
            return
        
        try:
            batteries = []
            cell_count = min(len(self.cell_voltages), 4)  # Limit to 4 cells per track
            
            for i in range(cell_count):
                if self.cell_voltages[i] > 0:  # Only include active cells
                    battery_number = i + 1 + (4 if self.track == 'right' else 0)
                    cell_voltage = self.cell_voltages[i] / 1000.0  # Convert mV to V
                    
                    # Determine status based on cell voltage
                    if cell_voltage < 3.0:
                        status = 'critical'
                    elif cell_voltage < 3.2 or cell_voltage > 4.1:
                        status = 'warning'
                    else:
                        status = 'normal'
                    
                    battery = BatteryData(
                        batteryNumber=battery_number,
                        voltage=cell_voltage,
                        amperage=self.pack_info.get('amps', 0) / cell_count,
                        chargeLevel=self.pack_info.get('charge_level', 0),
                        temperature=self.pack_info.get('temp1'),
                        status=status,
                        track=self.track,
                        trackPosition=i + 1
                    )
                    batteries.append(battery)
            
            # Update the reader's data
            self.bms_reader.last_data[self.track] = batteries
            self.bms_reader.connection_status[self.track].last_update = datetime.now().isoformat()
            
            logger.debug(f"Updated {len(batteries)} batteries for {self.track} track")
            
        except Exception as e:
            logger.error(f"Error updating battery data for {self.track}: {e}")

class OverkillBMSReader:
    """Overkill Solar BMS Bluetooth reader using bluepy3.btle"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.left_mac = config.get('left_track_mac', 'A4:C1:38:7C:2D:F0')
        self.right_mac = config.get('right_track_mac', 'E0:9F:2A:E4:94:1D')
        self.connection_timeout = config.get('connection_timeout', 15)
        self.poll_interval = config.get('poll_interval', 2)
        
        self.peripherals: Dict[str, Peripheral] = {}
        self.delegates: Dict[str, BMSDelegate] = {}
        self.last_data: Dict[str, List[BatteryData]] = {'left': [], 'right': []}
        self.connection_status: Dict[str, BMSStatus] = {
            'left': BMSStatus(False, self.left_mac, 'left'),
            'right': BMSStatus(False, self.right_mac, 'right')
        }
        self.running = False
    
    def connect_to_device(self, mac_address: str, track: str) -> bool:
        """Connect to a specific BMS device"""
        try:
            logger.info(f"Connecting to {track} track BMS: {mac_address}")
            
            # Try to connect
            peripheral = Peripheral(mac_address, addrType="public")
            
            # Set up delegate for notifications
            delegate = BMSDelegate(self, track)
            peripheral.setDelegate(delegate)
            
            # Enable notifications on handle 22 (CCCD for handle 21)
            try:
                peripheral.writeCharacteristic(22, b'\x01\x00', False)
                logger.info(f"✓ Notifications enabled for {track} track")
            except Exception as e:
                logger.warning(f"Could not enable notifications for {track} track: {e}")
            
            # Store connections
            self.peripherals[track] = peripheral
            self.delegates[track] = delegate
            
            # Update status
            self.connection_status[track].connected = True
            self.connection_status[track].last_update = datetime.now().isoformat()
            self.connection_status[track].error_message = None
            
            logger.info(f"✓ Connected to {track} track BMS")
            return True
            
        except BTLEException as e:
            logger.error(f"Failed to connect to {track} track BMS: {e}")
            self.connection_status[track].connected = False
            self.connection_status[track].error_message = str(e)
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to {track} track BMS: {e}")
            self.connection_status[track].connected = False
            self.connection_status[track].error_message = str(e)
            return False
    
    def disconnect_device(self, track: str):
        """Disconnect from a BMS device"""
        try:
            if track in self.peripherals:
                self.peripherals[track].disconnect()
                del self.peripherals[track]
                del self.delegates[track]
                
            self.connection_status[track].connected = False
            logger.info(f"Disconnected from {track} track BMS")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {track} track: {e}")
    
    def read_bms_data(self, track: str) -> bool:
        """Read data from a connected BMS device"""
        if track not in self.peripherals:
            return False
        
        try:
            peripheral = self.peripherals[track]
            
            # Request cell voltages (0x04) - this works reliably
            peripheral.writeCharacteristic(21, b'\xdd\xa5\x04\x00\xff\xfc\x77', False)
            peripheral.waitForNotifications(3)
            
            return True
            
        except BTLEException as e:
            logger.error(f"BLE error reading from {track} track: {e}")
            self.connection_status[track].connected = False
            self.connection_status[track].error_message = str(e)
            return False
        except Exception as e:
            logger.error(f"Error reading from {track} track BMS: {e}")
            self.connection_status[track].error_message = str(e)
            return False
    
    def connect_all_devices(self) -> Dict[str, bool]:
        """Connect to all configured BMS devices"""
        results = {}
        
        # Try to connect to left track
        results['left'] = self.connect_to_device(self.left_mac, 'left')
        
        # Try to connect to right track
        results['right'] = self.connect_to_device(self.right_mac, 'right')
        
        return results
    
    def disconnect_all(self):
        """Disconnect from all BMS devices"""
        for track in ['left', 'right']:
            self.disconnect_device(track)
    
    def start_reading(self):
        """Start continuous BMS data reading"""
        self.running = True
        logger.info("Starting BMS data reading loop")
        
        while self.running:
            try:
                # Read from all connected devices
                for track in ['left', 'right']:
                    if self.connection_status[track].connected:
                        success = self.read_bms_data(track)
                        if not success:
                            # Try to reconnect on failure
                            logger.warning(f"Lost connection to {track} track, attempting reconnect...")
                            mac = self.left_mac if track == 'left' else self.right_mac
                            self.disconnect_device(track)
                            time.sleep(1)
                            self.connect_to_device(mac, track)
                
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping BMS reader...")
                break
            except Exception as e:
                logger.error(f"Error in reading loop: {e}")
                time.sleep(5)
        
        self.disconnect_all()
    
    def stop_reading(self):
        """Stop continuous BMS data reading"""
        self.running = False
    
    def get_all_batteries(self) -> List[Dict[str, Any]]:
        """Get all battery data as JSON-serializable format"""
        all_batteries = []
        for track_batteries in self.last_data.values():
            for battery in track_batteries:
                all_batteries.append(asdict(battery))
        return all_batteries
    
    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """Get connection status for all tracks"""
        return {
            track: asdict(status) 
            for track, status in self.connection_status.items()
        }

async def main():
    """Main function for testing the BMS reader"""
    config = {
        'left_track_mac': 'A4:C1:38:7C:2D:F0',
        'right_track_mac': 'E0:9F:2A:E4:94:1D',
        'connection_timeout': 15,
        'poll_interval': 2
    }
    
    reader = OverkillBMSReader(config)
    
    try:
        # Connect to devices
        results = reader.connect_all_devices()
        logger.info(f"Connection results: {results}")
        
        if any(results.values()):
            # Start reading data
            reader.start_reading()
        else:
            logger.error("Failed to connect to any BMS devices")
    
    finally:
        reader.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())
