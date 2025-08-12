import { BatteryListItem } from "@/components/battery-list-item";
import { useWebSocket } from "@/hooks/use-websocket";

export default function BatteryMonitor() {
  const { isConnected, batteryData } = useWebSocket();

  return (
    <div className="w-full h-screen flex flex-col bg-display-black text-white font-mono-display">
      {/* Connection Status Indicator (minimal) */}
      {!isConnected && (
        <div className="bg-battery-red text-white text-center p-2 text-sm">
          Connection Lost - Attempting to Reconnect...
        </div>
      )}
      
      {/* Battery List */}
      <div className="flex-1 p-4 scrollable-container">
        <div className="space-y-4" data-testid="battery-container">
          {batteryData.length > 0 ? (
            batteryData
              .sort((a, b) => a.batteryNumber - b.batteryNumber)
              .map((battery) => (
                <BatteryListItem
                  key={battery.batteryNumber}
                  batteryNumber={battery.batteryNumber}
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
    </div>
  );
}
