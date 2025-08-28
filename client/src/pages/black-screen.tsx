import { useLocation } from "wouter";

export default function BlackScreen() {
  const [, setLocation] = useLocation();

  const handleScreenOn = async () => {
    try {
      await fetch('/api/screen/on', { method: 'POST' });
      setLocation('/');
    } catch (error) {
      console.error('Failed to turn on screen:', error);
      // Still navigate back even if API call fails
      setLocation('/');
    }
  };

  return (
    <div 
      className="min-h-screen bg-black w-full h-full fixed inset-0 z-50 cursor-pointer"
      onClick={handleScreenOn}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleScreenOn();
        }
      }}
      tabIndex={0}
    >
      {/* Completely black screen - click anywhere to wake */}
    </div>
  );
}
