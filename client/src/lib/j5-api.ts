// J5 Console API client for integration with j5_console.py
const J5_API_BASE = 'http://localhost:5000';

export interface SystemStatus {
  current_state: string;
  uptime: number;
  gpio_status: string;
}

export interface ServoInfo {
  name: string;
  current_angle: number;
  min_angle: number;
  max_angle: number;
  status: string;
}

export interface DoorStatus {
  status: string;
  message: string;
}

export const j5Api = {
  // System status
  getSystemStatus: async (): Promise<SystemStatus> => {
    const response = await fetch(`${J5_API_BASE}/api/system/status`);
    if (!response.ok) throw new Error('Failed to fetch system status');
    return response.json();
  },

  // Door control
  controlDoor: async (door: string, action: string): Promise<DoorStatus> => {
    const response = await fetch(`${J5_API_BASE}/api/door/${door}?action=${action}`, { 
      method: 'POST' 
    });
    if (!response.ok) throw new Error(`Failed to control door ${door}`);
    return response.json();
  },

  // LED control
  controlLED: async (led: string, state: string): Promise<{ status: string }> => {
    const response = await fetch(`${J5_API_BASE}/api/digital/${led}?state=${state}`, { 
      method: 'POST' 
    });
    if (!response.ok) throw new Error(`Failed to control LED ${led}`);
    return response.json();
  },

  // Servo control
  controlServo: async (servo: string, angle: number): Promise<{ status: string }> => {
    const response = await fetch(`${J5_API_BASE}/api/servo/${servo}?angle=${angle}`, { 
      method: 'POST' 
    });
    if (!response.ok) throw new Error(`Failed to control servo ${servo}`);
    return response.json();
  },

  // Get servo info
  getServoInfo: async (servo: string): Promise<ServoInfo> => {
    const response = await fetch(`${J5_API_BASE}/api/servo/${servo}/info`);
    if (!response.ok) throw new Error(`Failed to get servo info for ${servo}`);
    return response.json();
  },

  // State control
  setState: async (mode: string): Promise<{ status: string; current_state: string }> => {
    const response = await fetch(`${J5_API_BASE}/api/state/?mode=${mode}`, { 
      method: 'POST' 
    });
    if (!response.ok) throw new Error(`Failed to set state to ${mode}`);
    return response.json();
  },

  // Run activation sequence
  runActivationSequence: async (): Promise<{ status: string }> => {
    const response = await fetch(`${J5_API_BASE}/api/system/sequence`);
    if (!response.ok) throw new Error('Failed to run activation sequence');
    return response.json();
  },

  // Battery door control
  controlBatteryDoors: async (action: string): Promise<DoorStatus> => {
    const response = await fetch(`${J5_API_BASE}/api/door/battery?action=${action}`, { 
      method: 'POST' 
    });
    if (!response.ok) throw new Error(`Failed to control battery doors`);
    return response.json();
  }
};

// Available door names
export const DOORS = {
  LEFT: 'left_door',
  CONSOLE: 'console_door', 
  RIGHT: 'right_door'
} as const;

// Available LED names
export const LEDS = {
  ORANGE_LAMP: 'orange_lamp',
  RED_LAMP: 'red_lamp',
  STARTUP: 'startup_led',
  MALFUNCTION: 'malfunction_led1'
} as const;

// Available states
export const STATES = {
  ACTIVATED: 'activated',
  DEACTIVATED: 'deactivated',
  MALFUNCTION: 'malfunction'
} as const;
