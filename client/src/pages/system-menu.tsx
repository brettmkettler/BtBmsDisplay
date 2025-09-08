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

  const handleBatteryDoorAction = async (action: 'open' | 'close') => {
    setActionLoading(action);
    try {
      const response = await fetch(`http://localhost:5000/door/battery?action=${action}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} battery doors`);
      }
      
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

  return (
    <div className="min-h-screen bg-black text-red-500 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Button
          variant="ghost"
          size="lg"
          onClick={() => setLocation('/')}
          className="text-red-500 hover:bg-red-500/10 border border-red-500/30 hover:border-red-500"
        >
          <ArrowLeft className="mr-2 h-5 w-5" />
          Back to Battery Monitor
        </Button>
        <h1 className="text-3xl font-bold text-red-500">System Menu</h1>
        <div className="w-32" /> {/* Spacer for centering */}
      </div>

      {/* System Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        
        {/* Battery Doors Section */}
        <div className="col-span-full">
          <h2 className="text-xl font-semibold mb-4 text-red-400 border-b border-red-500/30 pb-2">Battery Doors</h2>
        </div>

        {/* Open Battery Doors */}
        <Card className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300 cursor-pointer">
          <CardContent className="p-6">
            <Button
              onClick={() => handleBatteryDoorAction('open')}
              disabled={actionLoading === 'open'}
              className="w-full h-full min-h-[120px] bg-black hover:bg-red-500/10 border-2 border-red-500/50 hover:border-red-400 text-red-500 flex flex-col items-center justify-center space-y-3"
            >
              <DoorOpen className="h-12 w-12 text-red-400" />
              <div className="text-center">
                <div className="text-lg font-semibold text-red-500">Open Battery Doors</div>
                <div className="text-sm text-red-400 mt-1">
                  {actionLoading === 'open' ? 'Opening...' : 'Click to open all battery doors'}
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Close Battery Doors */}
        <Card className="bg-black border-red-500/50 hover:border-red-400 transition-all duration-300 cursor-pointer">
          <CardContent className="p-6">
            <Button
              onClick={() => handleBatteryDoorAction('close')}
              disabled={actionLoading === 'close'}
              className="w-full h-full min-h-[120px] bg-black hover:bg-red-500/10 border-2 border-red-500/50 hover:border-red-400 text-red-500 flex flex-col items-center justify-center space-y-3"
            >
              <DoorClosed className="h-12 w-12 text-red-400" />
              <div className="text-center">
                <div className="text-lg font-semibold text-red-500">Close Battery Doors</div>
                <div className="text-sm text-red-400 mt-1">
                  {actionLoading === 'close' ? 'Closing...' : 'Click to close all battery doors'}
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Placeholder for future system controls */}
        <Card className="bg-black border-red-500/30 opacity-50">
          <CardContent className="p-6">
            <div className="w-full h-full min-h-[120px] flex flex-col items-center justify-center space-y-3 text-red-500/50">
              <div className="h-12 w-12 rounded-full border-2 border-red-500/30 flex items-center justify-center">
                <span className="text-2xl">+</span>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold">More Controls</div>
                <div className="text-sm mt-1">Additional system controls coming soon</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
