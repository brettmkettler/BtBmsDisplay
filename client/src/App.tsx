import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ScreenOverlay } from "@/components/screen-overlay";
import { useScreenControl } from "@/hooks/use-screen-control";
import BatteryMonitor from "@/pages/battery-monitor";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={BatteryMonitor} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const { isScreenOn } = useScreenControl();

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
        <ScreenOverlay isVisible={!isScreenOn} />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
