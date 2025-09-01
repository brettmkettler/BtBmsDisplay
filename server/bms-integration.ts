// BMS Integration Module for Overkill Solar BMS via Bluetooth BLE
// Optimized for Raspberry Pi 5
import noble from '@abandonware/noble';
import { Buffer } from 'buffer';

export interface BatteryData {
  batteryNumber: number;
  voltage: number;
  amperage: number;
  chargeLevel: number;
  temperature?: number;
  status?: 'normal' | 'warning' | 'critical';
  track?: 'left' | 'right';
  trackPosition?: number;
}

export interface BMSConfig {
  leftTrackMac: string;
  rightTrackMac: string;
  pollInterval?: number;
  batteryCount?: number;
  connectionTimeout?: number;
  scanTimeout?: number;
  maxReconnectAttempts?: number;
}

interface BMSDevice {
  mac: string;
  track: 'left' | 'right';
  peripheral?: any;
  characteristic?: any;
  connected: boolean;
  lastData?: Date;
  reconnectAttempts: number;
}

export class BMSIntegration {
  private config: BMSConfig;
  private devices: Map<string, BMSDevice> = new Map();
  private isScanning: boolean = false;
  private pollTimer?: NodeJS.Timeout;
  private scanTimer?: NodeJS.Timeout;
  private isInitialized: boolean = false;

  // Overkill Solar BMS Protocol Constants
  private readonly BMS_SERVICE_UUID = 'ff00';
  private readonly BMS_CHARACTERISTIC_UUID = 'ff02';
  private readonly BMS_READ_COMMAND = Buffer.from([0xDD, 0xA5, 0x03, 0x00, 0xFF, 0xFD, 0x77]);

  constructor(config: BMSConfig) {
    this.config = {
      pollInterval: 2000,
      batteryCount: 4, // 4 batteries per track for dual-track system
      connectionTimeout: 15000, // Increased for RPi5
      scanTimeout: 30000,
      maxReconnectAttempts: 5,
      ...config
    };

    // Initialize device tracking
    this.devices.set(config.leftTrackMac.toLowerCase(), {
      mac: config.leftTrackMac.toLowerCase(),
      track: 'left',
      connected: false,
      reconnectAttempts: 0
    });

    this.devices.set(config.rightTrackMac.toLowerCase(), {
      mac: config.rightTrackMac.toLowerCase(),
      track: 'right',
      connected: false,
      reconnectAttempts: 0
    });
  }

  private async initializeNoble(): Promise<void> {
    if (this.isInitialized) return;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Bluetooth initialization timeout'));
      }, 10000);

      const onStateChange = (state: string) => {
        console.log(`Bluetooth state: ${state}`);
        
        if (state === 'poweredOn') {
          clearTimeout(timeout);
          noble.removeListener('stateChange', onStateChange);
          this.setupNobleEventHandlers();
          this.isInitialized = true;
          resolve();
        } else if (state === 'unsupported' || state === 'unauthorized') {
          clearTimeout(timeout);
          noble.removeListener('stateChange', onStateChange);
          reject(new Error(`Bluetooth ${state}`));
        }
      };

      noble.on('stateChange', onStateChange);

      // Check if already powered on
      if (noble.state === 'poweredOn') {
        clearTimeout(timeout);
        noble.removeListener('stateChange', onStateChange);
        this.setupNobleEventHandlers();
        this.isInitialized = true;
        resolve();
      }
    });
  }

  private setupNobleEventHandlers(): void {
    noble.on('discover', (peripheral) => {
      const mac = peripheral.address?.toLowerCase();
      if (!mac) return;

      // Log all discovered devices for debugging
      console.log(`Discovered BLE device: ${mac} (${peripheral.advertisement?.localName || 'Unknown'}) RSSI: ${peripheral.rssi}dBm`);

      const device = this.devices.get(mac);
      
      if (device && !device.connected) {
        console.log(`Found BMS device: ${device.track} track (${mac}) RSSI: ${peripheral.rssi}dBm`);
        this.connectToDevice(peripheral, device);
      } else if (!device) {
        // Log devices that don't match our configured MACs
        console.log(`Device ${mac} not in configured BMS list`);
      }
    });

    noble.on('scanStart', () => {
      console.log('BLE scan started');
    });

    noble.on('scanStop', () => {
      console.log('BLE scan stopped');
    });

    noble.on('warning', (message) => {
      console.log('Noble warning:', message);
    });
  }

  private async startScanning(): Promise<void> {
    if (this.isScanning || !this.isInitialized) return;

    try {
      console.log('Starting BLE scan for BMS devices...');
      console.log(`Looking for devices: ${this.config.leftTrackMac}, ${this.config.rightTrackMac}`);
      
      // Stop any existing scan
      if (noble.state === 'poweredOn') {
        await noble.stopScanningAsync();
      }

      // Start scanning with allowDuplicates for better discovery
      await noble.startScanningAsync([], true); // true = allowDuplicates
      this.isScanning = true;

      // Auto-stop scan after timeout to save power
      if (this.scanTimer) clearTimeout(this.scanTimer);
      this.scanTimer = setTimeout(async () => {
        console.log('Scan timeout reached, stopping scan...');
        await this.stopScanning();
        // Restart scan periodically if devices not connected
        const hasDisconnectedDevices = Array.from(this.devices.values()).some(d => !d.connected);
        if (hasDisconnectedDevices) {
          console.log('Restarting scan in 5 seconds...');
          setTimeout(() => this.startScanning(), 5000);
        }
      }, this.config.scanTimeout!);

    } catch (error) {
      console.error('Error starting BLE scan:', error);
      this.isScanning = false;
    }
  }

  private async stopScanning(): Promise<void> {
    if (!this.isScanning) return;

    try {
      if (noble.state === 'poweredOn') {
        await noble.stopScanningAsync();
      }
      this.isScanning = false;
      
      if (this.scanTimer) {
        clearTimeout(this.scanTimer);
        this.scanTimer = undefined;
      }
    } catch (error) {
      console.error('Error stopping BLE scan:', error);
    }
  }

  private async connectToDevice(peripheral: any, device: BMSDevice): Promise<void> {
    if (device.connected || device.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      return;
    }

    try {
      console.log(`Connecting to ${device.track} track BMS (attempt ${device.reconnectAttempts + 1})...`);
      
      // Stop scanning while connecting
      await this.stopScanning();

      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, this.config.connectionTimeout);

        peripheral.connect((error: any) => {
          clearTimeout(timeout);
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });

      device.peripheral = peripheral;
      
      // Discover services and characteristics
      const services = await new Promise<any[]>((resolve, reject) => {
        peripheral.discoverServices([this.BMS_SERVICE_UUID], (error: any, services: any[]) => {
          if (error) reject(error);
          else resolve(services || []);
        });
      });

      if (services.length === 0) {
        throw new Error('BMS service not found');
      }

      const characteristics = await new Promise<any[]>((resolve, reject) => {
        services[0].discoverCharacteristics([this.BMS_CHARACTERISTIC_UUID], (error: any, characteristics: any[]) => {
          if (error) reject(error);
          else resolve(characteristics || []);
        });
      });

      if (characteristics.length === 0) {
        throw new Error('BMS characteristic not found');
      }

      device.characteristic = characteristics[0];
      device.connected = true;
      device.reconnectAttempts = 0;

      console.log(`✓ Successfully connected to ${device.track} track BMS`);

      // Handle disconnection
      peripheral.once('disconnect', () => {
        console.log(`${device.track} track BMS disconnected`);
        device.connected = false;
        device.peripheral = undefined;
        device.characteristic = undefined;
        device.reconnectAttempts++;
        
        // Restart scanning to reconnect after delay
        setTimeout(() => this.startScanning(), 3000);
      });

    } catch (error) {
      console.error(`Failed to connect to ${device.track} track BMS:`, error);
      device.connected = false;
      device.reconnectAttempts++;
      
      // Restart scanning after failed connection
      setTimeout(() => this.startScanning(), 2000);
    }
  }

  async connect(): Promise<boolean> {
    try {
      console.log('Initializing Bluetooth BLE for Raspberry Pi 5...');
      
      await this.initializeNoble();
      await this.startScanning();
      
      // Start polling for data
      this.startDataPolling();
      
      console.log('BMS Bluetooth integration initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize BMS Bluetooth connection:', error);
      return false;
    }
  }

  async disconnect(): Promise<void> {
    await this.stopScanning();
    this.stopDataPolling();

    for (const device of this.devices.values()) {
      if (device.peripheral && device.connected) {
        try {
          await new Promise<void>((resolve) => {
            device.peripheral.disconnect(() => resolve());
          });
        } catch (error) {
          console.error(`Error disconnecting ${device.track} track BMS:`, error);
        }
      }
    }
  }

  private startDataPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
    }

    this.pollTimer = setInterval(async () => {
      try {
        const data = await this.readBatteryData();
        // Data is automatically broadcast via WebSocket in routes.ts
      } catch (error) {
        // Silently handle polling errors to avoid spam
        if (error instanceof Error && !error.message.includes('not connected')) {
          console.error('Error during data polling:', error);
        }
      }
    }, this.config.pollInterval);
  }

  private stopDataPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
  }

  async readBatteryData(): Promise<BatteryData[]> {
    const allBatteries: BatteryData[] = [];

    for (const device of this.devices.values()) {
      if (device.connected && device.characteristic) {
        try {
          const batteries = await this.readDeviceData(device);
          allBatteries.push(...batteries);
          console.log(`Successfully read data from ${device.track} track BMS`);
        } catch (error) {
          console.error(`Error reading data from ${device.track} track BMS:`, error);
        }
      } else {
        console.warn(`${device.track} track BMS not connected - MAC: ${device.mac}`);
      }
    }

    if (allBatteries.length === 0) {
      console.warn('No real BMS data available - check BMS connections');
    }

    return allBatteries;
  }

  private async readDeviceData(device: BMSDevice): Promise<BatteryData[]> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('BMS read timeout'));
      }, 5000);

      // Send read command
      device.characteristic.write(this.BMS_READ_COMMAND, false, (error: any) => {
        if (error) {
          clearTimeout(timeout);
          reject(error);
          return;
        }

        // Read response
        device.characteristic.read((error: any, data: Buffer) => {
          clearTimeout(timeout);
          
          if (error) {
            reject(error);
            return;
          }

          try {
            const batteries = this.parseBMSData(data, device.track);
            device.lastData = new Date();
            resolve(batteries);
          } catch (parseError) {
            reject(parseError);
          }
        });
      });
    });
  }

  private parseBMSData(data: Buffer, track: 'left' | 'right'): BatteryData[] {
    if (data.length < 34) {
      throw new Error('Invalid BMS data length');
    }

    // Overkill Solar BMS data format parsing
    const batteries: BatteryData[] = [];
    const cellCount = Math.min(data[25], this.config.batteryCount || 4);

    for (let i = 0; i < cellCount; i++) {
      const voltageOffset = 6 + (i * 2);
      const voltage = data.readUInt16BE(voltageOffset) / 1000; // Convert mV to V
      
      // Calculate charge level based on LiFePO4 voltage curve
      const chargeLevel = this.calculateChargeLevel(voltage);
      
      // Current is at offset 2-3 (signed 16-bit, in 10mA units)
      const current = data.readInt16BE(2) / 100; // Convert to Amps
      
      // Temperature is at offset 23-24
      const temperature = data.readInt16BE(23) / 10; // Convert to Celsius

      let status: 'normal' | 'warning' | 'critical' = 'normal';
      if (voltage < 3.0) status = 'critical';
      else if (voltage < 3.1) status = 'warning';

      batteries.push({
        batteryNumber: (track === 'left' ? 0 : 4) + i + 1, // 1-4 for left, 5-8 for right
        voltage: Math.round(voltage * 100) / 100,
        amperage: Math.round(Math.abs(current) * 100) / 100,
        chargeLevel: Math.round(chargeLevel),
        temperature: Math.round(temperature),
        status,
        track,
        trackPosition: i + 1
      });
    }

    return batteries;
  }

  private calculateChargeLevel(voltage: number): number {
    // LiFePO4 voltage curve approximation
    const minVoltage = 2.5;
    const maxVoltage = 3.65;
    const nominalVoltage = 3.2;

    if (voltage <= minVoltage) return 0;
    if (voltage >= maxVoltage) return 100;

    // Non-linear approximation for LiFePO4
    if (voltage < nominalVoltage) {
      return ((voltage - minVoltage) / (nominalVoltage - minVoltage)) * 50;
    } else {
      return 50 + ((voltage - nominalVoltage) / (maxVoltage - nominalVoltage)) * 50;
    }
  }

  isConnectedToBMS(): boolean {
    return Array.from(this.devices.values()).some(device => device.connected);
  }

  getConnectionStatus(): { left: boolean; right: boolean } {
    const leftDevice = this.devices.get(this.config.leftTrackMac.toLowerCase());
    const rightDevice = this.devices.get(this.config.rightTrackMac.toLowerCase());
    
    return {
      left: leftDevice?.connected || false,
      right: rightDevice?.connected || false
    };
  }

  getConfig(): BMSConfig {
    return { ...this.config };
  }

  updateConfig(newConfig: Partial<BMSConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  // Get device status for debugging
  getDeviceStatus(): { [mac: string]: { track: string; connected: boolean; reconnectAttempts: number; lastData?: Date } } {
    const status: any = {};
    for (const [mac, device] of this.devices.entries()) {
      status[mac] = {
        track: device.track,
        connected: device.connected,
        reconnectAttempts: device.reconnectAttempts,
        lastData: device.lastData
      };
    }
    return status;
  }
}

// Create singleton instance with your BMS MAC addresses
export const bmsIntegration = new BMSIntegration({
  leftTrackMac: 'A4:C1:38:7C:2D:F0',   // Left Track BMS
  rightTrackMac: 'E0:9F:2A:E4:94:1D',  // Right Track BMS
  pollInterval: 2000,
  batteryCount: 4,
  connectionTimeout: 15000,
  scanTimeout: 30000,
  maxReconnectAttempts: 5
});

// Auto-connect on module load
bmsIntegration.connect().then(connected => {
  if (connected) {
    console.log('BMS Integration initialized successfully for Raspberry Pi 5');
    console.log('Scanning for BMS devices...');
  } else {
    console.warn('BMS Integration failed to initialize');
  }
});
