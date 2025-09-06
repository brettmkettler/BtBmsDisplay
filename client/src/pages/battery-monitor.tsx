import { useState } from "react";
import { useBmsApi } from "@/hooks/use-bms-api";
import { BatteryListItem } from "@/components/battery-list-item";
import { LoadingScreen } from "@/components/loading-screen";
import { ConnectionStatus } from "@/components/connection-status";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, Bluetooth } from "lucide-react";

export default function BatteryMonitor() {
  const { isConnected, batteryData } = useBmsApi();
  const [selectedTrack, setSelectedTrack] = useState<'left' | 'right'>('left');

  // Filter batteries by selected track
  const filteredBatteries = batteryData.filter(battery => battery.track === selectedTrack);

  return (
    <div className="w-full h-screen flex flex-col bg-display-black text-white font-mono-display">
      {/* Connection Status Indicator (minimal) */}
      {!isConnected && (
        <div className="bg-battery-red text-white text-center p-2 text-sm">
          Connection Lost - Attempting to Reconnect...
        </div>
      )}
      
      {/* Battery List - Takes up 4/5 of screen height */}
      <div className="p-4 scrollable-container">
        <div className="battery-list-container space-y-4" data-testid="battery-container">
          {filteredBatteries.length > 0 ? (
            filteredBatteries
              .sort((a, b) => a.trackPosition - b.trackPosition)
              .map((battery) => (
                <BatteryListItem
                  key={`${battery.track}-${battery.trackPosition}`}
                  batteryNumber={battery.trackPosition}
                  voltage={battery.voltage}
                  amperage={battery.amperage}
                  chargeLevel={battery.chargeLevel}
                />
              ))
          ) : (
            <div className="text-center text-battery-yellow py-8">
              <div className="text-xl">Initializing Battery Monitor...</div>
              <div className="text-sm mt-2">Connecting to BMS...</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Bottom 1/5 blank space */}
      <div className="h-[20vh] bg-display-black"></div>
    </div>
  );
}
