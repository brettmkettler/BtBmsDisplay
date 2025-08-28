import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useJ5System } from '@/hooks/use-j5-system';
import { DOORS, LEDS, STATES } from '@/lib/j5-api';
import { 
  Power, 
  DoorOpen, 
  DoorClosed, 
  Lightbulb, 
  AlertTriangle,
  CheckCircle,
  XCircle 
} from 'lucide-react';

export function J5ControlPanel() {
  const {
    systemStatus,
    isConnected,
    loading,
    error,
    controlDoor,
    controlLED,
    setState,
    runActivationSequence,
    controlBatteryDoors,
    isActivated,
    isMalfunction,
    isDeactivated
  } = useJ5System();

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleAction = async (action: () => Promise<any>, actionName: string) => {
    setActionLoading(actionName);
    try {
      await action();
    } catch (err) {
      console.error(`Action ${actionName} failed:`, err);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = () => {
    if (!isConnected) return 'bg-gray-500';
    if (isMalfunction) return 'bg-red-500';
    if (isActivated) return 'bg-green-500';
    return 'bg-yellow-500';
  };

  const getStatusText = () => {
    if (!isConnected) return 'DISCONNECTED';
    if (loading) return 'LOADING...';
    return systemStatus?.current_state?.toUpperCase() || 'UNKNOWN';
  };

  if (error && !isConnected) {
    return (
      <Card className="bg-red-900/20 border-red-500">
        <CardHeader>
          <CardTitle className="text-red-400 flex items-center gap-2">
            <XCircle className="w-5 h-5" />
            J5 Console Connection Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-300">{error}</p>
          <p className="text-sm text-gray-400 mt-2">
            Ensure j5_console.py is running on port 5000
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* System Status */}
      <Card className="bg-gray-900/50 border-gray-700">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Power className="w-5 h-5" />
              J5 Console Status
            </span>
            <Badge className={`${getStatusColor()} text-white`}>
              {getStatusText()}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {systemStatus && (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Uptime:</span>
                <span className="ml-2">{Math.floor(systemStatus.uptime / 60)}m</span>
              </div>
              <div>
                <span className="text-gray-400">GPIO:</span>
                <span className="ml-2">{systemStatus.gpio_status}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Control */}
      <Card className="bg-gray-900/50 border-gray-700">
        <CardHeader className="pb-3">
          <CardTitle>System Control</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => setState(STATES.ACTIVATED), 'activate')}
              disabled={actionLoading !== null || isActivated}
              className="bg-green-600 hover:bg-green-700"
            >
              {actionLoading === 'activate' ? 'Activating...' : 'Activate'}
            </Button>
            <Button
              onClick={() => handleAction(() => setState(STATES.DEACTIVATED), 'deactivate')}
              disabled={actionLoading !== null || isDeactivated}
              variant="outline"
            >
              {actionLoading === 'deactivate' ? 'Deactivating...' : 'Deactivate'}
            </Button>
          </div>
          <Button
            onClick={() => handleAction(runActivationSequence, 'sequence')}
            disabled={actionLoading !== null}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {actionLoading === 'sequence' ? 'Running Sequence...' : 'Run Activation Sequence'}
          </Button>
        </CardContent>
      </Card>

      {/* Door Control */}
      <Card className="bg-gray-900/50 border-gray-700">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <DoorOpen className="w-5 h-5" />
            Door Control
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => controlDoor(DOORS.CONSOLE, 'open'), 'console-open')}
              disabled={actionLoading !== null}
              size="sm"
            >
              {actionLoading === 'console-open' ? '...' : 'Console Open'}
            </Button>
            <Button
              onClick={() => handleAction(() => controlDoor(DOORS.CONSOLE, 'close'), 'console-close')}
              disabled={actionLoading !== null}
              variant="outline"
              size="sm"
            >
              {actionLoading === 'console-close' ? '...' : 'Console Close'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => controlDoor(DOORS.LEFT, 'open'), 'left-open')}
              disabled={actionLoading !== null}
              size="sm"
            >
              {actionLoading === 'left-open' ? '...' : 'Left Open'}
            </Button>
            <Button
              onClick={() => handleAction(() => controlDoor(DOORS.RIGHT, 'open'), 'right-open')}
              disabled={actionLoading !== null}
              size="sm"
            >
              {actionLoading === 'right-open' ? '...' : 'Right Open'}
            </Button>
          </div>
          <Button
            onClick={() => handleAction(() => controlBatteryDoors('toggle'), 'battery-toggle')}
            disabled={actionLoading !== null}
            className="w-full"
            variant="outline"
          >
            {actionLoading === 'battery-toggle' ? 'Toggling...' : 'Toggle Battery Doors'}
          </Button>
        </CardContent>
      </Card>

      {/* LED Control */}
      <Card className="bg-gray-900/50 border-gray-700">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            LED Control
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.ORANGE_LAMP, 'on'), 'orange-on')}
              disabled={actionLoading !== null}
              className="bg-orange-600 hover:bg-orange-700"
              size="sm"
            >
              {actionLoading === 'orange-on' ? '...' : 'Orange On'}
            </Button>
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.ORANGE_LAMP, 'off'), 'orange-off')}
              disabled={actionLoading !== null}
              variant="outline"
              size="sm"
            >
              {actionLoading === 'orange-off' ? '...' : 'Orange Off'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.RED_LAMP, 'on'), 'red-on')}
              disabled={actionLoading !== null}
              className="bg-red-600 hover:bg-red-700"
              size="sm"
            >
              {actionLoading === 'red-on' ? '...' : 'Red On'}
            </Button>
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.RED_LAMP, 'off'), 'red-off')}
              disabled={actionLoading !== null}
              variant="outline"
              size="sm"
            >
              {actionLoading === 'red-off' ? '...' : 'Red Off'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.STARTUP, 'on'), 'startup-on')}
              disabled={actionLoading !== null}
              className="bg-blue-600 hover:bg-blue-700"
              size="sm"
            >
              {actionLoading === 'startup-on' ? '...' : 'Startup On'}
            </Button>
            <Button
              onClick={() => handleAction(() => controlLED(LEDS.MALFUNCTION, 'on'), 'malfunction-on')}
              disabled={actionLoading !== null}
              className="bg-yellow-600 hover:bg-yellow-700"
              size="sm"
            >
              {actionLoading === 'malfunction-on' ? '...' : 'Malfunction On'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
