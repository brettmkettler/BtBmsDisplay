#!/usr/bin/env python3
"""
Overkill Solar BMS Reader
Connects to Overkill Solar BMS units via Bluetooth BLE and extracts battery data.
Optimized for Raspberry Pi 5.
"""

import asyncio
import struct
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import bleak
from bleak import BleakClient, BleakScanner

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

class OverkillBMSReader:
    """Overkill Solar BMS Bluetooth reader"""
    
    # Overkill Solar BMS Protocol Constants
    BMS_SERVICE_UUID = "0000ff00-0000-1000-8000-00805f9b34fb"
    BMS_CHARACTERISTIC_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"
    BMS_READ_COMMAND = bytes([0xDD, 0xA5, 0x03, 0x00, 0xFF, 0xFD, 0x77])
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.left_mac = config.get('left_track_mac', 'A4:C1:38:7C:2D:F0')
        self.right_mac = config.get('right_track_mac', 'E0:9F:2A:E4:94:1D')
        self.scan_timeout = config.get('scan_timeout', 30)
        self.connection_timeout = config.get('connection_timeout', 15)
        
        self.clients: Dict[str, BleakClient] = {}
        self.last_data: Dict[str, List[BatteryData]] = {'left': [], 'right': []}
        self.connection_status: Dict[str, BMSStatus] = {
            'left': BMSStatus(False, self.left_mac, 'left'),
            'right': BMSStatus(False, self.right_mac, 'right')
        }
    
    async def scan_for_devices(self) -> Dict[str, str]:
        """Scan for BMS devices and return found MAC addresses"""
        logger.info("Scanning for BMS devices...")
        found_devices = {}
        
        try:
            devices = await BleakScanner.discover(timeout=self.scan_timeout)
            
            for device in devices:
                mac = device.address.lower()
                name = device.name or "Unknown"
                
                logger.debug(f"Found device: {mac} ({name}) RSSI: {device.rssi}dBm")
                
                if mac == self.left_mac.lower():
                    found_devices['left'] = device.address
                    logger.info(f"Found LEFT track BMS: {mac} RSSI: {device.rssi}dBm")
                elif mac == self.right_mac.lower():
                    found_devices['right'] = device.address
                    logger.info(f"Found RIGHT track BMS: {mac} RSSI: {device.rssi}dBm")
                    
        except Exception as e:
            logger.error(f"Error during BLE scan: {e}")
        
        logger.info(f"Scan complete. Found {len(found_devices)} BMS devices")
        return found_devices
    
    async def connect_to_device(self, mac_address: str, track: str) -> Optional[BleakClient]:
        """Connect to a specific BMS device"""
        try:
            logger.info(f"Connecting to {track} track BMS: {mac_address}")
            
            client = BleakClient(mac_address, timeout=self.connection_timeout)
            await client.connect()
            
            if client.is_connected:
                logger.info(f"✓ Connected to {track} track BMS")
                self.clients[track] = client
                self.connection_status[track].connected = True
                self.connection_status[track].last_update = datetime.now().isoformat()
                self.connection_status[track].error_message = None
                return client
            else:
                raise Exception("Failed to establish connection")
                
        except Exception as e:
            logger.error(f"Failed to connect to {track} track BMS: {e}")
            self.connection_status[track].connected = False
            self.connection_status[track].error_message = str(e)
            return None
    
    def parse_bms_data(self, data: bytes, track: str) -> List[BatteryData]:
        """Parse BMS response data into battery information"""
        try:
            if len(data) < 34:
                logger.warning(f"Insufficient data received from {track} track: {len(data)} bytes")
                return []
            
            # Parse BMS data according to Overkill Solar protocol
            # This is a simplified parser - adjust based on actual protocol
            
            batteries = []
            
            # Extract basic info (adjust offsets based on actual protocol)
            pack_voltage = struct.unpack('>H', data[4:6])[0] / 100.0  # Pack voltage in V
            pack_current = struct.unpack('>h', data[6:8])[0] / 100.0  # Pack current in A
            remaining_capacity = struct.unpack('>H', data[8:10])[0] / 100.0  # Remaining capacity
            nominal_capacity = struct.unpack('>H', data[10:12])[0] / 100.0  # Nominal capacity
            
            # Calculate charge level
            charge_level = (remaining_capacity / nominal_capacity * 100) if nominal_capacity > 0 else 0
            
            # Temperature (if available)
            temp1 = struct.unpack('>H', data[12:14])[0] / 10.0 - 273.15 if len(data) >= 14 else None
            
            # For now, create 4 batteries per track (adjust based on actual setup)
            cell_voltages_start = 14
            for i in range(4):
                if cell_voltages_start + (i * 2) + 1 < len(data):
                    cell_voltage = struct.unpack('>H', data[cell_voltages_start + (i * 2):cell_voltages_start + (i * 2) + 2])[0] / 1000.0
                else:
                    cell_voltage = pack_voltage / 4  # Fallback estimate
                
                battery = BatteryData(
                    batteryNumber=i + 1 + (4 if track == 'right' else 0),
                    voltage=cell_voltage,
                    amperage=pack_current / 4,  # Distribute current across cells
                    chargeLevel=charge_level,
                    temperature=temp1,
                    status='normal' if 3.0 <= cell_voltage <= 4.2 else 'warning',
                    track=track,
                    trackPosition=i + 1
                )
                batteries.append(battery)
            
            logger.debug(f"Parsed {len(batteries)} batteries from {track} track")
            return batteries
            
        except Exception as e:
            logger.error(f"Error parsing BMS data from {track} track: {e}")
            return []
    
    async def read_bms_data(self, track: str) -> List[BatteryData]:
        """Read data from a connected BMS device"""
        client = self.clients.get(track)
        if not client or not client.is_connected:
            logger.warning(f"{track} track BMS not connected")
            return []
        
        try:
            # Send read command to BMS
            await client.write_gatt_char(self.BMS_CHARACTERISTIC_UUID, self.BMS_READ_COMMAND)
            
            # Wait a bit for response
            await asyncio.sleep(0.1)
            
            # Read response
            response = await client.read_gatt_char(self.BMS_CHARACTERISTIC_UUID)
            
            # Parse the data
            batteries = self.parse_bms_data(response, track)
            
            if batteries:
                self.last_data[track] = batteries
                self.connection_status[track].last_update = datetime.now().isoformat()
                logger.debug(f"Successfully read data from {track} track BMS")
            
            return batteries
            
        except Exception as e:
            logger.error(f"Error reading from {track} track BMS: {e}")
            self.connection_status[track].error_message = str(e)
            return []
    
    async def read_all_bms_data(self) -> Dict[str, List[BatteryData]]:
        """Read data from all connected BMS devices"""
        tasks = []
        
        for track in ['left', 'right']:
            if self.clients.get(track) and self.clients[track].is_connected:
                tasks.append(self.read_bms_data(track))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Process results as needed
        
        return self.last_data
    
    async def disconnect_all(self):
        """Disconnect from all BMS devices"""
        for track, client in self.clients.items():
            if client and client.is_connected:
                try:
                    await client.disconnect()
                    logger.info(f"Disconnected from {track} track BMS")
                except Exception as e:
                    logger.error(f"Error disconnecting from {track} track: {e}")
                finally:
                    self.connection_status[track].connected = False
        
        self.clients.clear()
    
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
        'scan_timeout': 30,
        'connection_timeout': 15
    }
    
    reader = OverkillBMSReader(config)
    
    try:
        # Scan for devices
        found_devices = await reader.scan_for_devices()
        
        # Connect to found devices
        for track, mac in found_devices.items():
            await reader.connect_to_device(mac, track)
        
        # Read data a few times
        for i in range(3):
            logger.info(f"Reading BMS data (attempt {i+1})")
            data = await reader.read_all_bms_data()
            
            print(f"\n--- Battery Data ---")
            print(json.dumps(reader.get_all_batteries(), indent=2))
            
            print(f"\n--- Connection Status ---")
            print(json.dumps(reader.get_connection_status(), indent=2))
            
            await asyncio.sleep(2)
    
    finally:
        await reader.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())
