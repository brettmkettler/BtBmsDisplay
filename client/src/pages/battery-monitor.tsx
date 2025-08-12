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
      
      {/* Battery List - Takes up 4/5 of screen height */}
      <div className="p-4 scrollable-container">
        <div className="battery-list-container space-y-4" data-testid="battery-container">
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
      
      {/* Bottom 1/5 blank space */}
      <div className="h-[20vh] bg-display-black"></div>
    </div>
  );
}
