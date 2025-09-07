import { useState } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { BatteryListItem } from "@/components/battery-list-item";
import { ConnectionStatus } from "@/components/connection-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Bluetooth } from "lucide-react";

export default function BatteryMonitor() {
  const { isConnected, batteryData, connectionStatus, lastUpdate } = useWebSocket();
  const [selectedTrack, setSelectedTrack] = useState<'left' | 'right'>('left');

  // Filter batteries by selected track
  const filteredBatteries = batteryData.filter(battery => battery.track === selectedTrack);

  return (
    <div className="min-h-screen bg-display-black text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-4xl font-bold text-battery-red">BATTERY MONITOR</h1>
        <div className="flex items-center gap-2">
          <Bluetooth className={`w-6 h-6 ${isConnected ? 'text-green-500' : 'text-red-500'}`} />
          <span className={`text-sm ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
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
        <Alert className="mb-6 border-red-500/50 bg-red-500/10">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-400">
            Connection lost to server. Attempting to reconnect...
          </AlertDescription>
        </Alert>
      )}

      {/* Track Selection */}
      <div className="flex justify-center mb-8">
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setSelectedTrack('left')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              selectedTrack === 'left'
                ? 'bg-battery-red text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            LEFT TRACK
          </button>
          <button
            onClick={() => setSelectedTrack('right')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              selectedTrack === 'right'
                ? 'bg-battery-red text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            RIGHT TRACK
          </button>
        </div>
      </div>

      {/* Battery List */}
      <div className="space-y-4">
        {filteredBatteries.length > 0 ? (
          filteredBatteries.map((battery) => (
            <BatteryListItem
              key={`${battery.track}-${battery.trackPosition}`}
              batteryNumber={battery.trackPosition}
              voltage={battery.voltage}
              amperage={battery.amperage}
              chargeLevel={battery.chargeLevel}
            />
          ))
        ) : (
          <div className="text-center py-12">
            <div className="text-gray-400 text-lg">
              {connectionStatus[selectedTrack] 
                ? 'No battery data available' 
                : `Waiting for ${selectedTrack.toUpperCase()} TRACK BMS connection...`
              }
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
