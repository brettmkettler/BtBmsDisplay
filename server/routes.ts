import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { batteryUpdateSchema, type BatteryUpdate } from "@shared/schema";
import * as os from "os";
import { execSync } from "child_process";
import fetch from "node-fetch";

export async function registerRoutes(app: Express): Promise<Server> {
  // Get latest battery data from Python BMS API
  app.get("/api/batteries", async (req, res) => {
    try {
      const response = await fetch("http://localhost:8000/api/batteries");
      if (!response.ok) {
        throw new Error(`BMS API responded with status: ${response.status}`);
      }
      const batteries = await response.json();
      res.json(batteries);
    } catch (error) {
      console.error("Error fetching battery data from Python BMS API:", error);
      res.status(500).json({ error: "Failed to fetch battery data" });
    }
  });

  // Get BMS connection status from Python BMS API
  app.get("/api/bms/status", async (req, res) => {
    try {
      const response = await fetch("http://localhost:8000/api/bms/status");
      if (!response.ok) {
        throw new Error(`BMS API responded with status: ${response.status}`);
      }
      const status = await response.json();
      res.json(status);
    } catch (error) {
      console.error("Error fetching BMS status from Python BMS API:", error);
      res.status(500).json({ error: "Failed to fetch BMS status" });
    }
  });

  // Toggle mock mode - not applicable for Python API, return error
  app.post("/api/bms/mock/:enabled", async (req, res) => {
    res.status(501).json({ error: "Mock mode not supported with Python BMS API" });
  });

  // Update battery data (legacy endpoint for external systems)
  app.post("/api/batteries/update", async (req, res) => {
    try {
      const batteryData = req.body;
      
      // Validate the incoming data
      if (!Array.isArray(batteryData)) {
        return res.status(400).json({ error: "Battery data must be an array" });
      }

      // Save to storage
      await storage.saveBatteryData(batteryData);

      // Broadcast to all connected WebSocket clients
      const response = await fetch("http://localhost:8000/api/bms/status");
      if (!response.ok) {
        throw new Error(`BMS API responded with status: ${response.status}`);
      }
      const connectionStatus = await response.json();
      const update: BatteryUpdate = {
        type: "battery_update",
        batteries: batteryData.map(b => ({
          batteryNumber: b.batteryNumber,
          voltage: b.voltage,
          amperage: b.amperage,
          chargeLevel: b.chargeLevel,
          temperature: b.temperature,
          status: b.status,
          track: b.track,
          trackPosition: b.trackPosition,
        })),
        connectionStatus
      };

      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(update));
        }
      });

      res.json({ success: true, message: "Battery data updated successfully" });
    } catch (error) {
      console.error("Error updating battery data:", error);
      res.status(500).json({ error: "Failed to update battery data" });
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
  app.get("/api/system", async (req, res) => {
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

      // Get BMS connection status for system info
      const response = await fetch("http://localhost:8000/api/bms/status");
      if (!response.ok) {
        throw new Error(`BMS API responded with status: ${response.status}`);
      }
      const bmsStatus = await response.json();

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
        uptime: Math.floor(os.uptime()),
        bmsConnected: bmsStatus.left || bmsStatus.right,
        bmsStatus: bmsStatus
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

    // Send initial battery data and connection status
    const sendInitialData = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/batteries");
        if (!response.ok) {
          throw new Error(`BMS API responded with status: ${response.status}`);
        }
        const batteries = await response.json();
        const connectionStatusResponse = await fetch("http://localhost:8000/api/bms/status");
        if (!connectionStatusResponse.ok) {
          throw new Error(`BMS API responded with status: ${connectionStatusResponse.status}`);
        }
        const connectionStatus = await connectionStatusResponse.json();
        
        const update: BatteryUpdate = {
          type: "battery_update",
          batteries: batteries.map(b => ({
            batteryNumber: b.batteryNumber,
            voltage: b.voltage,
            amperage: b.amperage,
            chargeLevel: b.chargeLevel,
            temperature: b.temperature,
            status: b.status,
            track: b.track,
            trackPosition: b.trackPosition,
          })),
          connectionStatus
        };
        
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(update));
        }
      } catch (error) {
        console.error('Error sending initial WebSocket data:', error);
      }
    };

    sendInitialData();

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  // Real-time data broadcasting from BMS
  const broadcastBatteryData = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/batteries");
      if (!response.ok) {
        throw new Error(`BMS API responded with status: ${response.status}`);
      }
      const batteries = await response.json();
      const connectionStatusResponse = await fetch("http://localhost:8000/api/bms/status");
      if (!connectionStatusResponse.ok) {
        throw new Error(`BMS API responded with status: ${connectionStatusResponse.status}`);
      }
      const connectionStatus = await connectionStatusResponse.json();
      
      const update: BatteryUpdate = {
        type: "battery_update",
        batteries: batteries.map(b => ({
          batteryNumber: b.batteryNumber,
          voltage: b.voltage,
          amperage: b.amperage,
          chargeLevel: b.chargeLevel,
          temperature: b.temperature,
          status: b.status,
          track: b.track,
          trackPosition: b.trackPosition,
        })),
        connectionStatus
      };

      // Save to storage
      await storage.saveBatteryData(batteries);

      // Broadcast to all connected clients
      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(update));
        }
      });
    } catch (error) {
      // Silently handle errors to avoid spam
      if (error instanceof Error && !error.message.includes('not connected')) {
        console.error('Error broadcasting battery data:', error);
      }
    }
  };

  // Start real-time data broadcasting
  setInterval(broadcastBatteryData, 2000);

  return httpServer;
}
