#!/usr/bin/env python3
"""
BMS API Server
FastAPI server that provides REST endpoints for Overkill Solar BMS data.
Uses bluepy-based BMS reader for reliable Bluetooth BLE communication.
"""

import asyncio
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psutil
import uvicorn

from bms_reader import OverkillBMSReader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="BMS API Server",
    description="REST API for Overkill Solar BMS data",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global BMS reader instance
bms_reader: Optional[OverkillBMSReader] = None
reader_thread: Optional[threading.Thread] = None

# BMS Configuration
BMS_CONFIG = {
    'left_track_mac': 'A4:C1:38:7C:2D:F0',
    'right_track_mac': 'E0:9F:2A:E4:94:1D',
    'connection_timeout': 15,
    'poll_interval': 2
}

def run_bms_reader():
    """Run BMS reader in a separate thread"""
    global bms_reader
    
    try:
        logger.info("Starting BMS reader thread")
        bms_reader = OverkillBMSReader(BMS_CONFIG)
        
        # Connect to devices
        results = bms_reader.connect_all_devices()
        logger.info(f"BMS connection results: {results}")
        
        if any(results.values()):
            # Start continuous reading
            bms_reader.start_reading()
        else:
            logger.error("Failed to connect to any BMS devices")
            
    except Exception as e:
        logger.error(f"Error in BMS reader thread: {e}")
    finally:
        if bms_reader:
            bms_reader.disconnect_all()

@app.on_event("startup")
async def startup_event():
    """Initialize BMS reader on startup"""
    global reader_thread
    
    logger.info("Starting BMS API Server...")
    
    # Start BMS reader in background thread
    reader_thread = threading.Thread(target=run_bms_reader, daemon=True)
    reader_thread.start()
    
    # Give it a moment to initialize
    await asyncio.sleep(2)
    
    logger.info("BMS API Server started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bms_reader
    
    logger.info("Shutting down BMS API Server...")
    
    if bms_reader:
        bms_reader.stop_reading()
        bms_reader.disconnect_all()
    
    logger.info("BMS API Server shutdown complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/batteries")
async def get_batteries():
    """Get all battery data"""
    global bms_reader
    
    if not bms_reader:
        return JSONResponse(
            status_code=503,
            content={"error": "BMS reader not initialized", "batteries": []}
        )
    
    try:
        batteries = bms_reader.get_all_batteries()
        
        if not batteries:
            # Return empty array with status info
            connection_status = bms_reader.get_connection_status()
            connected_tracks = [track for track, status in connection_status.items() if status['connected']]
            
            return {
                "batteries": [],
                "status": "no_data",
                "message": f"No battery data available. Connected tracks: {connected_tracks}",
                "connection_status": connection_status
            }
        
        return {
            "batteries": batteries,
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "count": len(batteries)
        }
        
    except Exception as e:
        logger.error(f"Error getting battery data: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "batteries": []}
        )

@app.get("/api/bms/status")
async def get_bms_status():
    """Get BMS connection status"""
    global bms_reader
    
    if not bms_reader:
        return JSONResponse(
            status_code=503,
            content={
                "error": "BMS reader not initialized",
                "status": {
                    "left": {"connected": False, "error_message": "Reader not initialized"},
                    "right": {"connected": False, "error_message": "Reader not initialized"}
                }
            }
        )
    
    try:
        status = bms_reader.get_connection_status()
        
        # Add summary info
        connected_count = sum(1 for s in status.values() if s['connected'])
        total_count = len(status)
        
        return {
            "status": status,
            "summary": {
                "connected": connected_count,
                "total": total_count,
                "all_connected": connected_count == total_count,
                "any_connected": connected_count > 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting BMS status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/bms/reconnect")
async def reconnect_bms():
    """Force reconnect to BMS devices"""
    global bms_reader
    
    if not bms_reader:
        return JSONResponse(
            status_code=503,
            content={"error": "BMS reader not initialized"}
        )
    
    try:
        logger.info("Manual BMS reconnect requested")
        
        # Disconnect all devices
        bms_reader.disconnect_all()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Reconnect
        results = bms_reader.connect_all_devices()
        
        return {
            "message": "Reconnect attempt completed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during BMS reconnect: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/system")
async def get_system_info():
    """Get system information including BMS status"""
    global bms_reader
    
    try:
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get BMS status if available
        bms_status = None
        if bms_reader:
            bms_status = bms_reader.get_connection_status()
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 1),
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "bms": bms_status,
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/config")
async def get_config():
    """Get current BMS configuration"""
    return {
        "config": BMS_CONFIG,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "BMS API Server",
        "version": "2.0.0",
        "description": "REST API for Overkill Solar BMS data using bluepy",
        "endpoints": {
            "batteries": "/api/batteries",
            "bms_status": "/api/bms/status", 
            "system": "/api/system",
            "reconnect": "/api/bms/reconnect",
            "config": "/api/config",
            "health": "/health",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("Starting BMS API Server...")
    
    try:
        uvicorn.run(
            "bms_api_server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
