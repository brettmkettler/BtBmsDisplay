# Local Testing Guide for J5 Console Display

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/brettkettler/REPO/j5_console/BtBmsDisplay
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
This will start the app on **http://localhost:3000** with hot reloading.

### 3. Access the Display
Open your browser to:
- **Main Display**: http://localhost:3000
- **Battery Monitor**: Shows left/right track navigation
- **Control Panel**: Click "Show Controls" to access J5 console controls

## Testing Features

### Battery Track Navigation
- **Left Track**: Shows batteries 1-4 from the left track
- **Right Track**: Shows batteries 5-8 from the right track  
- **Navigation**: Use < and > arrows to switch between tracks
- **Mock Data**: Automatically generates realistic LiFePO4 battery data

### J5 Console Integration
The display will try to connect to your j5_console.py API on port 5000:

#### Option A: Test with j5_console.py Running
```bash
# In another terminal, start your J5 console
cd /Users/brettkettler/REPO/j5_console
python j5_console.py
```

#### Option B: Test Display Only (Mock Mode)
If j5_console.py isn't running, the display will show connection errors but battery data will still work.

### Real-time Updates
- Battery data updates every 2 seconds via WebSocket
- System status polls every 5 seconds (when j5_console.py is available)
- Connection status shows in UI

## Testing Different Scenarios

### 1. Full System Test
```bash
# Terminal 1: Start J5 Console
cd /Users/brettkettler/REPO/j5_console
python j5_console.py

# Terminal 2: Start Display
cd /Users/brettkettler/REPO/j5_console/BtBmsDisplay
npm run dev
```

### 2. Display Only Test
```bash
# Just start the display
npm run dev
# J5 controls will show connection errors, but battery monitor works
```

### 3. Production Build Test
```bash
# Build and test production version
npm run build
npm start
# Runs on port 3000 in production mode
```

## Development Tools

### Browser DevTools
- **Console**: Check for WebSocket connections and API calls
- **Network**: Monitor API requests to j5_console.py
- **Application**: View WebSocket messages for battery data

### Useful URLs
- **Display**: http://localhost:3000
- **J5 Console API**: http://localhost:5000 (when running)
- **API Docs**: http://localhost:5000 (Flask-RESTx Swagger UI)

## Customization for Testing

### Mock Data Configuration
Edit `server/routes.ts` to customize mock battery data:
```typescript
// Change battery count, voltage ranges, update intervals
const mockBatteries = Array.from({ length: 8 }, (_, i) => {
  // Modify voltage, amperage, charge levels here
});
```

### BMS Integration Testing
Edit `server/bms-integration.ts`:
```typescript
// Switch to real BMS mode
this.mockMode = false; // Enable real hardware connection
```

### Port Configuration
- **Display**: PORT=3000 (set in package.json)
- **J5 Console**: Port 5000 (hardcoded in j5_console.py)

## Troubleshooting

### Common Issues

**"Connection Lost" Banner**:
- WebSocket connection failed
- Check if development server is running
- Refresh browser

**"J5 Console Connection Error"**:
- j5_console.py not running on port 5000
- Check if Flask API is accessible
- Verify no port conflicts

**No Battery Data**:
- Check browser console for WebSocket errors
- Verify server/routes.ts is generating mock data
- Check Network tab for failed requests

### Debug Commands
```bash
# Check if ports are in use
lsof -i :3000
lsof -i :5000

# View server logs
npm run dev  # Shows server logs in terminal

# Test API directly
curl http://localhost:5000/api/system/status
curl http://localhost:3000/api/batteries
```

## Kiosk Mode Testing

### Simulate Kiosk Environment
```bash
# Start in fullscreen (Chrome)
open -a "Google Chrome" --args --kiosk http://localhost:3000

# Or use browser fullscreen
# Press F11 in browser for fullscreen mode
```

### Touch Interface Testing
- Use browser dev tools device simulation
- Test navigation arrows with touch/click
- Verify button sizes are touch-friendly

## Next Steps

Once local testing is complete:
1. **Deploy to Pi**: Follow `deploy-kiosk.md`
2. **Real BMS**: Configure actual hardware in `bms-integration.ts`
3. **Production**: Set up systemd services for auto-start
