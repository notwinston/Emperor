import { useRef, useEffect, useState, FormEvent } from "react";
import { Send, Mic } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMessage } from "@/components/ChatMessage";
import { useConversationStore } from "@/stores/conversationStore";
import { useWebSocket } from "@/hooks/useWebSocket";

export function ChatPanel() {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, isTyping, status } = useConversationStore();
  const { sendMessage } = useWebSocket();

  const isConnected = status === "connected";

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = inputValue.trim();
    if (text && isConnected) {
      sendMessage(text);
      setInputValue("");
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages area */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="flex flex-col py-4">
          {messages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center p-8 text-center">
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-foreground">
                  Welcome to Emperor
                </h3>
                <p className="text-sm text-muted-foreground">
                  Your AI assistant is ready to help.
                  <br />
                  Type a message to get started.
                </p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}

          {/* Typing indicator */}
          {isTyping && (
            <div className="flex gap-3 px-4 py-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-medium">
                E
              </div>
              <div className="flex items-center gap-1 rounded-lg bg-secondary px-3 py-2">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input area */}
      <div className="border-t border-border p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0"
            disabled={!isConnected}
          >
            <Mic className="h-4 w-4" />
          </Button>

          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={
              isConnected ? "Type a message..." : "Connecting..."
            }
            disabled={!isConnected}
            className="flex-1"
          />

          <Button
            type="submit"
            size="icon"
            className="shrink-0"
            disabled={!isConnected || !inputValue.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
