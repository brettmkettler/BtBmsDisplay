interface BatteryListItemProps {
  batteryNumber: number;
  voltage: number;
  amperage: number;
  chargeLevel: number;
}

export function BatteryListItem({ batteryNumber, voltage, amperage, chargeLevel }: BatteryListItemProps) {
  return (
    <div 
      className="battery-item border-2 border-battery-red rounded-lg p-6 bg-display-black min-h-[120px]"
      data-testid={`battery-item-${batteryNumber}`}
    >
      <div className="grid grid-cols-4 gap-6 items-center h-full">
        {/* Battery Number */}
        <div className="flex justify-center">
          <div 
            className="text-battery-red text-6xl font-bold w-20 text-center"
            data-testid={`battery-number-${batteryNumber}`}
          >
            {batteryNumber}
          </div>
        </div>
        
        {/* Battery Icon */}
        <div className="flex justify-center">
          <div className="w-32 h-12 border-2 border-battery-red bg-display-black relative rounded-sm">
            {/* Battery Fill */}
            <div 
              className="battery-fill h-full rounded-sm transition-all duration-300" 
              style={{ 
                width: `${Math.max(0, Math.min(100, chargeLevel))}%`,
                backgroundColor: chargeLevel > 50 ? '#10B981' : chargeLevel > 20 ? '#F59E0B' : '#EF4444'
              }}
              data-testid={`battery-fill-${batteryNumber}`}
            />
            {/* Battery Terminal */}
            <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-2 h-6 bg-battery-red rounded-r-sm" />
          </div>
        </div>
        
        {/* AMPS Section */}
        <div className="flex flex-col items-center">
          <div className="text-battery-yellow text-xl font-bold mb-1">AMPS</div>
          <div 
            className="text-battery-green text-2xl font-bold font-mono min-w-[80px] text-center"
            data-testid={`battery-amps-${batteryNumber}`}
          >
            {amperage.toFixed(1)}
          </div>
        </div>
        
        {/* VOLTS Section */}
        <div className="flex flex-col items-center">
          <div className="text-battery-yellow text-xl font-bold mb-1">VOLTS</div>
          <div 
            className="text-battery-green text-2xl font-bold font-mono min-w-[80px] text-center"
            data-testid={`battery-volts-${batteryNumber}`}
          >
            {voltage.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}
