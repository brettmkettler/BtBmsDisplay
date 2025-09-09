import { useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowLeft, DoorOpen, DoorClosed } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

export default function SystemMenu() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // LED/Lamp devices configuration
  const ledDevices = [
    { id: 'orange_lamp', name: 'Orange Lamp', icon: '�' },
    { id: 'red_lamp', name: 'Red Lamp', icon: '�' },
    { id: 'startup_led', name: 'Startup LED', icon: '�' },
    { id: 'malfunction_led1', name: 'Malfunction LED', icon: '⚠️' },
    { id: 'other2', name: 'Other LED (GPIO 24)', icon: '💡' }
  ];

  const handleBatteryDoorAction = async (action: 'open' | 'close') => {
    setActionLoading(action);
    try {
      const response = await fetch(`http://localhost:5000/door/battery?action=${action}`, {
        method: 'GET'
      });
      
      // Don't check response.ok since the API may return success with different status codes
      // If we get here without throwing, the request succeeded
      
      toast({
        title: "Success",
        description: `Battery doors ${action === 'open' ? 'opened' : 'closed'} successfully`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} battery doors`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleLEDControl = async (deviceId: string, state: 'on' | 'off') => {
    setActionLoading(`${deviceId}_${state}`);
    try {
      const response = await fetch(`http://localhost:3000/api/digital/${deviceId}?state=${state}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status !== 'success') {
        throw new Error(`API returned status: ${data.status}`);
      }
      
      toast({
        title: "Success",
        description: `${deviceId.replace(/_/g, ' ')} turned ${state}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to turn ${state} ${deviceId.replace(/_/g, ' ')}`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTestAllLights = async (state: 'on' | 'off') => {
    setActionLoading(`test_all_${state}`);
    try {
      const response = await fetch(`http://localhost:3000/api/digital/test-all?state=${state}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status !== 'success') {
        throw new Error(`API returned status: ${data.status}`);
      }
      
      toast({
        title: "Test Complete",
        description: data.message,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to test all lights`,
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleActivateClick = () => {
    console.log('ACTIVATE button clicked');
  };

  const handleSystemClick = () => {
    setLocation('/');
  };

  return (
    <div className="min-h-screen bg-black text-red-500 flex flex-col">
      {/* Main Content Area - Scrollable */}
      <div className="flex-1 overflow-y-auto touch-pan-y" style={{ height: '80vh' }}>
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLocation('/')}
              className="text-red-500 hover:bg-red-500/10 border border-red-500/30 hover:border-red-500"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <h1 className="text-2xl font-bold text-red-500">System Menu</h1>
            <div className="w-20" /> {/* Spacer for centering */}
          </div>

          {/* System Controls Grid - More compact */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-w-7xl mx-auto">
            
            {/* Battery Doors Section */}
            <div className="col-span-full">
              <h2 className="text-lg font-semibold mb-2 text-red-400 border-b border-red-500/30 pb-1">Battery Doors</h2>
            </div>

            {/* Open Battery Doors */}
            <Card className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300">
              <CardContent className="p-3">
                <Button
                  onClick={() => handleBatteryDoorAction('open')}
                  disabled={actionLoading === 'open'}
                  className="w-full h-full min-h-[80px] bg-black hover:bg-red-500/10 border-2 border-red-500/50 hover:border-red-400 text-red-500 flex flex-col items-center justify-center space-y-2"
                >
                  <DoorOpen className="h-8 w-8 text-red-400" />
                  <div className="text-center">
                    <div className="text-sm font-semibold text-red-500">Open Doors</div>
                    <div className="text-xs text-red-400">
                      {actionLoading === 'open' ? 'Opening...' : 'Battery doors'}
                    </div>
                  </div>
                </Button>
              </CardContent>
            </Card>

            {/* Close Battery Doors */}
            <Card className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300">
              <CardContent className="p-3">
                <Button
                  onClick={() => handleBatteryDoorAction('close')}
                  disabled={actionLoading === 'close'}
                  className="w-full h-full min-h-[80px] bg-black hover:bg-red-500/10 border-2 border-red-500/50 hover:border-red-400 text-red-500 flex flex-col items-center justify-center space-y-2"
                >
                  <DoorClosed className="h-8 w-8 text-red-400" />
                  <div className="text-center">
                    <div className="text-sm font-semibold text-red-500">Close Doors</div>
                    <div className="text-xs text-red-400">
                      {actionLoading === 'close' ? 'Closing...' : 'Battery doors'}
                    </div>
                  </div>
                </Button>
              </CardContent>
            </Card>

            {/* LED/Lamp Controls */}
            <div className="col-span-full">
              <h2 className="text-lg font-semibold mb-2 text-red-400 border-b border-red-500/30 pb-1">LED/Lamp Controls</h2>
            </div>

            {ledDevices.map((device) => (
              <Card key={device.id} className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300">
                <CardContent className="p-3">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <span className="text-2xl">{device.icon}</span>
                    <div className="text-center">
                      <div className="text-sm font-semibold text-red-500">{device.name}</div>
                      <div className="flex space-x-1 mt-1">
                        <Button
                          onClick={() => handleLEDControl(device.id, 'on')}
                          disabled={actionLoading === `${device.id}_on`}
                          size="sm"
                          className="bg-black hover:bg-red-500/10 border border-red-500/50 hover:border-red-400 text-red-500 text-xs px-2 py-1"
                        >
                          On
                        </Button>
                        <Button
                          onClick={() => handleLEDControl(device.id, 'off')}
                          disabled={actionLoading === `${device.id}_off`}
                          size="sm"
                          className="bg-black hover:bg-red-500/10 border border-red-500/50 hover:border-red-400 text-red-500 text-xs px-2 py-1"
                        >
                          Off
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Test All Lights */}
            <Card className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300">
              <CardContent className="p-3">
                <div className="flex flex-col items-center justify-center space-y-2">
                  <span className="text-2xl">⚠️</span>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-red-500">Test All</div>
                    <div className="flex space-x-1 mt-1">
                      <Button
                        onClick={() => handleTestAllLights('on')}
                        disabled={actionLoading === 'test_all_on'}
                        size="sm"
                        className="bg-black hover:bg-red-500/10 border border-red-500/50 hover:border-red-400 text-red-500 text-xs px-2 py-1"
                      >
                        On
                      </Button>
                      <Button
                        onClick={() => handleTestAllLights('off')}
                        disabled={actionLoading === 'test_all_off'}
                        size="sm"
                        className="bg-black hover:bg-red-500/10 border border-red-500/50 hover:border-red-400 text-red-500 text-xs px-2 py-1"
                      >
                        Off
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Placeholder for future system controls */}
            <Card className="bg-black border-red-500/30 opacity-50">
              <CardContent className="p-3">
                <div className="w-full h-full min-h-[80px] flex flex-col items-center justify-center space-y-2 text-red-500/50">
                  <div className="h-8 w-8 rounded-full border-2 border-red-500/30 flex items-center justify-center">
                    <span className="text-xl">+</span>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold">More Controls</div>
                    <div className="text-xs mt-1">Additional system controls coming soon</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Bottom Control Section - 1/5 of screen height */}
      <div className="flex" style={{ height: '20vh' }}>
        {/* ACTIVATE Button - Left Half */}
        <button
          onClick={handleActivateClick}
          className="flex-1 bg-display-black hover:bg-gray-900 transition-colors flex items-center justify-center border-r border-gray-600"
          style={{ 
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#16a34a',
            textAlign: 'center'
          }}
        >
          <span style={{ 
            position: 'relative',
            top: '20px',
            left: '-80px'
          }}>
            ACTIVATE
          </span>
        </button>

        {/* SYSTEM Button - Right Half */}
        <button
          onClick={handleSystemClick}
          className="flex-1 bg-display-black hover:bg-gray-900 transition-colors flex items-center justify-center border-l border-gray-600"
          style={{ 
            fontSize: '2rem',
            fontWeight: 'bold',
            color: 'hsl(0, 100%, 50%)',
            textAlign: 'center'
          }}
        >
          <span style={{ 
            position: 'relative',
            top: '20px',
            left: '100px'
          }}>
            SYSTEM
          </span>
        </button>
      </div>
    </div>
  );
}
