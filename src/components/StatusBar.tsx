import { useConversationStore } from "@/stores/conversationStore";
import { cn } from "@/lib/utils";

export function StatusBar() {
  const { status } = useConversationStore();

  const statusConfig = {
    connected: {
      color: "bg-green-500",
      text: "Emperor Online",
    },
    connecting: {
      color: "bg-yellow-500",
      text: "Connecting...",
    },
    disconnected: {
      color: "bg-gray-500",
      text: "Disconnected",
    },
    error: {
      color: "bg-red-500",
      text: "Connection Error",
    },
  };

  const config = statusConfig[status];

  return (
    <div className="drag-region flex h-10 items-center justify-between border-b border-border bg-card px-4">
      <div className="flex items-center gap-2">
        <div className={cn("h-2 w-2 rounded-full", config.color)} />
        <span className="text-xs font-medium text-muted-foreground">
          {config.text}
        </span>
      </div>

      {/* Window controls placeholder for custom titlebar if needed */}
      <div className="no-drag flex items-center gap-1">
        {/* Add window control buttons here if using custom titlebar */}
      </div>
    </div>
  );
}
