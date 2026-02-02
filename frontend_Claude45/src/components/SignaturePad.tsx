import { useRef, useState, useEffect, lazy, Suspense } from 'react';
import type SignatureCanvasType from 'react-signature-canvas';
import { Button } from '@/components/ui/Button';
import { Eraser } from 'lucide-react';

// Lazy load SignatureCanvas to reduce initial bundle size
const SignatureCanvas = lazy(() => import('react-signature-canvas'));

interface SignaturePadProps {
  onSignatureChange: (dataUrl: string | null) => void;
  width?: number;
  height?: number;
  className?: string;
}

export function SignaturePad({ 
  onSignatureChange, 
  width, 
  height,
  className 
}: SignaturePadProps) {
  const sigPadRef = useRef<SignatureCanvasType>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasDimensions, setCanvasDimensions] = useState({ width: width || 400, height: height || 200 });

  // Handle responsive resizing
  useEffect(() => {
    if (width && height) return; // If fixed dimensions provided, don't auto-resize

    const resizeCanvas = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        // Maintain aspect ratio or fill width
        const newWidth = rect.width;
        // Default height logic: roughly 1/2 width but min 150px
        const newHeight = height || Math.max(150, newWidth * 0.4); 
        
        setCanvasDimensions({ width: newWidth, height: newHeight });
        
        // Note: resizing clears the canvas, so we might want to save data if we wanted to preserve it
        // but for now, simple resize is okay.
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return () => window.removeEventListener('resize', resizeCanvas);
  }, [width, height]);

  const handleClear = () => {
    sigPadRef.current?.clear();
    onSignatureChange(null);
  };

  const handleEnd = () => {
    if (sigPadRef.current) {
      if (sigPadRef.current.isEmpty()) {
        onSignatureChange(null);
      } else {
        // Get PNG data URL directly from the canvas
        // Note: We avoid getTrimmedCanvas() due to trim-canvas compatibility issues
        const dataUrl = sigPadRef.current.toDataURL('image/png');
        console.log('Signature captured, length:', dataUrl.length);
        onSignatureChange(dataUrl);
      }
    }
  };

  // Also trigger on stroke begin to ensure we capture initial state
  const handleBegin = () => {
    // We could potentially set a 'dirty' state here
  };

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div 
        ref={containerRef}
        className="border-2 border-dashed border-input rounded-md bg-white hover:border-primary/50 transition-colors flex items-center justify-center overflow-hidden"
        style={{ height: canvasDimensions.height }}
      >
        <Suspense fallback={<div className="text-sm text-muted-foreground">Loading signature pad...</div>}>
          <SignatureCanvas
            ref={sigPadRef}
            penColor="black"
            backgroundColor="white"
            canvasProps={{
              width: canvasDimensions.width,
              height: canvasDimensions.height,
              className: 'signature-canvas w-full h-full rounded-md'
            }}
            onBegin={handleBegin}
            onEnd={handleEnd}
          />
        </Suspense>
      </div>
      
      <div className="flex justify-between items-center text-xs text-muted-foreground">
        <span>Sign above with your finger or mouse</span>
        <Button 
          type="button" 
          variant="ghost" 
          size="sm" 
          onClick={handleClear}
          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 px-2"
        >
          <Eraser className="w-3.5 h-3.5 mr-1" />
          Clear
        </Button>
      </div>
    </div>
  );
}
