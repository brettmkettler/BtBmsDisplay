import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { batteryUpdateSchema, type BatteryUpdate } from "@shared/schema";
import * as os from "os";
import { execSync } from "child_process";

// Python BMS API configuration
const PYTHON_BMS_API_URL = process.env.PYTHON_BMS_API_URL || 'http://localhost:8000';

// Helper function to fetch from Python API
async function fetchFromPythonAPI(endpoint: string) {
  try {
    const response = await fetch(`${PYTHON_BMS_API_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching from Python API ${endpoint}:`, error);
    throw error;
  }
}

export async function registerRoutes(app: Express): Promise<Server> {
  // Get latest battery data from Python BMS API
  app.get("/api/batteries", async (req, res) => {
    try {
      const data = await fetchFromPythonAPI('/api/batteries');
      // Return batteries array directly to match UI expectations
      res.json(data.batteries || []);
    } catch (error) {
      console.error("Error fetching battery data from Python API:", error);
      res.json([]); // Return empty array if no data available
    }
  });

  // Get BMS connection status from Python API
  app.get("/api/bms/status", async (req, res) => {
    try {
      const data = await fetchFromPythonAPI('/api/bms/status');
      res.json(data);
    } catch (error) {
      console.error("Error fetching BMS status from Python API:", error);
      res.status(503).json({ 
        connected: false,
        tracks: { left: false, right: false },
        devices: {},
        error: "Python BMS API unavailable"
      });
    }
  });

  // Update battery data (legacy endpoint for external systems)
  app.post("/api/batteries/update", async (req, res) => {
    try {
      const batteryData = req.body;
      
      // Validate the incoming data
      if (!Array.isArray(batteryData)) {
        return res.status(400).json({ error: "Battery data must be an array" });
      }

      // Store the data
      await storage.storeBatteryData(batteryData);
      
      res.json({ 
        success: true, 
        message: "Battery data updated successfully",
        count: batteryData.length 
      });
    } catch (error) {
      console.error("Error updating battery data:", error);
      res.status(500).json({ error: "Failed to update battery data" });
    }
  });

  // Get system information
  app.get("/api/system", async (req, res) => {
    try {
      // Get system info from Python API
      const pythonSystemInfo = await fetchFromPythonAPI('/api/system');
      
      // Add Node.js specific info
      const systemInfo = {
        ...pythonSystemInfo,
        nodejs: {
          version: process.version,
          platform: process.platform,
          arch: process.arch,
          uptime: process.uptime(),
          memory: process.memoryUsage()
        },
        proxy_status: "Connected to Python BMS API"
      };
      
      res.json(systemInfo);
    } catch (error) {
      console.error("Error fetching system info:", error);
      
      // Fallback to basic Node.js info if Python API unavailable
      const fallbackInfo = {
        nodejs: {
          version: process.version,
          platform: process.platform,
          arch: process.arch,
          uptime: process.uptime(),
          memory: process.memoryUsage()
        },
        proxy_status: "Python BMS API unavailable",
        error: error.message
      };
      
      res.json(fallbackInfo);
    }
  });

  // Proxy reconnect request to Python API
  app.post("/api/bms/reconnect", async (req, res) => {
    try {
      const response = await fetch(`${PYTHON_BMS_API_URL}/api/bms/reconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Error reconnecting BMS via Python API:", error);
      res.status(500).json({ error: "Failed to reconnect BMS" });
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

  const server = createServer(app);
  
  // WebSocket server for real-time updates
  const wss = new WebSocketServer({ server });
  
  wss.on("connection", (ws: WebSocket) => {
    console.log("WebSocket client connected");
    
    ws.on("close", () => {
      console.log("WebSocket client disconnected");
    });
    
    ws.on("error", (error) => {
      console.error("WebSocket error:", error);
    });
  });

  // Broadcast battery data to all connected WebSocket clients
  const broadcastBatteryData = async () => {
    if (wss.clients.size === 0) return;
    
    try {
      // Fetch latest data from Python API
      const batteryData = await fetchFromPythonAPI('/api/batteries');
      const statusData = await fetchFromPythonAPI('/api/bms/status');
      
      const message = JSON.stringify({
        type: 'batteryUpdate',
        data: {
          batteries: batteryData.batteries || [],
          connectionStatus: statusData.tracks || { left: false, right: false },
          timestamp: new Date().toISOString()
        }
      });

      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(message);
        }
      });
    } catch (error) {
      console.error("Error broadcasting battery data:", error);
      
      // Send empty data if Python API unavailable
      const fallbackMessage = JSON.stringify({
        type: 'batteryUpdate',
        data: {
          batteries: [],
          connectionStatus: { left: false, right: false },
          timestamp: new Date().toISOString(),
          error: 'Python BMS API unavailable'
        }
      });

      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(fallbackMessage);
        }
      });
    }
  };

  // Broadcast battery data every 2 seconds
  setInterval(broadcastBatteryData, 2000);

  return server;
}
