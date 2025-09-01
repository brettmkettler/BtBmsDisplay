import { useState } from "react";
import { useWebSocket } from "@/hooks/use-websocket";
import { BatteryListItem } from "@/components/battery-list-item";
import { LoadingScreen } from "@/components/loading-screen";
import { ConnectionStatus } from "@/components/connection-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Bluetooth } from "lucide-react";
import { J5ControlPanel } from "@/components/j5-control-panel";
import { Button } from "@/components/ui/button";
import { Settings, Battery, ChevronLeft, ChevronRight } from "lucide-react";

type Track = 'left' | 'right';

export default function BatteryMonitor() {
  const { isConnected, batteryData, connectionStatus, lastUpdate } = useWebSocket();
  const [showControls, setShowControls] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<Track>('left');

  // Show loading screen if not both BMS devices are connected
  const bothConnected = connectionStatus.left && connectionStatus.right;
  const showLoadingScreen = !bothConnected;

  // Filter batteries by current track
  const trackBatteries = batteryData.filter(battery => 
    battery.track === currentTrack || 
    // Fallback for batteries without track info - use battery number
    (!battery.track && (
      (currentTrack === 'left' && battery.batteryNumber <= 4) ||
      (currentTrack === 'right' && battery.batteryNumber > 4)
    ))
  );

  const switchTrack = (track: Track) => {
    setCurrentTrack(track);
  };

  const getTrackDisplayName = (track: Track) => {
    return track === 'left' ? 'LEFT TRACK' : 'RIGHT TRACK';
  };

  return (
    <div className="w-full h-screen flex bg-display-black text-white font-mono-display">
      {/* Loading Screen Overlay */}
      {showLoadingScreen && (
        <LoadingScreen
          connectionStatus={connectionStatus}
          isWebSocketConnected={isConnected}
          lastUpdate={lastUpdate}
        />
      )}

      {/* Main Battery Display - Left side */}
      <div className="flex-1 flex flex-col">
        {/* Connection Status Indicator (minimal) */}
        {!isConnected && (
          <div className="bg-battery-red text-white text-center p-2 text-sm">
            Connection Lost - Attempting to Reconnect...
          </div>
        )}
        
        {/* Header with track navigation and controls */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-battery-yellow">
              {getTrackDisplayName(currentTrack)}
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Track Navigation Arrows */}
            <div className="flex items-center gap-2">
              <Button
                onClick={() => switchTrack('left')}
                variant={currentTrack === 'left' ? 'default' : 'outline'}
                size="lg"
                className="flex items-center gap-2 min-w-[60px] h-12"
                disabled={currentTrack === 'left'}
              >
                <ChevronLeft className="w-6 h-6" />
              </Button>
              <Button
                onClick={() => switchTrack('right')}
                variant={currentTrack === 'right' ? 'default' : 'outline'}
                size="lg"
                className="flex items-center gap-2 min-w-[60px] h-12"
                disabled={currentTrack === 'right'}
              >
                <ChevronRight className="w-6 h-6" />
              </Button>
            </div>
          </div>
        </div>
        
        {/* Battery List for Current Track - Takes 5/6 of remaining space */}
        <div className="flex-1 p-6 scrollable-container overflow-y-auto" style={{ height: 'calc(83.33vh - 80px)' }}>
          <div className="battery-list-container space-y-6" data-testid="battery-container">
            {trackBatteries.length > 0 ? (
              trackBatteries
                .sort((a, b) => (a.trackPosition || a.batteryNumber) - (b.trackPosition || b.batteryNumber))
                .map((battery) => (
                  <BatteryListItem
                    key={battery.batteryNumber}
                    batteryNumber={battery.trackPosition || (battery.batteryNumber > 4 ? battery.batteryNumber - 4 : battery.batteryNumber)}
                    voltage={battery.voltage}
                    amperage={battery.amperage}
                    chargeLevel={battery.chargeLevel}
                  />
                ))
            ) : (
              <div className="text-center text-battery-yellow py-8">
                <div className="text-xl">Initializing {getTrackDisplayName(currentTrack)}...</div>
                <div className="text-sm mt-2">Connecting to BMS...</div>
              </div>
            )}
          </div>
        </div>
        
        {/* Divider */}
        <div className="border-t border-gray-700"></div>
        
        {/* Bottom Black Section - 1/6 of screen height (configurable) */}
        <div className="bg-display-black flex items-center justify-center" style={{ height: '30.67vh' }}>
          {/* Track Indicator */}
          <div className="flex gap-2">
            <div className={`w-3 h-3 rounded-full ${currentTrack === 'left' ? 'bg-battery-yellow' : 'bg-gray-600'}`}></div>
            <div className={`w-3 h-3 rounded-full ${currentTrack === 'right' ? 'bg-battery-yellow' : 'bg-gray-600'}`}></div>
          </div>
        </div>
      </div>
      
      {/* Control Panel - Right side (collapsible) */}
      {showControls && (
        <div className="w-80 border-l border-gray-700 bg-gray-900/30 p-4 overflow-y-auto">
          <J5ControlPanel />
        </div>
      )}
    </div>
  );
}
