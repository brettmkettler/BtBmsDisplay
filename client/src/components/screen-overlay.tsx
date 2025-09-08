interface ScreenOverlayProps {
  isVisible: boolean;
}

export function ScreenOverlay({ isVisible }: ScreenOverlayProps) {
  if (!isVisible) return null;

  return (
    <div 
      className="fixed inset-0 bg-black z-[9999] cursor-none"
      style={{ 
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: '#000000',
        zIndex: 9999
      }}
    />
  );
}
