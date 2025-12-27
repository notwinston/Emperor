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
import { SettingsPanel } from "./SettingsPanel";

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

// Emperor Crown SVG Icon
function CrownIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M2.5 18.5L4 7.5L8 12L12 4L16 12L20 7.5L21.5 18.5H2.5Z"
        fill="currentColor"
        fillOpacity="0.2"
      />
      <path
        d="M2.5 18.5L4 7.5L8 12L12 4L16 12L20 7.5L21.5 18.5H2.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="4" r="1" fill="currentColor" />
      <circle cx="4" cy="7.5" r="1" fill="currentColor" />
      <circle cx="20" cy="7.5" r="1" fill="currentColor" />
      <path
        d="M4 21H20"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [activeItem, setActiveItem] = useState("chat");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { createConversation } = useConversationStore();

  const handleNewChat = () => {
    createConversation();
    setActiveItem("chat");
  };

  const handleNavClick = (itemId: string) => {
    if (itemId === "settings") {
      setSettingsOpen(true);
    } else {
      setActiveItem(itemId);
    }
  };

  return (
    <div
      className={cn(
        "flex h-full flex-col border-r border-border/50 sidebar-gradient sidebar-collapse-transition shadow-emperor-lg",
        isCollapsed ? "w-14" : "w-52"
      )}
    >
      {/* Header with Emperor Branding */}
      <div
        className={cn(
          "flex h-14 items-center border-b border-border/50 sidebar-header-gradient",
          isCollapsed ? "justify-center px-2" : "justify-between px-3"
        )}
      >
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <CrownIcon className="h-5 w-5 text-gold-primary crown-icon" />
            <span className="emperor-logo-text text-sm">Emperor</span>
          </div>
        )}
        {isCollapsed && (
          <CrownIcon className="h-5 w-5 text-gold-primary crown-icon" />
        )}
        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-muted-foreground hover:text-gold-primary hover:bg-transparent transition-all duration-200"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Collapse Toggle for Collapsed State */}
      {isCollapsed && (
        <div className="p-2">
          <Button
            variant="ghost"
            size="icon"
            className="w-full h-8 text-muted-foreground hover:text-gold-primary hover:bg-gold-primary/10 transition-all duration-200"
            onClick={() => setIsCollapsed(false)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* New Chat Button */}
      <div className="p-2">
        <Button
          variant="outline"
          className={cn(
            "w-full btn-gold-outline text-gold-text hover:text-gold-light",
            isCollapsed ? "justify-center px-0" : "justify-start gap-2"
          )}
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && <span className="font-medium">New Chat</span>}
        </Button>
      </div>

      {/* Decorative Divider */}
      <div className="mx-3 divider-gold" />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2 mt-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={cn(
              "nav-item-hover w-full flex items-center rounded-md px-3 py-2 text-sm font-medium",
              isCollapsed && "justify-center px-0",
              activeItem === item.id
                ? "active text-gold-primary"
                : "text-muted-foreground hover:text-gold-text"
            )}
            onClick={() => handleNavClick(item.id)}
          >
            <span
              className={cn(
                "icon-gold-hover",
                activeItem === item.id && "text-gold-primary"
              )}
            >
              {item.icon}
            </span>
            {!isCollapsed && (
              <span className="ml-3 transition-opacity duration-200">
                {item.label}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom Section - Optional Version Info */}
      {!isCollapsed && (
        <div className="p-3 border-t border-border/30">
          <p className="text-[10px] text-muted-foreground/50 text-center">
            Emperor v1.0
          </p>
        </div>
      )}

      {/* Settings Panel */}
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
