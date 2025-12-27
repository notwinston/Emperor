import { useConversationStore } from "@/stores/conversationStore";
import { cn } from "@/lib/utils";

// Small Crown Icon for Status Bar
function MiniCrownIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M2 12L3 5L6 8L8 3L10 8L13 5L14 12H2Z"
        fill="currentColor"
        fillOpacity="0.3"
      />
      <path
        d="M2 12L3 5L6 8L8 3L10 8L13 5L14 12H2Z"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface StatusBarProps {
  reconnect: () => void;
}

export function StatusBar({ reconnect }: StatusBarProps) {
  const { status } = useConversationStore();

  const statusConfig = {
    connected: {
      indicatorClass: "status-indicator connected",
      text: "Emperor Online",
      textClass: "text-gold-text",
      showCrown: true,
      showRetry: false,
    },
    connecting: {
      indicatorClass: "status-indicator connecting",
      text: "Awakening...",
      textClass: "text-gold-light/70",
      showCrown: false,
      showRetry: false,
    },
    disconnected: {
      indicatorClass: "status-indicator disconnected",
      text: "Dormant",
      textClass: "text-muted-foreground",
      showCrown: false,
      showRetry: true,
    },
    error: {
      indicatorClass: "status-indicator error",
      text: "Connection Lost",
      textClass: "text-red-400/80",
      showCrown: false,
      showRetry: true,
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={cn(
        "drag-region flex h-10 items-center justify-between",
        "border-b border-border/30 bg-black-secondary/80 backdrop-blur-sm px-4",
        "transition-all duration-300"
      )}
    >
      <div className="flex items-center gap-3">
        {/* Status Indicator with Gold Glow for Connected */}
        <div className="relative flex items-center justify-center">
          <div className={cn("h-2 w-2 rounded-full", config.indicatorClass)} />
        </div>

        {/* Status Text with Crown for Online */}
        <div className="flex items-center gap-1.5">
          {config.showCrown && (
            <MiniCrownIcon className="h-3 w-3 text-gold-primary" />
          )}
          <span
            className={cn(
              "text-xs font-medium tracking-wide transition-colors duration-300",
              config.textClass
            )}
          >
            {config.text}
          </span>

          {/* Retry button for error/disconnected states */}
          {config.showRetry && (
            <button
              onClick={reconnect}
              className="ml-2 text-xs text-gold-primary/70 hover:text-gold-primary underline underline-offset-2 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>

      {/* Right side - Window controls placeholder for custom titlebar */}
      <div className="no-drag flex items-center gap-2">
        {/* Subtle gold accent line */}
        <div className="h-4 w-px bg-gradient-to-b from-transparent via-gold-primary/20 to-transparent" />

        {/* Optional: Add window control buttons here if using custom titlebar */}
        <div className="flex items-center gap-1 opacity-0">
          {/* Placeholder for traffic lights or custom buttons */}
        </div>
      </div>
    </div>
  );
}
