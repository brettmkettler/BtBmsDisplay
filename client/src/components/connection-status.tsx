import { Bluetooth, BluetoothConnected, AlertTriangle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ConnectionStatusProps {
  track: 'left' | 'right';
  isConnected: boolean;
  isWebSocketConnected: boolean;
  lastUpdate: Date | null;
}

export function ConnectionStatus({ track, isConnected, isWebSocketConnected, lastUpdate }: ConnectionStatusProps) {
  const trackName = track === 'left' ? 'LEFT TRACK' : 'RIGHT TRACK';
  const macAddress = track === 'left' ? 'A4:C1:38:7C:2D:F0' : 'E0:9F:2A:E4:94:1D';
  
  const getStatusColor = () => {
    if (!isWebSocketConnected) return 'text-battery-red opacity-50';
    if (isConnected) return 'text-battery-red';
    return 'text-battery-red opacity-75';
  };

  const getStatusIcon = () => {
    if (!isWebSocketConnected) {
      return <AlertTriangle className="w-5 h-5 text-battery-red opacity-50" />;
    }
    if (isConnected) {
      return <BluetoothConnected className="w-5 h-5 text-battery-red" />;
    }
    return <Loader2 className="w-5 h-5 text-battery-red opacity-75 animate-spin" />;
  };

  const getStatusText = () => {
    if (!isWebSocketConnected) return 'Server Disconnected';
    if (isConnected) return 'Connected';
    return 'Connecting...';
  };

  const getLastUpdateText = () => {
    if (!lastUpdate) return 'No data received';
    const now = new Date();
    const diff = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);
    
    if (diff < 5) return 'Live';
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  return (
    <div className="bg-display-black border border-battery-red rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-battery-red">{trackName} BMS</h3>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
      </div>
      
      <div className="space-y-2 text-sm text-battery-red opacity-75">
        <div className="flex justify-between">
          <span>MAC Address:</span>
          <span className="font-mono text-xs">{macAddress}</span>
        </div>
        <div className="flex justify-between">
          <span>Last Update:</span>
          <span className={lastUpdate && getLastUpdateText() === 'Live' ? 'text-battery-red' : 'text-battery-red opacity-50'}>
            {getLastUpdateText()}
          </span>
        </div>
      </div>

      {!isWebSocketConnected && (
        <Alert className="border-battery-red bg-display-black">
          <AlertTriangle className="h-4 w-4 text-battery-red" />
          <AlertDescription className="text-battery-red">
            Server connection lost. Check if the BMS service is running.
          </AlertDescription>
        </Alert>
      )}

      {isWebSocketConnected && !isConnected && (
        <Alert className="border-battery-red bg-display-black">
          <Bluetooth className="h-4 w-4 text-battery-red" />
          <AlertDescription className="text-battery-red opacity-75">
            Scanning for BMS device. Ensure the BMS is powered and within range.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
