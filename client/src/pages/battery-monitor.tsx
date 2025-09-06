import { useState } from "react";
import { useBmsApi } from "@/hooks/use-bms-api";
import { BatteryListItem } from "@/components/battery-list-item";

export default function BatteryMonitor() {
  const { batteryData } = useBmsApi();
  const [selectedTrack, setSelectedTrack] = useState<'left' | 'right'>('left');

  // Filter batteries by selected track
  const filteredBatteries = batteryData.filter(battery => battery.track === selectedTrack);

  return (
    <div className="w-full h-screen flex flex-col bg-display-black text-white font-mono-display">
      {/* Track Selection */}
      <div className="flex justify-center p-4">
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
      
      {/* Battery List - Takes up remaining screen height */}
      <div className="flex-1 p-4 scrollable-container">
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
              <div className="text-xl">No Battery Data Available</div>
              <div className="text-sm mt-2">Waiting for BMS data...</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Bottom 1/5 blank space */}
      <div className="h-[20vh] bg-display-black"></div>
    </div>
  );
}
