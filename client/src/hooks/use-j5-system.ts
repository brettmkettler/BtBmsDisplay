import { useState, useEffect } from 'react';
import { j5Api, type SystemStatus, STATES } from '@/lib/j5-api';

export function useJ5System() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch system status
  const fetchSystemStatus = async () => {
    try {
      const status = await j5Api.getSystemStatus();
      setSystemStatus(status);
      setIsConnected(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to J5 Console');
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  };

  // Control functions
  const controlDoor = async (door: string, action: string) => {
    try {
      const result = await j5Api.controlDoor(door, action);
      await fetchSystemStatus(); // Refresh status
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Door control failed');
      throw err;
    }
  };

  const controlLED = async (led: string, state: string) => {
    try {
      const result = await j5Api.controlLED(led, state);
      await fetchSystemStatus(); // Refresh status
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'LED control failed');
      throw err;
    }
  };

  const setState = async (mode: string) => {
    try {
      const result = await j5Api.setState(mode);
      await fetchSystemStatus(); // Refresh status
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'State change failed');
      throw err;
    }
  };

  const runActivationSequence = async () => {
    try {
      const result = await j5Api.runActivationSequence();
      await fetchSystemStatus(); // Refresh status
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Activation sequence failed');
      throw err;
    }
  };

  const controlBatteryDoors = async (action: string) => {
    try {
      const result = await j5Api.controlBatteryDoors(action);
      await fetchSystemStatus(); // Refresh status
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Battery door control failed');
      throw err;
    }
  };

  // Poll system status every 5 seconds
  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return {
    systemStatus,
    isConnected,
    loading,
    error,
    controlDoor,
    controlLED,
    setState,
    runActivationSequence,
    controlBatteryDoors,
    refreshStatus: fetchSystemStatus,
    // Helper functions
    isActivated: systemStatus?.current_state === STATES.ACTIVATED,
    isMalfunction: systemStatus?.current_state === STATES.MALFUNCTION,
    isDeactivated: systemStatus?.current_state === STATES.DEACTIVATED,
  };
}
