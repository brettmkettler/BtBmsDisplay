import { useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowLeft, DoorOpen, DoorClosed } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useJ5System } from '@/hooks/use-j5-system';
import { useToast } from '@/hooks/use-toast';

export default function SystemMenu() {
  const [, setLocation] = useLocation();
  const { controlBatteryDoors, loading } = useJ5System();
  const { toast } = useToast();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleBatteryDoorAction = async (action: 'open' | 'close') => {
    setActionLoading(action);
    try {
      await controlBatteryDoors(action);
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Button
          variant="ghost"
          size="lg"
          onClick={() => setLocation('/')}
          className="text-white hover:bg-white/10"
        >
          <ArrowLeft className="mr-2 h-5 w-5" />
          Back to Battery Monitor
        </Button>
        <h1 className="text-3xl font-bold">System Menu</h1>
        <div className="w-32" /> {/* Spacer for centering */}
      </div>

      {/* System Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        
        {/* Battery Doors Section */}
        <div className="col-span-full">
          <h2 className="text-xl font-semibold mb-4 text-blue-300">Battery Doors</h2>
        </div>

        {/* Open Battery Doors */}
        <Card className="bg-gradient-to-br from-green-800/20 to-green-900/20 border-green-500/30 hover:border-green-400/50 transition-all duration-300 cursor-pointer">
          <CardContent className="p-6">
            <Button
              onClick={() => handleBatteryDoorAction('open')}
              disabled={loading || actionLoading === 'open'}
              className="w-full h-full min-h-[120px] bg-transparent hover:bg-green-500/20 border-2 border-green-500/50 hover:border-green-400 text-white flex flex-col items-center justify-center space-y-3"
            >
              <DoorOpen className="h-12 w-12 text-green-400" />
              <div className="text-center">
                <div className="text-lg font-semibold">Open Battery Doors</div>
                <div className="text-sm text-green-300 mt-1">
                  {actionLoading === 'open' ? 'Opening...' : 'Click to open all battery doors'}
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Close Battery Doors */}
        <Card className="bg-gradient-to-br from-red-800/20 to-red-900/20 border-red-500/30 hover:border-red-400/50 transition-all duration-300 cursor-pointer">
          <CardContent className="p-6">
            <Button
              onClick={() => handleBatteryDoorAction('close')}
              disabled={loading || actionLoading === 'close'}
              className="w-full h-full min-h-[120px] bg-transparent hover:bg-red-500/20 border-2 border-red-500/50 hover:border-red-400 text-white flex flex-col items-center justify-center space-y-3"
            >
              <DoorClosed className="h-12 w-12 text-red-400" />
              <div className="text-center">
                <div className="text-lg font-semibold">Close Battery Doors</div>
                <div className="text-sm text-red-300 mt-1">
                  {actionLoading === 'close' ? 'Closing...' : 'Click to close all battery doors'}
                </div>
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Placeholder for future system controls */}
        <Card className="bg-gradient-to-br from-slate-800/20 to-slate-900/20 border-slate-500/30 opacity-50">
          <CardContent className="p-6">
            <div className="w-full h-full min-h-[120px] flex flex-col items-center justify-center space-y-3 text-slate-400">
              <div className="h-12 w-12 rounded-full bg-slate-600/30 flex items-center justify-center">
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
