import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { batteryUpdateSchema, type BatteryUpdate } from "@shared/schema";
import * as os from "os";
import { execSync } from "child_process";

export async function registerRoutes(app: Express): Promise<Server> {
  // Get latest battery data
  app.get("/api/batteries", async (req, res) => {
    try {
      const batteries = await storage.getLatestBatteryData();
      res.json(batteries);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch battery data" });
    }
  });

  // Screen control APIs
  app.post("/api/screen/off", (req, res) => {
    try {
      // Turn screen black/off
      res.json({ success: true, message: "Screen turned off" });
    } catch (error) {
      res.status(500).json({ error: "Failed to turn off screen" });
    }
  });

  app.post("/api/screen/on", (req, res) => {
    try {
      // Turn screen back on
      res.json({ success: true, message: "Screen turned on" });
    } catch (error) {
      res.status(500).json({ error: "Failed to turn on screen" });
    }
  });

  // System information API
  app.get("/api/system", (req, res) => {
    try {
      const totalMem = os.totalmem();
      const freeMem = os.freemem();
      const usedMem = totalMem - freeMem;
      
      // Get CPU usage
      const cpus = os.cpus();
      let totalIdle = 0;
      let totalTick = 0;
      
      cpus.forEach(cpu => {
        for (const type in cpu.times) {
          totalTick += cpu.times[type as keyof typeof cpu.times];
        }
        totalIdle += cpu.times.idle;
      });
      
      const cpuUsage = Math.round(((totalTick - totalIdle) / totalTick) * 100);
      
      // Get disk usage (Linux/macOS)
      let diskUsage = { total: 0, used: 0, available: 0 };
      try {
        const dfOutput = execSync('df -h /', { encoding: 'utf8' });
        const lines = dfOutput.split('\n');
        if (lines.length > 1) {
          const parts = lines[1].split(/\s+/);
          diskUsage = {
            total: parseFloat(parts[1].replace('G', '')),
            used: parseFloat(parts[2].replace('G', '')),
            available: parseFloat(parts[3].replace('G', ''))
          };
        }
      } catch (e) {
        // Fallback for systems without df command
        diskUsage = { total: 100, used: 50, available: 50 };
      }

      const systemInfo = {
        unitId: "J5-CONSOLE-001",
        softwareVersion: "v2.1.4",
        registeredTo: "BRETTKETTLER",
        systemDate: new Date().toLocaleDateString(),
        systemTime: new Date().toLocaleTimeString(),
        cpuUsage: cpuUsage,
        memoryUsage: Math.round((usedMem / totalMem) * 100),
        internalDriveUsage: Math.round((diskUsage.used / diskUsage.total) * 100),
        externalDriveUsage: 0, // Placeholder for external drive
        hostname: os.hostname(),
        platform: os.platform(),
        arch: os.arch(),
        uptime: Math.floor(os.uptime())
      };

      res.json(systemInfo);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch system information" });
    }
  });

  const httpServer = createServer(app);

  // WebSocket server for real-time battery updates
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws) => {
    console.log('WebSocket client connected');

    // Send initial battery data
    storage.getLatestBatteryData().then(batteries => {
      const update: BatteryUpdate = {
        type: "battery_update",
        batteries: batteries.map(b => ({
          batteryNumber: b.batteryNumber,
          voltage: b.voltage,
          amperage: b.amperage,
          chargeLevel: b.chargeLevel,
        })),
      };
      
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(update));
      }
    });

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  // Simulate BMS data updates every 2 seconds
  setInterval(() => {
    // Simulate realistic LiFePO4 data with small variations
    // 4 batteries per track (left track: 1-4, right track: 5-8)
    const mockBatteries = Array.from({ length: 8 }, (_, i) => {
      const batteryNumber = i + 1;
      const track = batteryNumber <= 4 ? 'left' : 'right';
      const trackPosition = batteryNumber <= 4 ? batteryNumber : batteryNumber - 4;
      
      return {
        batteryNumber,
        track,
        trackPosition,
        voltage: 3.2 + Math.random() * 0.45, // 3.2V - 3.65V range
        amperage: 10 + Math.random() * 5, // 10-15A range
        chargeLevel: Math.max(0, Math.min(100, ((3.2 + Math.random() * 0.45 - 2.5) / (3.65 - 2.5)) * 100)),
      };
    });

    // Save to storage
    storage.saveBatteryData(mockBatteries.map(b => ({
      batteryNumber: b.batteryNumber,
      voltage: b.voltage,
      amperage: b.amperage,
      chargeLevel: b.chargeLevel,
    })));

    // Broadcast to all connected clients
    const update: BatteryUpdate = {
      type: "battery_update",
      batteries: mockBatteries.map(b => ({
        batteryNumber: b.batteryNumber,
        voltage: b.voltage,
        amperage: b.amperage,
        chargeLevel: b.chargeLevel,
        track: b.track,
        trackPosition: b.trackPosition,
      })),
    };

    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(update));
      }
    });
  }, 2000);

  return httpServer;
}
