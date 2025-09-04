#!/usr/bin/env python3
"""
Dual BMS Service - Alternates between left and right track BMS units
Provides REST API for UI to consume battery data with timestamps
"""

import sys
import time
import json
import logging
import threading
from datetime import datetime
from typing import Optional, Dict
from flask import Flask, jsonify
from dataclasses import dataclass, asdict

try:
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException, ADDR_TYPE_PUBLIC
except ImportError:
    print("ERROR: bluepy3 not installed. Run: pip install bluepy3")
    sys.exit(1)

# Import our existing JBD BMS classes
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Copy the classes from jbd_bms_reader.py
import binascii
import struct

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
    cell_voltages: list = None
    last_update: Optional[str] = None
    connection_status: str = "disconnected"

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
            self.battery_data.connection_status = "connected"
            
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
    
    def __init__(self, mac_address, track):
        self.mac_address = mac_address
        self.track = track
        self.peripheral = None
        self.service = None
        self.characteristic = None
        self.connected = False
        
        # Correct JBD BMS UUIDs from reference implementation
        self.service_uuid = "0000ffe0-0000-1000-8000-00805f9b34fb"
        self.char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
        
        # Protocol constants
        self.MIN_CELL_V = 2.5   # LiFePO4 min voltage for 0%
        self.MAX_CELL_V = 3.65  # LiFePO4 max voltage for 100%

    def connect(self):
        """Connect to the BMS device"""
        try:
            print(f"Connecting to {self.track} track: {self.mac_address}")
            
            # Step 1: Connect to peripheral with proper address type
            self.peripheral = Peripheral(self.mac_address, addrType=ADDR_TYPE_PUBLIC)
            
            # Step 2: Wait a moment for connection to stabilize
            time.sleep(0.5)
            
            # Step 3: Get services and find the correct one
            services = self.peripheral.getServices()
            print(f"Available services for {self.track}: {[str(s.uuid) for s in services]}")
            
            # Try to find service by UUID (try both short and long form)
            service_found = False
            for service in services:
                service_uuid_str = str(service.uuid).lower()
                if "ffe0" in service_uuid_str:
                    self.service = service
                    service_found = True
                    print(f"✓ Found service: {service.uuid}")
                    break
            
            if not service_found:
                # Try direct UUID lookup
                try:
                    self.service = self.peripheral.getServiceByUUID(self.service_uuid)
                    service_found = True
                    print(f"✓ Found service by direct lookup: {self.service_uuid}")
                except:
                    pass
            
            if not service_found:
                raise Exception(f"Service with UUID containing 'ffe0' not found. Available: {[str(s.uuid) for s in services]}")
            
            # Step 4: Get characteristics
            characteristics = self.service.getCharacteristics()
            print(f"Available characteristics for {self.track}: {[str(c.uuid) for c in characteristics]}")
            
            # Find the correct characteristic
            char_found = False
            for char in characteristics:
                char_uuid_str = str(char.uuid).lower()
                if "ffe1" in char_uuid_str:
                    self.characteristic = char
                    char_found = True
                    print(f"✓ Found characteristic: {char.uuid}")
                    break
            
            if not char_found:
                # Try direct characteristic lookup
                try:
                    self.characteristic = self.service.getCharacteristics(self.char_uuid)[0]
                    char_found = True
                    print(f"✓ Found characteristic by direct lookup: {self.char_uuid}")
                except:
                    pass
            
            if not char_found:
                raise Exception(f"Characteristic with UUID containing 'ffe1' not found. Available: {[str(c.uuid) for c in characteristics]}")
            
            self.connected = True
            print(f"✓ {self.track} connected successfully")
            return True
            
        except Exception as e:
            print(f"✗ {self.track} connection failed: {e}")
            self.connected = False
            return False

    def _send_cmd(self, cmd):
        """Send command and read response"""
        if not self.connected or not self.characteristic:
            raise Exception("Not connected to BMS")
            
        try:
            # Send command
            self.characteristic.write(bytes(cmd))
            time.sleep(0.1)  # Wait for response
            
            # Read response
            response = bytearray(self.characteristic.read())
            return response
            
        except Exception as e:
            print(f"Command failed: {e}")
            raise

    def get_basic_info(self):
        """Get basic BMS information using correct JBD protocol"""
        try:
            # Correct JBD command for basic info
            cmd = [0xDD, 0xA5, 0x03, 0x00, 0xFF, 0xFD, 0x77]
            data = self._send_cmd(cmd)
            
            # Validate response format
            if len(data) < 4 or data[0] != 0xDD or data[1] != 0x00 or data[-1] != 0x77:
                raise ValueError("Invalid basic response format")
            
            pos = 3  # Skip header
            len_ = data[2]
            
            # Parse total voltage (2 bytes, /100 for volts)
            total_v = ((data[pos] << 8) | data[pos + 1]) / 100.0
            pos += 2
            
            # Parse current (2 bytes, signed, /100 for amps)
            curr_raw = (data[pos] << 8) | data[pos + 1]
            current = curr_raw / 100.0 if curr_raw < 0x8000 else -(0x10000 - curr_raw) / 100.0
            pos += 2
            
            # Parse remaining capacity (2 bytes, /100 for Ah)
            res_cap = ((data[pos] << 8) | data[pos + 1]) / 100.0
            pos += 2
            
            # Parse nominal capacity (2 bytes, /100 for Ah)
            nom_cap = ((data[pos] << 8) | data[pos + 1]) / 100.0
            pos += 2
            
            # Skip cycles, date, balance, protection, version (9 bytes total)
            pos += 2 + 2 + 2 + 2 + 1
            
            # Parse state of charge (1 byte, percentage)
            soc = data[pos] if pos < len(data) else 0
            
            return {
                'voltage': total_v,
                'current': current,
                'power': total_v * current,
                'soc': soc,
                'remaining_capacity': res_cap,
                'nominal_capacity': nom_cap,
                'cell_voltages': [],
                'cell_percentages': [],
                'min_cell_voltage': 0,
                'max_cell_voltage': 0,
                'avg_cell_voltage': 0,
                'cell_balance': 0,
                'num_cells': 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Failed to get basic info from {self.track}: {e}")
            return None

    def get_cell_voltages(self):
        """Get individual cell voltages using correct JBD protocol"""
        try:
            # Correct JBD command for cell voltages
            cmd = [0xDD, 0xA5, 0x04, 0x00, 0xFF, 0xFC, 0x77]
            data = self._send_cmd(cmd)
            
            # Validate response format
            if len(data) < 4 or data[0] != 0xDD or data[1] != 0x00 or data[-1] != 0x77:
                raise ValueError("Invalid cells response format")
            
            pos = 3
            len_ = data[2]
            num_cells = len_ // 2
            
            cells = []
            for i in range(num_cells):
                if pos + 1 < len(data):
                    # Parse cell voltage (2 bytes, /1000 for volts)
                    v = ((data[pos] << 8) | data[pos + 1]) / 1000.0
                    cells.append(v)
                    pos += 2
                else:
                    break
            
            return cells
            
        except Exception as e:
            print(f"Failed to get cell voltages from {self.track}: {e}")
            return []

    def get_all_data(self):
        """Get all BMS data"""
        if not self.connected:
            return None
            
        try:
            basic_info = self.get_basic_info()
            cell_voltages = self.get_cell_voltages()
            
            if basic_info is None:
                return None
                
            # Calculate cell statistics
            if cell_voltages:
                min_cell = min(cell_voltages)
                max_cell = max(cell_voltages)
                avg_cell = sum(cell_voltages) / len(cell_voltages)
                
                # Calculate cell balance (difference between min and max)
                cell_balance = max_cell - min_cell
                
                # Calculate individual cell percentages
                cell_percentages = []
                for voltage in cell_voltages:
                    if voltage <= self.MIN_CELL_V:
                        percentage = 0
                    elif voltage >= self.MAX_CELL_V:
                        percentage = 100
                    else:
                        percentage = ((voltage - self.MIN_CELL_V) / (self.MAX_CELL_V - self.MIN_CELL_V)) * 100
                    cell_percentages.append(round(percentage, 1))
            else:
                min_cell = max_cell = avg_cell = cell_balance = 0
                cell_percentages = []
            
            return {
                'name': self.track,
                'connected': True,
                'voltage': basic_info['voltage'],
                'current': basic_info['current'],
                'power': basic_info['power'],
                'soc': basic_info['soc'],
                'remaining_capacity': basic_info['remaining_capacity'],
                'nominal_capacity': basic_info['nominal_capacity'],
                'cell_voltages': cell_voltages,
                'cell_percentages': cell_percentages,
                'min_cell_voltage': min_cell,
                'max_cell_voltage': max_cell,
                'avg_cell_voltage': avg_cell,
                'cell_balance': cell_balance,
                'num_cells': len(cell_voltages),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Failed to get data from {self.track}: {e}")
            return None

    def reconnect(self):
        """Reconnect after disconnection"""
        try:
            self.peripheral = Peripheral(self.mac_address, addrType="public")
            self.service = self.peripheral.getServiceByUUID(self.service_uuid)
            characteristics = self.service.getCharacteristics(self.char_uuid)
            
            if not characteristics:
                raise Exception(f"Characteristic {self.char_uuid} not found")
                
            self.characteristic = characteristics[0]
            print(f"✓ {self.track} reconnected")
            return True
        except Exception as e:
            print(f"✗ {self.track} reconnection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from device"""
        if self.peripheral:
            try:
                self.peripheral.disconnect()
                print(f"✓ {self.track} disconnected")
            except:
                pass
        self.connected = False

class DualBMSService:
    """Service that alternates between left and right BMS units"""
    
    def __init__(self, left_mac: str, right_mac: str, poll_interval: int = 5):
        self.left_mac = left_mac
        self.right_mac = right_mac
        self.poll_interval = poll_interval
        
        # Data storage
        self.battery_data = {
            'left': BatteryData(track='left'),
            'right': BatteryData(track='right')
        }
        
        # Service control
        self.running = False
        self.thread = None
        
        # Flask app for API
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/api/battery/status', methods=['GET'])
        def get_battery_status():
            """Get current battery status for both tracks"""
            return jsonify({
                'left': asdict(self.battery_data['left']),
                'right': asdict(self.battery_data['right']),
                'service_status': 'running' if self.running else 'stopped',
                'last_poll': datetime.now().isoformat()
            })
        
        @self.app.route('/api/battery/left', methods=['GET'])
        def get_left_battery():
            """Get left track battery data"""
            return jsonify(asdict(self.battery_data['left']))
        
        @self.app.route('/api/battery/right', methods=['GET'])
        def get_right_battery():
            """Get right track battery data"""
            return jsonify(asdict(self.battery_data['right']))
    
    def poll_bms_data(self):
        """Main polling loop - alternates between left and right with longer delays"""
        logger.info("Starting BMS polling service...")
        
        while self.running:
            # Poll left track
            self.poll_single_bms(self.left_mac, 'left')
            
            if not self.running:
                break
                
            # Longer pause between tracks to let BMS recover
            time.sleep(10)
            
            # Poll right track
            self.poll_single_bms(self.right_mac, 'right')
            
            if not self.running:
                break
                
            # Wait for next cycle - much longer to prevent device lockup
            time.sleep(self.poll_interval + 15)
    
    def poll_single_bms(self, mac_address: str, track: str):
        """Poll a single BMS unit"""
        reader = JBDBMSReader(mac_address, track)
        
        try:
            if reader.connect():
                data = reader.get_all_data()
                if data:
                    self.battery_data[track] = BatteryData(track=track, 
                                                           voltage=data['voltage'], 
                                                           current=data['current'], 
                                                           remaining_capacity=data['remaining_capacity'], 
                                                           total_capacity=data['nominal_capacity'], 
                                                           soc=data['soc'], 
                                                           cell_voltages=data['cell_voltages'], 
                                                           last_update=data['timestamp'], 
                                                           connection_status="connected")
                    print(f"✓ {track} data updated: {data['voltage']:.2f}V, {data['soc']:.1f}%")
                else:
                    print(f"⚠ {track} no data received")
                    self.battery_data[track].connection_status = "no_data"
            else:
                print(f"✗ {track} connection failed")
                self.battery_data[track].connection_status = "connection_failed"
                
        except Exception as e:
            print(f"✗ {track} polling error: {e}")
            self.battery_data[track].connection_status = "error"
        finally:
            reader.disconnect()
    
    def start_service(self):
        """Start the polling service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.poll_bms_data, daemon=True)
            self.thread.start()
            logger.info("BMS service started")
    
    def stop_service(self):
        """Stop the polling service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("BMS service stopped")
    
    def run_api_server(self, host='0.0.0.0', port=5000):
        """Run the Flask API server"""
        logger.info(f"Starting API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    # Configuration
    LEFT_TRACK_MAC = "A4:C1:38:7C:2D:F0"
    RIGHT_TRACK_MAC = "E0:9F:2A:E4:94:1D"
    POLL_INTERVAL = 5  # seconds
    
    # Create service
    service = DualBMSService(LEFT_TRACK_MAC, RIGHT_TRACK_MAC, POLL_INTERVAL)
    
    try:
        # Start polling service
        service.start_service()
        
        # Run API server (blocking)
        service.run_api_server(host='0.0.0.0', port=8000)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.stop_service()
