#!/usr/bin/env python3
"""
BMS API Server
FastAPI server that hosts BMS data endpoints for the UI to consume.
Runs the BMS reader in the background and provides REST API access to battery data.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from bms_reader import OverkillBMSReader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global BMS reader instance
bms_reader: Optional[OverkillBMSReader] = None
background_task: Optional[asyncio.Task] = None

# Configuration
BMS_CONFIG = {
    'left_track_mac': 'A4:C1:38:7C:2D:F0',
    'right_track_mac': 'E0:9F:2A:E4:94:1D',
    'scan_timeout': 30,
    'connection_timeout': 15,
    'poll_interval': 2  # seconds between data reads
}

async def bms_background_task():
    """Background task to continuously read BMS data"""
    global bms_reader
    
    logger.info("Starting BMS background task...")
    
    while True:
        try:
            if not bms_reader:
                logger.info("Initializing BMS reader...")
                bms_reader = OverkillBMSReader(BMS_CONFIG)
                
                # Scan and connect to devices
                found_devices = await bms_reader.scan_for_devices()
                
                if found_devices:
                    logger.info(f"Found {len(found_devices)} BMS devices, connecting...")
                    for track, mac in found_devices.items():
                        await bms_reader.connect_to_device(mac, track)
                else:
                    logger.warning("No BMS devices found during scan")
            
            # Read data from connected devices
            if bms_reader:
                await bms_reader.read_all_bms_data()
            
            # Wait before next read
            await asyncio.sleep(BMS_CONFIG['poll_interval'])
            
        except Exception as e:
            logger.error(f"Error in BMS background task: {e}")
            # Reset reader on error
            if bms_reader:
                try:
                    await bms_reader.disconnect_all()
                except:
                    pass
                bms_reader = None
            
            # Wait before retry
            await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan - start/stop background tasks"""
    global background_task
    
    # Startup
    logger.info("Starting BMS API Server...")
    background_task = asyncio.create_task(bms_background_task())
    
    yield
    
    # Shutdown
    logger.info("Shutting down BMS API Server...")
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    
    if bms_reader:
        await bms_reader.disconnect_all()

# Create FastAPI app
app = FastAPI(
    title="BMS API Server",
    description="API server for Overkill Solar BMS data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BMS API Server", "status": "running", "timestamp": datetime.now().isoformat()}

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
        return {
            "batteries": batteries,
            "count": len(batteries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting battery data: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading battery data: {str(e)}")

@app.get("/api/bms/status")
async def get_bms_status():
    """Get BMS connection status"""
    global bms_reader
    
    if not bms_reader:
        return {
            "connected": False,
            "tracks": {
                "left": False,
                "right": False
            },
            "devices": {
                "left": {"connected": False, "mac_address": BMS_CONFIG['left_track_mac'], "track": "left"},
                "right": {"connected": False, "mac_address": BMS_CONFIG['right_track_mac'], "track": "right"}
            },
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        connection_status = bms_reader.get_connection_status()
        
        # Format response to match UI expectations
        tracks = {
            "left": connection_status.get("left", {}).get("connected", False),
            "right": connection_status.get("right", {}).get("connected", False)
        }
        
        return {
            "connected": any(tracks.values()),
            "tracks": tracks,
            "devices": connection_status,
            "config": {
                "left_track_mac": BMS_CONFIG['left_track_mac'],
                "right_track_mac": BMS_CONFIG['right_track_mac']
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting BMS status: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading BMS status: {str(e)}")

@app.get("/api/system")
async def get_system_info():
    """Get system information"""
    global bms_reader
    
    # Get basic system info
    import platform
    import psutil
    
    connection_status = {}
    if bms_reader:
        try:
            connection_status = bms_reader.get_connection_status()
        except:
            pass
    
    return {
        "system": {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "bms": {
            "reader_initialized": bms_reader is not None,
            "connection_status": connection_status
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/bms/reconnect")
async def reconnect_bms():
    """Force reconnection to BMS devices"""
    global bms_reader
    
    try:
        if bms_reader:
            await bms_reader.disconnect_all()
        
        # Reset reader
        bms_reader = None
        
        return {
            "message": "BMS reconnection initiated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reconnecting BMS: {e}")
        raise HTTPException(status_code=500, detail=f"Error reconnecting BMS: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global bms_reader
    
    status = "healthy"
    details = {}
    
    if bms_reader:
        try:
            connection_status = bms_reader.get_connection_status()
            connected_devices = sum(1 for status in connection_status.values() if status.get('connected', False))
            details = {
                "bms_reader": "initialized",
                "connected_devices": connected_devices,
                "total_devices": len(connection_status)
            }
        except Exception as e:
            status = "degraded"
            details = {"error": str(e)}
    else:
        status = "starting"
        details = {"bms_reader": "not_initialized"}
    
    return {
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "bms_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
