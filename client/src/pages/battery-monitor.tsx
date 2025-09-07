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

  return (
    <div className="min-h-screen bg-display-black text-battery-red p-6">
      {/* Loading Screen Overlay */}
      {showLoadingScreen && (
        <LoadingScreen
          connectionStatus={connectionStatus}
          isWebSocketConnected={isConnected}
          lastUpdate={lastUpdate}
        />
      )}

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

      {/* Connection Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <ConnectionStatus
          track="left"
          isConnected={connectionStatus.left}
          isWebSocketConnected={isConnected}
          lastUpdate={lastUpdate}
        />
        <ConnectionStatus
          track="right"
          isConnected={connectionStatus.right}
          isWebSocketConnected={isConnected}
          lastUpdate={lastUpdate}
        />
      </div>

      {/* Server Connection Alert */}
      {!isConnected && (
        <Alert className="mb-6 border-battery-red bg-display-black">
          <AlertTriangle className="h-4 w-4 text-battery-red" />
          <AlertDescription className="text-battery-red">
            Connection lost to server. Attempting to reconnect...
          </AlertDescription>
        </Alert>
      )}

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
  );
}
