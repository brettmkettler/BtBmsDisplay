import { useState, useEffect } from 'react';

interface ScreenState {
  isScreenOn: boolean;
}

export function useScreenControl() {
  const [isScreenOn, setIsScreenOn] = useState(true);

  // Listen for screen control messages via WebSocket or polling
  useEffect(() => {
    const handleScreenMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'screen_control') {
          setIsScreenOn(data.isScreenOn);
        }
      } catch (error) {
        // Ignore invalid messages
      }
    };

    // Connect to WebSocket for screen control updates
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    ws.addEventListener('message', handleScreenMessage);

    return () => {
      ws.close();
    };
  }, []);

  return {
    isScreenOn,
    setIsScreenOn
  };
}
