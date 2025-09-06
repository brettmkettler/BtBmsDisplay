import { useEffect, useRef, useState, useCallback } from 'react';
import { type BatteryUpdate } from '@shared/schema';

interface ConnectionStatus {
  left: boolean;
  right: boolean;
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [batteryData, setBatteryData] = useState<BatteryUpdate['batteries']>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ left: false, right: false });
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as BatteryUpdate;
          if (data.type === 'battery_update') {
            setBatteryData(data.batteries);
            setLastUpdate(new Date());
            
            // Update BMS connection status if provided
            if (data.connectionStatus) {
              setConnectionStatus(data.connectionStatus);
            }
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) {
            connect();
          }
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    batteryData,
    connectionStatus,
    lastUpdate,
    reconnect: connect,
  };
}
