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
    from bluepy3.btle import Peripheral, DefaultDelegate, BTLEException
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
    full_capacity: float = 0.0
    soc: float = 0.0
    cycles: int = 0
    cell_voltages: list = None
    last_update: Optional[str] = None
    connection_status: str = "disconnected"

    def __post_init__(self):
        if self.cell_voltages is None:
            self.cell_voltages = []

class JBDBMSDelegate(DefaultDelegate):
    """Notification delegate for JBD BMS responses"""
    def __init__(self, track):
        DefaultDelegate.__init__(self)
        self.track = track
        self.battery_data = BatteryData(track=track)
        self.last_notification = None
        
    def handleNotification(self, cHandle, data):
        """Handle BMS notifications following working script pattern"""
        try:
            hex_data = binascii.hexlify(data)
            text_string = hex_data.decode('utf-8')
            
            if text_string.find('dd04') != -1:  # Cell voltages response
                self.parse_cell_voltages(data)
            elif text_string.find('dd03') != -1:  # Basic info response
                self.parse_basic_info(data)
            elif text_string.find('77') != -1 and (len(text_string) == 28 or len(text_string) == 36):
                self.parse_extended_info(data)
                
        except Exception as e:
            logger.error(f"Error handling notification for {self.track}: {e}")
    
    def parse_basic_info(self, data):
        """Parse basic pack info (0x03 response)"""
        try:
            print(f"Basic info data length: {len(data)} bytes")
            
            # Check minimum buffer size (need 20 bytes: 4 header + 16 data)
            if len(data) < 20:
                print(f"Buffer too small for basic info: {len(data)} bytes, need 20")
                return
                
            i = 4  # Skip header bytes 0-3
            volts, amps, remain, capacity, cycles, mdate, balance1, balance2 = struct.unpack_from('>HhHHHHHH', data, i)
            
            # Convert to proper units
            self.battery_data.voltage = volts / 100.0
            self.battery_data.current = amps / 100.0
            self.battery_data.remaining_capacity = remain / 100.0
            self.battery_data.full_capacity = capacity / 100.0
            self.battery_data.cycles = cycles
            self.battery_data.last_update = datetime.now().isoformat()
            
            print(f"✓ {self.track} Pack: {self.battery_data.voltage:.2f}V, {self.battery_data.current:.2f}A, {self.battery_data.remaining_capacity:.1f}Ah")
            
        except Exception as e:
            logger.error(f"Error parsing basic info for {self.track}: {e}")
            print(f"Raw data: {binascii.hexlify(data).decode('utf-8')}")
    
    def parse_cell_voltages(self, data):
        """Parse cell voltages (0x04 response)"""
        try:
            print(f"Cell voltage data length: {len(data)} bytes")
            
            # Check minimum buffer size
            if len(data) < 8:  # Need at least header + some data
                print(f"Buffer too small: {len(data)} bytes")
                return
            
            i = 4  # Skip header bytes 0-3
            available_bytes = len(data) - i
            
            # Calculate how many cells we can read (2 bytes per cell)
            max_cells = available_bytes // 2
            print(f"Can read {max_cells} cells from {available_bytes} available bytes")
            
            if max_cells == 0:
                print("No cell data available")
                return
            
            # Read available cells (up to 8)
            cells = []
            for cell_idx in range(min(max_cells, 8)):
                if i + 1 < len(data):
                    cell_value = struct.unpack_from('>H', data, i)[0]
                    cells.append(cell_value)
                    i += 2
                else:
                    break
            
            # Convert to volts and filter out zero cells
            self.battery_data.cell_voltages = [c / 1000.0 for c in cells if c > 0]
            self.battery_data.last_update = datetime.now().isoformat()
            
            print(f"✓ {self.track} Cells ({len(cells)}): {[f'{c:.3f}V' for c in self.battery_data.cell_voltages]}")
            
        except Exception as e:
            logger.error(f"Error parsing cell voltages for {self.track}: {e}")
            print(f"Raw data: {binascii.hexlify(data).decode('utf-8')}")
    
    def parse_extended_info(self, data):
        """Parse extended info (protection, SOC, etc.)"""
        try:
            i = 0
            protect, vers, percent, fet, cells, sensors, temp1, temp2, b77 = struct.unpack_from('>HBBBBBHHB', data, i)
            
            self.battery_data.soc = percent
            self.battery_data.last_update = datetime.now().isoformat()
            
            print(f"✓ {self.track} Extended: SOC {percent}%")
            
        except Exception as e:
            logger.error(f"Error parsing extended info for {self.track}: {e}")

class JBDBMSReader:
    """JBD BMS Reader using exact working script pattern"""
    
    def __init__(self, mac_address, track):
        self.mac_address = mac_address
        self.track = track
        self.peripheral = None
        self.delegate = None
        self.connected = False

    def connect(self):
        """Connect using exact pattern from working script"""
        try:
            print(f"Attempting to connect to {self.track}: {self.mac_address}")
            
            # First connection attempt
            try:
                self.peripheral = Peripheral(self.mac_address, addrType="public")
            except BTLEException:
                print(f"2nd try connect to {self.track}")
                time.sleep(2)
                self.peripheral = Peripheral(self.mac_address, addrType="public")
            
            print(f"✓ Connected to {self.track}: {self.mac_address}")
            
            # Setup delegate for notifications
            self.delegate = JBDBMSDelegate(self.track)
            self.peripheral.setDelegate(self.delegate)
            
            self.connected = True
            return True
            
        except BTLEException as e:
            print(f"✗ Cannot connect to {self.track}: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"✗ Connection error for {self.track}: {e}")
            self.connected = False
            return False

    def read_data(self):
        """Read BMS data using exact working script pattern"""
        if not self.connected or not self.peripheral:
            return False
        
        try:
            # Write to handle 0x15 for basic info (0x03)
            self.peripheral.writeCharacteristic(0x15, b'\xdd\xa5\x03\x00\xff\xfd\x77', False)
            self.peripheral.waitForNotifications(5)
            
            # Write to handle 0x15 for cell voltages (0x04)  
            self.peripheral.writeCharacteristic(0x15, b'\xdd\xa5\x04\x00\xff\xfc\x77', False)
            self.peripheral.waitForNotifications(5)
            
            return True
            
        except BTLEException as e:
            print(f"✗ {self.track} read error: {e}")
            self.connected = False
            return False
        except Exception as e:
            print(f"✗ {self.track} unexpected error: {e}")
            return False

    def get_battery_data(self):
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
            self.peripheral = None
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
        
        @self.app.route('/api/batteries', methods=['GET'])
        def get_batteries():
            """Get battery data in format expected by UI - left/right tracks with 4 cells each"""
            batteries = []
            
            # Generate left track batteries (positions 1-4)
            left_data = self.battery_data['left']
            for i in range(4):
                # If we have cell voltage data, use it, otherwise use pack voltage / 4
                if left_data.cell_voltages and len(left_data.cell_voltages) > i:
                    cell_voltage = left_data.cell_voltages[i]
                else:
                    cell_voltage = left_data.voltage / 4 if left_data.voltage > 0 else 3.2
                
                batteries.append({
                    'batteryNumber': i + 1,
                    'voltage': round(cell_voltage, 2),
                    'amperage': round(abs(left_data.current), 1),
                    'chargeLevel': round(left_data.soc, 0),
                    'temperature': 25,  # Default temperature
                    'status': 'normal' if left_data.connection_status == 'connected' else 'warning',
                    'track': 'left',
                    'trackPosition': i + 1
                })
            
            # Generate right track batteries (positions 1-4)
            right_data = self.battery_data['right']
            for i in range(4):
                # If we have cell voltage data, use it, otherwise use pack voltage / 4
                if right_data.cell_voltages and len(right_data.cell_voltages) > i:
                    cell_voltage = right_data.cell_voltages[i]
                else:
                    cell_voltage = right_data.voltage / 4 if right_data.voltage > 0 else 3.2
                
                batteries.append({
                    'batteryNumber': i + 5,  # 5-8 for right track
                    'voltage': round(cell_voltage, 2),
                    'amperage': round(abs(right_data.current), 1),
                    'chargeLevel': round(right_data.soc, 0),
                    'temperature': 25,  # Default temperature
                    'status': 'normal' if right_data.connection_status == 'connected' else 'warning',
                    'track': 'right',
                    'trackPosition': i + 1
                })
            
            return jsonify(batteries)
        
        @self.app.route('/api/bms/status', methods=['GET'])
        def get_bms_status():
            """Get BMS connection status in format expected by UI"""
            return jsonify({
                'connected': any(data.connection_status == 'connected' for data in self.battery_data.values()),
                'tracks': {
                    'left': self.battery_data['left'].connection_status == 'connected',
                    'right': self.battery_data['right'].connection_status == 'connected'
                },
                'devices': {
                    self.left_mac: {
                        'track': 'left',
                        'connected': self.battery_data['left'].connection_status == 'connected',
                        'lastData': self.battery_data['left'].last_update
                    },
                    self.right_mac: {
                        'track': 'right', 
                        'connected': self.battery_data['right'].connection_status == 'connected',
                        'lastData': self.battery_data['right'].last_update
                    }
                },
                'config': {
                    'leftTrackMac': self.left_mac,
                    'rightTrackMac': self.right_mac,
                    'pollInterval': self.poll_interval * 1000  # Convert to ms
                }
            })
        
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
                reader.read_data()
                data = reader.get_battery_data()
                if data:
                    self.battery_data[track] = data
                    print(f"✓ {track} data updated: {data.voltage:.2f}V, {data.soc:.1f}%")
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
    
    def run_api_server(self, host='0.0.0.0', port=8000):
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
