import { useState, useCallback, useEffect } from "react";
import { Mic, Square, Loader2, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useConversationStore } from "@/stores/conversationStore";

type MicrophoneState = "idle" | "recording" | "processing" | "permission_denied";

interface MicrophoneButtonProps {
  disabled?: boolean;
  className?: string;
}

/**
 * Premium floating microphone button with gold styling.
 * Records audio and sends to backend for transcription.
 */
export function MicrophoneButton({
  disabled = false,
  className,
}: MicrophoneButtonProps) {
  const [state, setState] = useState<MicrophoneState>("idle");
  const { status } = useConversationStore();
  const { sendAudio } = useWebSocket();

  const isConnected = status === "connected";
  const isDisabled = disabled || !isConnected;

  const {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    permissionDenied,
  } = useAudioRecorder({
    onAudioData: (blob) => {
      setState("processing");
      sendAudio(blob);
      // Reset to idle after a short delay (backend will send transcription)
      setTimeout(() => {
        setState("idle");
      }, 2000);
    },
    onError: (error) => {
      console.error("Recording error:", error);
      setState("idle");
    },
    onStart: () => {
      setState("recording");
    },
    onStop: () => {
      // State will be set to processing in onAudioData
    },
  });

  // Update state when permission is denied
  useEffect(() => {
    if (permissionDenied) {
      setState("permission_denied");
    }
  }, [permissionDenied]);

  // Sync state with recording state
  useEffect(() => {
    if (isRecording && state !== "recording") {
      setState("recording");
    }
  }, [isRecording, state]);

  const handleClick = useCallback(async () => {
    if (isDisabled) return;

    if (state === "idle" || state === "permission_denied") {
      await startRecording();
    } else if (state === "recording") {
      stopRecording();
    }
  }, [state, isDisabled, startRecording, stopRecording]);

  const getStateStyles = () => {
    switch (state) {
      case "recording":
        return "mic-recording";
      case "processing":
        return "mic-processing";
      case "permission_denied":
        return "mic-idle opacity-60";
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
      case "permission_denied":
        return <MicOff className="h-6 w-6" />;
      default:
        return <Mic className="h-6 w-6" />;
    }
  };

  const getAriaLabel = () => {
    if (!isConnected) return "Disconnected - cannot record";
    switch (state) {
      case "recording":
        return "Stop recording";
      case "processing":
        return "Processing audio";
      case "permission_denied":
        return "Microphone access denied - click to retry";
      default:
        return "Start voice recording";
    }
  };

  // Calculate pulse scale based on audio level
  const pulseScale = 1 + audioLevel * 0.3;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled || state === "processing"}
      aria-label={getAriaLabel()}
      aria-pressed={state === "recording"}
      className={cn(
        // Base styles
        "relative flex items-center justify-center rounded-full transition-all duration-200",
        // Size - Large and prominent (56px)
        "h-14 w-14",
        // State-specific styles from CSS classes
        getStateStyles(),
        // Text color based on state
        state === "idle" && "text-[var(--gold-primary)]",
        state === "recording" && "text-[var(--black-primary)]",
        state === "processing" && "text-[var(--gold-light)]",
        state === "permission_denied" && "text-[var(--gold-dark)]",
        // Focus styles
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--gold-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--black-primary)]",
        // Disabled styles
        isDisabled && "opacity-50 cursor-not-allowed",
        // Custom className
        className
      )}
    >
      {/* Audio level indicator ring */}
      {state === "recording" && (
        <div
          className="absolute inset-0 rounded-full bg-[var(--gold-primary)]/20 transition-transform duration-75"
          style={{ transform: `scale(${pulseScale})` }}
        />
      )}
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
