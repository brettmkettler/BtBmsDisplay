import { useState } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { BatteryListItem } from "@/components/battery-list-item";
import { LoadingScreen } from "@/components/loading-screen";
import { ConnectionStatus } from "@/components/connection-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Bluetooth } from "lucide-react";

export default function BatteryMonitor() {
  const { isConnected, batteryData, connectionStatus, lastUpdate } = useWebSocket();
  const [selectedTrack, setSelectedTrack] = useState<'left' | 'right'>('left');

  // Show loading screen if not both BMS devices are connected
  const bothConnected = connectionStatus.left && connectionStatus.right;
  const showLoadingScreen = false;

  // Create fallback data if no data is available
  const fallbackData = [
    // Left track batteries
    { batteryNumber: 1, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'left', trackPosition: 1 },
    { batteryNumber: 2, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'left', trackPosition: 2 },
    { batteryNumber: 3, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'left', trackPosition: 3 },
    { batteryNumber: 4, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'left', trackPosition: 4 },
    // Right track batteries
    { batteryNumber: 5, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'right', trackPosition: 1 },
    { batteryNumber: 6, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'right', trackPosition: 2 },
    { batteryNumber: 7, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'right', trackPosition: 3 },
    { batteryNumber: 8, voltage: 3.33, amperage: 0.0, chargeLevel: 0, track: 'right', trackPosition: 4 },
  ];

  // Use WebSocket data if available, otherwise use fallback
  const displayData = batteryData.length > 0 ? batteryData : fallbackData;

  // Filter batteries by selected track
  const filteredBatteries = displayData.filter(battery => battery.track === selectedTrack);

  // Debug logging
  console.log('Battery Monitor Debug:', {
    batteryDataLength: batteryData.length,
    displayDataLength: displayData.length,
    filteredBatteriesLength: filteredBatteries.length,
    selectedTrack,
    isConnected,
    connectionStatus
  });

  const handleActivateClick = () => {
    console.log('ACTIVATE button clicked');
  };

  const handleSystemClick = () => {
    console.log('SYSTEM button clicked');
  };

  return (
    <div className="min-h-screen bg-display-black text-battery-red flex flex-col">
      {/* Loading Screen Overlay */}
      {showLoadingScreen && (
        <LoadingScreen
          connectionStatus={connectionStatus}
          isWebSocketConnected={isConnected}
          lastUpdate={lastUpdate}
        />
      )}

      {/* Main Content Area - 4/5 of screen height */}
      <div className="flex-1 p-6" style={{ height: '80vh' }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-battery-red">BATTERY MONITOR</h1>
          <div className="flex items-center gap-2">
            <Bluetooth className={`w-6 h-6 ${isConnected ? 'text-battery-red' : 'text-battery-red opacity-50'}`} />
            <span className={`text-sm ${isConnected ? 'text-battery-red' : 'text-battery-red opacity-50'}`}>
              {isConnected ? 'Server Connected' : 'Server Disconnected'}
            </span>
          </div>
        </div>

        {/* Track Selection */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-display-black border border-battery-red rounded-lg p-1">
            <button
              onClick={() => setSelectedTrack('left')}
              className={`px-6 py-3 rounded-md font-semibold transition-colors ${
                selectedTrack === 'left'
                  ? 'bg-battery-red text-display-black'
                  : 'text-battery-red hover:bg-battery-red hover:bg-opacity-20'
              }`}
            >
              LEFT TRACK
            </button>
            <button
              onClick={() => setSelectedTrack('right')}
              className={`px-6 py-3 rounded-md font-semibold transition-colors ${
                selectedTrack === 'right'
                  ? 'bg-battery-red text-display-black'
                  : 'text-battery-red hover:bg-battery-red hover:bg-opacity-20'
              }`}
            >
              RIGHT TRACK
            </button>
          </div>
        </div>

        {/* Battery List */}
        <div className="space-y-4">
          {filteredBatteries.map((battery) => (
            <BatteryListItem
              key={`${battery.track}-${battery.trackPosition}`}
              batteryNumber={battery.trackPosition}
              voltage={battery.voltage}
              amperage={battery.amperage}
              chargeLevel={battery.chargeLevel}
            />
          ))}
          
          {/* Debug info */}
          <div className="text-xs text-battery-red opacity-50 mt-4">
            Debug: Showing {filteredBatteries.length} batteries for {selectedTrack} track
            {batteryData.length === 0 && " (using fallback data)"}
          </div>
        </div>
      </div>

      {/* Bottom Control Section - 1/5 of screen height */}
      <div className="flex" style={{ height: '20vh' }}>
        {/* ACTIVATE Button - Left Half */}
        <button
          onClick={handleActivateClick}
          className="flex-1 bg-green-600 hover:bg-green-700 transition-colors flex items-center justify-center border-r border-display-black"
          style={{ 
            fontSize: '3rem',
            fontWeight: 'bold',
            color: 'white',
            textAlign: 'center'
          }}
        >
          <span style={{ 
            position: 'relative',
            top: '0px',
            left: '0px'
          }}>
            ACTIVATE
          </span>
        </button>

        {/* SYSTEM Button - Right Half */}
        <button
          onClick={handleSystemClick}
          className="flex-1 bg-battery-red hover:bg-red-700 transition-colors flex items-center justify-center border-l border-display-black"
          style={{ 
            fontSize: '3rem',
            fontWeight: 'bold',
            color: 'white',
            textAlign: 'center'
          }}
        >
          <span style={{ 
            position: 'relative',
            top: '0px',
            left: '0px'
          }}>
            SYSTEM
          </span>
        </button>
      </div>
    </div>
  );
}
