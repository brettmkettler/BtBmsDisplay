import { useEffect, useState, useCallback } from 'react';

interface BatteryData {
  track: string;
  voltage: number;
  current: number;
  remaining_capacity: number;
  full_capacity: number;
  soc: number;
  cycles: number;
  cell_voltages: number[];
  last_update: string | null;
  connection_status: string;
}

interface BmsApiResponse {
  left: BatteryData;
  right: BatteryData;
  service_status: string;
  last_poll: string;
}

interface ProcessedBatteryData {
  track: 'left' | 'right';
  trackPosition: number;
  voltage: number;
  amperage: number;
  chargeLevel: number;
}

interface ConnectionStatus {
  left: boolean;
  right: boolean;
}

export function useBmsApi() {
  const [isConnected, setIsConnected] = useState(false);
  const [batteryData, setBatteryData] = useState<ProcessedBatteryData[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ left: false, right: false });
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchBatteryData = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/battery/status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: BmsApiResponse = await response.json();
      console.log('BMS API Response:', data);
      
      // Update connection status
      setConnectionStatus({
        left: data.left.connection_status === 'connected' || data.left.last_update !== null,
        right: data.right.connection_status === 'connected' || data.right.last_update !== null
      });
      
      // Process battery data - convert cell voltages to individual battery entries
      const processedData: ProcessedBatteryData[] = [];
      
      // Process left track cells
      if (data.left.cell_voltages && data.left.cell_voltages.length > 0) {
        console.log('Processing left track cells:', data.left.cell_voltages);
        data.left.cell_voltages.forEach((voltage, index) => {
          // Filter out invalid voltages (like the 65.458V reading)
          if (voltage > 2.0 && voltage < 5.0) {
            processedData.push({
              track: 'left',
              trackPosition: index + 1,
              voltage: voltage,
              amperage: data.left.current,
              chargeLevel: data.left.soc
            });
          }
        });
      }
      
      // Process right track cells
      if (data.right.cell_voltages && data.right.cell_voltages.length > 0) {
        console.log('Processing right track cells:', data.right.cell_voltages);
        data.right.cell_voltages.forEach((voltage, index) => {
          // Filter out invalid voltages (like the 65.458V reading)
          if (voltage > 2.0 && voltage < 5.0) {
            processedData.push({
              track: 'right',
              trackPosition: index + 1,
              voltage: voltage,
              amperage: data.right.current,
              chargeLevel: data.right.soc
            });
          }
        });
      }
      
      console.log('Processed battery data:', processedData);
      setBatteryData(processedData);
      setLastUpdate(new Date());
      setIsConnected(true);
      
    } catch (error) {
      console.error('Failed to fetch battery data:', error);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchBatteryData();
    
    // Set up polling every 5 seconds
    const interval = setInterval(fetchBatteryData, 5000);
    
    return () => clearInterval(interval);
  }, [fetchBatteryData]);

  return {
    isConnected,
    batteryData,
    connectionStatus,
    lastUpdate,
    refetch: fetchBatteryData,
  };
}
