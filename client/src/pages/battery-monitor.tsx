import { useState } from "react";
import { useLocation } from "wouter";
import { useWebSocket } from "@/hooks/use-websocket";
import { BatteryListItem } from "@/components/battery-list-item";
import { LoadingScreen } from "@/components/loading-screen";
import { ConnectionStatus } from "@/components/connection-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Bluetooth } from "lucide-react";

export default function BatteryMonitor() {
  const [, setLocation] = useLocation();
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
    setLocation('/system');
  };

  return (
    <>
      {showLoadingScreen && <LoadingScreen />}
      
      <div className="min-h-screen bg-black text-red-500 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-red-500/30">
          <div className="flex items-center space-x-4">
            <Bluetooth className={`h-6 w-6 ${isConnected ? 'text-red-400' : 'text-red-600'}`} />
            <span className="text-lg font-semibold text-red-400">
              {isConnected ? 'Server Connected' : 'Server Disconnected'}
            </span>
          </div>
          
          <h1 className="text-3xl font-bold text-red-500">Battery Monitor</h1>
          
          <div className="text-right">
            <div className="text-sm text-red-400">Last Update</div>
            <div className="text-xs text-red-500/70">{lastUpdate}</div>
          </div>
        </div>

        {/* Track Selection */}
        <div className="flex justify-center p-4 border-b border-red-500/30">
          <div className="flex bg-black border border-red-500/50 rounded-lg overflow-hidden">
            <button
              onClick={() => setSelectedTrack('left')}
              className={`px-8 py-3 font-semibold transition-colors ${
                selectedTrack === 'left'
                  ? 'bg-red-500/20 text-red-400 border-r border-red-500/50'
                  : 'text-red-500/70 hover:text-red-400 hover:bg-red-500/10 border-r border-red-500/30'
              }`}
            >
              Left Track
            </button>
            <button
              onClick={() => setSelectedTrack('right')}
              className={`px-8 py-3 font-semibold transition-colors ${
                selectedTrack === 'right'
                  ? 'bg-red-500/20 text-red-400'
                  : 'text-red-500/70 hover:text-red-400 hover:bg-red-500/10'
              }`}
            >
              Right Track
            </button>
          </div>
        </div>

        {/* Connection Status Alert */}
        {!bothConnected && (
          <div className="p-4">
            <Alert className="bg-red-500/10 border-red-500/30 text-red-400">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                BMS Connection Status: Left {connectionStatus.left ? '✓' : '✗'} | Right {connectionStatus.right ? '✓' : '✗'}
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Battery List */}
        <div className="flex-1 p-6">
          <div className="space-y-4 max-w-4xl mx-auto">
            {filteredBatteries.map((battery) => (
              <BatteryListItem key={battery.batteryNumber} battery={battery} />
            ))}
          </div>
        </div>

        {/* Debug Info */}
        {batteryData.length === 0 && (
          <div className="p-4 text-center">
            <div className="text-sm text-red-500/50">
              Using fallback data - WebSocket not receiving battery data
            </div>
          </div>
        )}
      </div>

      {/* Bottom Control Panel */}
      <div className="fixed bottom-0 left-0 right-0 h-20 bg-black border-t border-red-500/30 flex">
        {/* ACTIVATE Button - Left Half */}
        <button
          onClick={handleActivateClick}
          className="flex-1 bg-black hover:bg-red-500/10 transition-colors flex items-center justify-center border-r border-red-500/30"
        >
          <span className="text-red-500 font-bold text-xl relative" style={{
            position: 'relative',
            top: '20px',
            left: '100px'
          }}>
            ACTIVATE
          </span>
        </button>

        {/* SYSTEM Button - Right Half */}
        <button
          onClick={handleSystemClick}
          className="flex-1 bg-black hover:bg-red-500/10 transition-colors flex items-center justify-center"
        >
          <span className="text-red-500 font-bold text-xl relative" style={{
            position: 'relative',
            top: '20px',
            left: '100px'
          }}>
            SYSTEM
          </span>
        </button>
      </div>
    </>
  );
}
