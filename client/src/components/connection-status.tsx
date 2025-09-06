import { CheckCircle, XCircle, Loader2, Bluetooth } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ConnectionStatusProps {
  track: 'left' | 'right';
  isConnected: boolean;
  isWebSocketConnected: boolean;
  lastUpdate: Date | null;
}

const BMS_MAC_ADDRESSES = {
  left: 'A4:C1:38:7C:2D:F0',
  right: 'E0:9F:2A:E4:94:1D'
};

export function ConnectionStatus({ track, isConnected, isWebSocketConnected, lastUpdate }: ConnectionStatusProps) {
  const macAddress = BMS_MAC_ADDRESSES[track];
  
  const getStatusIcon = () => {
    if (!isWebSocketConnected) {
      return <XCircle className="w-6 h-6 text-battery-red" />;
    }
    
    if (isConnected) {
      return <CheckCircle className="w-6 h-6 text-battery-green" />;
    }
    
    return <Loader2 className="w-6 h-6 animate-spin text-battery-yellow" />;
  };

  const getStatusText = () => {
    if (!isWebSocketConnected) {
      return 'Server Disconnected';
    }
    
    if (isConnected) {
      return 'Connected';
    }
    
    return 'Connecting...';
  };

  const getStatusColor = () => {
    if (!isWebSocketConnected || !isConnected) {
      return 'text-battery-red';
    }
    
    return 'text-battery-green';
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Never';
    
    const now = new Date();
    const diff = now.getTime() - lastUpdate.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) {
      return `${seconds}s ago`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)}m ago`;
    } else {
      return lastUpdate.toLocaleTimeString();
    }
  };

  return (
    <div className="bg-display-black border border-battery-red rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bluetooth className="w-5 h-5 text-battery-red" />
          <span className="font-semibold text-battery-red uppercase">
            {track} BMS
          </span>
        </div>
        {getStatusIcon()}
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-battery-yellow">Status:</span>
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-battery-yellow">MAC:</span>
          <span className="text-sm font-mono text-battery-yellow">
            {macAddress}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-battery-yellow">Last Update:</span>
          <span className="text-sm text-battery-yellow">
            {formatLastUpdate()}
          </span>
        </div>
      </div>

      {!isWebSocketConnected && (
        <Alert className="border-battery-red/50 bg-battery-red/10">
          <XCircle className="h-4 w-4" />
          <AlertDescription className="text-battery-red">
            Server connection lost. Check if the BMS service is running.
          </AlertDescription>
        </Alert>
      )}

      {isWebSocketConnected && !isConnected && (
        <Alert className="border-battery-yellow/50 bg-battery-yellow/10">
          <Bluetooth className="h-4 w-4" />
          <AlertDescription className="text-battery-yellow">
            Scanning for BMS device. Ensure the BMS is powered and within range.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
