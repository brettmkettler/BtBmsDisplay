import { type BatteryData, type InsertBatteryData } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getLatestBatteryData(): Promise<BatteryData[]>;
  saveBatteryData(data: InsertBatteryData[]): Promise<BatteryData[]>;
}

export class MemStorage implements IStorage {
  private batteryData: Map<number, BatteryData>;

  constructor() {
    this.batteryData = new Map();
    // Initialize with default values for 8 batteries
    for (let i = 1; i <= 8; i++) {
      this.batteryData.set(i, {
        id: randomUUID(),
        batteryNumber: i,
        voltage: 3.3,
        amperage: 12.0,
        chargeLevel: 75,
        timestamp: new Date(),
      });
    }
  }

  async getLatestBatteryData(): Promise<BatteryData[]> {
    return Array.from(this.batteryData.values()).sort((a, b) => a.batteryNumber - b.batteryNumber);
  }

  async saveBatteryData(data: InsertBatteryData[]): Promise<BatteryData[]> {
    const savedData: BatteryData[] = [];
    
    for (const batteryData of data) {
      const newData: BatteryData = {
        ...batteryData,
        id: randomUUID(),
        timestamp: new Date(),
      };
      
      this.batteryData.set(batteryData.batteryNumber, newData);
      savedData.push(newData);
    }
    
    return savedData;
  }
}

export const storage = new MemStorage();
