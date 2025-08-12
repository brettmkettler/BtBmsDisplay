interface BatteryListItemProps {
  batteryNumber: number;
  voltage: number;
  amperage: number;
  chargeLevel: number;
}

export function BatteryListItem({ batteryNumber, voltage, amperage, chargeLevel }: BatteryListItemProps) {
  return (
    <div 
      className="border-2 border-battery-red rounded-lg p-4 flex items-center justify-between bg-display-black"
      data-testid={`battery-item-${batteryNumber}`}
    >
      {/* Battery Number */}
      <div 
        className="text-battery-red text-4xl font-bold w-16 text-center"
        data-testid={`battery-number-${batteryNumber}`}
      >
        {batteryNumber}
      </div>
      
      {/* Battery Icon */}
      <div className="flex-shrink-0 mx-4">
        <div className="w-20 h-8 border-2 border-battery-red bg-display-black relative rounded-sm">
          {/* Battery Fill */}
          <div 
            className="battery-fill h-full rounded-sm" 
            style={{ width: `${chargeLevel}%` }}
            data-testid={`battery-fill-${batteryNumber}`}
          />
          {/* Battery Terminal */}
          <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-1 h-3 bg-battery-red rounded-r-sm" />
        </div>
      </div>
      
      {/* AMPS Section */}
      <div className="flex flex-col items-center mx-6">
        <div className="text-battery-yellow text-lg font-bold">AMPS</div>
        <div 
          className="text-battery-green text-2xl font-bold"
          data-testid={`battery-amps-${batteryNumber}`}
        >
          {amperage.toFixed(1)}
        </div>
      </div>
      
      {/* VOLTS Section */}
      <div className="flex flex-col items-center mx-6">
        <div className="text-battery-yellow text-lg font-bold">VOLTS</div>
        <div 
          className="text-battery-green text-2xl font-bold"
          data-testid={`battery-volts-${batteryNumber}`}
        >
          {voltage.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
