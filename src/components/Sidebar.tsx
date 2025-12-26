import { useState } from "react";
import {
  MessageSquare,
  History,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useConversationStore } from "@/stores/conversationStore";

interface NavItem {
  icon: React.ReactNode;
  label: string;
  id: string;
}

const navItems: NavItem[] = [
  { icon: <MessageSquare className="h-4 w-4" />, label: "Chat", id: "chat" },
  { icon: <History className="h-4 w-4" />, label: "History", id: "history" },
  { icon: <Brain className="h-4 w-4" />, label: "Memory", id: "memory" },
  { icon: <Settings className="h-4 w-4" />, label: "Settings", id: "settings" },
];

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [activeItem, setActiveItem] = useState("chat");
  const { createConversation } = useConversationStore();

  const handleNewChat = () => {
    createConversation();
    setActiveItem("chat");
  };

  return (
    <div
      className={cn(
        "flex h-full flex-col border-r border-border bg-card transition-all duration-200",
        isCollapsed ? "w-14" : "w-48"
      )}
    >
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-border px-2">
        {!isCollapsed && (
          <span className="text-sm font-semibold text-foreground pl-2">
            Emperor
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn("h-8 w-8", isCollapsed && "mx-auto")}
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <Button
          variant="outline"
          className={cn(
            "w-full justify-start gap-2",
            isCollapsed && "justify-center px-0"
          )}
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && <span>New Chat</span>}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => (
          <Button
            key={item.id}
            variant={activeItem === item.id ? "secondary" : "ghost"}
            className={cn(
              "w-full justify-start gap-2",
              isCollapsed && "justify-center px-0"
            )}
            onClick={() => setActiveItem(item.id)}
          >
            {item.icon}
            {!isCollapsed && <span>{item.label}</span>}
          </Button>
        ))}
      </nav>
    </div>
  );
}
