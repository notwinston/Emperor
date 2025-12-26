import { useState, useCallback } from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type MicrophoneState = "idle" | "recording" | "processing";

interface MicrophoneButtonProps {
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Premium floating microphone button with gold styling
 * Positioned on the right side of the chat area
 */
export function MicrophoneButton({
  onRecordingStart,
  onRecordingStop,
  disabled = false,
  className,
}: MicrophoneButtonProps) {
  const [state, setState] = useState<MicrophoneState>("idle");

  const handleClick = useCallback(() => {
    if (disabled) return;

    if (state === "idle") {
      setState("recording");
      onRecordingStart?.();
    } else if (state === "recording") {
      setState("processing");
      onRecordingStop?.();
      // Simulate processing time (visual only for now)
      setTimeout(() => {
        setState("idle");
      }, 1500);
    }
  }, [state, disabled, onRecordingStart, onRecordingStop]);

  const getStateStyles = () => {
    switch (state) {
      case "recording":
        return "mic-recording";
      case "processing":
        return "mic-processing";
      default:
        return "mic-idle";
    }
  };

  const getIcon = () => {
    switch (state) {
      case "recording":
        return <Square className="h-6 w-6 fill-current" />;
      case "processing":
        return <Loader2 className="h-6 w-6 animate-spin" />;
      default:
        return <Mic className="h-6 w-6" />;
    }
  };

  const getAriaLabel = () => {
    switch (state) {
      case "recording":
        return "Stop recording";
      case "processing":
        return "Processing audio";
      default:
        return "Start voice recording";
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || state === "processing"}
      aria-label={getAriaLabel()}
      aria-pressed={state === "recording"}
      className={cn(
        // Base styles
        "flex items-center justify-center rounded-full transition-all duration-200",
        // Size - Large and prominent (56px)
        "h-14 w-14",
        // State-specific styles from CSS classes
        getStateStyles(),
        // Text color based on state
        state === "idle" && "text-[var(--gold-primary)]",
        state === "recording" && "text-[var(--black-primary)]",
        state === "processing" && "text-[var(--gold-light)]",
        // Focus styles
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--black-primary)]",
        // Disabled styles
        disabled && "opacity-50 cursor-not-allowed",
        // Custom className
        className
      )}
    >
      {getIcon()}
    </button>
  );
}

/**
 * Floating wrapper for positioning the microphone button
 * on the right side of the chat area
 */
export function FloatingMicrophoneButton({
  ...props
}: MicrophoneButtonProps) {
  return (
    <div className="fixed right-6 bottom-24 z-50">
      <MicrophoneButton {...props} />
    </div>
  );
}
