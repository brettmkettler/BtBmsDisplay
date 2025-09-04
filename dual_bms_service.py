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
        """Read BMS data using proper JBD protocol - write requests to handles 0x03 and 0x04"""
        if not self.connected or not self.peripheral:
            return False
        
        # JBD BMS protocol: write requests to specific handles (not characteristics)
        commands = [
            {
                'name': 'Basic Info (0x03)',
                'handle': 0x03,
                'data': b'\xdd\xa5\x03\x00\xff\xfd\x77'
            },
            {
                'name': 'Cell Voltages (0x04)', 
                'handle': 0x04,
                'data': b'\xdd\xa5\x04\x00\xff\xfc\x77'
            }
        ]
        
        for i, cmd in enumerate(commands):
            print(f"Sending {cmd['name']} to {self.track} handle {cmd['handle']}...")
            
            try:
                # JBD protocol: write request to specific handle (not characteristic)
                self.peripheral.writeCharacteristic(cmd['handle'], cmd['data'], False)
                
                # Wait for notification response
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
                        # Retry the same command after reconnection
                        try:
                            self.peripheral.writeCharacteristic(cmd['handle'], cmd['data'], False)
                            start_time = time.time()
                            while time.time() - start_time < 3:
                                if self.peripheral.waitForNotifications(0.5):
                                    print(f"✓ {self.track} response received after reconnect")
                                    break
                        except:
                            pass
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
                if reader.read_data():
                    battery_data = reader.get_battery_data()
                    if battery_data:
                        self.battery_data[track] = battery_data
                        print(f"✓ {track} data updated: {battery_data.voltage:.2f}V, {battery_data.soc:.1f}%")
                    else:
                        print(f"⚠ {track} no data received")
                        self.battery_data[track].connection_status = "no_data"
                else:
                    print(f"✗ {track} data read failed")
                    self.battery_data[track].connection_status = "read_failed"
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
        service.run_api_server(host='0.0.0.0', port=5050)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.stop_service()
