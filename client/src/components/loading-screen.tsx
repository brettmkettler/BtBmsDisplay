import { Loader2, Bluetooth } from "lucide-react";
import { ConnectionStatus } from "./connection-status";

interface LoadingScreenProps {
  connectionStatus: {
    left: boolean;
    right: boolean;
  };
  isWebSocketConnected: boolean;
  lastUpdate: Date | null;
}

export function LoadingScreen({ connectionStatus, isWebSocketConnected, lastUpdate }: LoadingScreenProps) {
  const bothConnected = connectionStatus.left && connectionStatus.right;
  const anyConnected = connectionStatus.left || connectionStatus.right;

  if (bothConnected) {
    return null; // Don't show loading screen when both are connected
  }

  return (
    <div className="fixed inset-0 bg-display-black z-50 flex items-center justify-center">
      <div className="bg-display-black border-2 border-battery-red rounded-xl p-8 max-w-2xl w-full mx-4 space-y-6">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3">
            <Bluetooth className="w-8 h-8 text-battery-red" />
            <h2 className="text-2xl font-bold text-battery-red">INITIALIZING BMS CONNECTION</h2>
          </div>
          
          {!isWebSocketConnected ? (
            <p className="text-battery-yellow">Connecting to server...</p>
          ) : !anyConnected ? (
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-battery-red" />
              <p className="text-battery-yellow">Scanning for BMS devices...</p>
            </div>
          ) : (
            <p className="text-battery-yellow">Establishing connections...</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ConnectionStatus
            track="left"
            isConnected={connectionStatus.left}
            isWebSocketConnected={isWebSocketConnected}
            lastUpdate={lastUpdate}
          />
          <ConnectionStatus
            track="right"
            isConnected={connectionStatus.right}
            isWebSocketConnected={isWebSocketConnected}
            lastUpdate={lastUpdate}
          />
        </div>

        <div className="text-center">
          <p className="text-sm text-battery-yellow">
            This may take up to 30 seconds. Ensure BMS devices are powered on and within range.
          </p>
        </div>
      </div>
    </div>
  );
}
