import { useRef, useEffect, useState, FormEvent, useCallback } from "react";
import { Send } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMessage } from "@/components/ChatMessage";
import { MicrophoneButton } from "@/components/MicrophoneButton";
import { useConversationStore } from "@/stores/conversationStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { cn } from "@/lib/utils";

/**
 * Premium Crown SVG icon for welcome screen with enhanced detail
 */
function WelcomeCrownIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="welcomeCrownGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="50%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#B8860B" />
        </linearGradient>
        <filter id="crownGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Crown body with gradient fill */}
      <path
        d="M8 48L12 20L24 32L32 12L40 32L52 20L56 48H8Z"
        fill="url(#welcomeCrownGradient)"
        fillOpacity="0.25"
        filter="url(#crownGlow)"
      />
      <path
        d="M8 48L12 20L24 32L32 12L40 32L52 20L56 48H8Z"
        stroke="url(#welcomeCrownGradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Crown jewels - top points */}
      <circle cx="32" cy="12" r="3" fill="#FFD700" />
      <circle cx="12" cy="20" r="2.5" fill="#D4AF37" />
      <circle cx="52" cy="20" r="2.5" fill="#D4AF37" />

      {/* Crown band */}
      <path
        d="M10 52H54"
        stroke="url(#welcomeCrownGradient)"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Decorative gems on crown body */}
      <circle cx="24" cy="40" r="2" fill="#FFD700" fillOpacity="0.8" />
      <circle cx="32" cy="38" r="2.5" fill="#FFD700" />
      <circle cx="40" cy="40" r="2" fill="#FFD700" fillOpacity="0.8" />
    </svg>
  );
}

/**
 * Small Crown icon for typing indicator avatar
 */
function SmallCrownIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="smallCrownGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="50%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#B8860B" />
        </linearGradient>
      </defs>
      <path
        d="M3 17L4.5 7L9 11L12 4L15 11L19.5 7L21 17H3Z"
        fill="url(#smallCrownGradient)"
        fillOpacity="0.3"
      />
      <path
        d="M3 17L4.5 7L9 11L12 4L15 11L19.5 7L21 17H3Z"
        stroke="url(#smallCrownGradient)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="4" r="1.5" fill="#FFD700" />
      <path d="M4 19.5H20" stroke="url(#smallCrownGradient)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Premium typing indicator with gold dots
 */
function TypingIndicator() {
  return (
    <div className="flex gap-4 px-6 py-4 fade-in">
      {/* Emperor avatar with crown */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--black-secondary)] to-[var(--black-tertiary)] border border-[var(--gold-primary)]/30 shadow-lg gold-glow">
        <SmallCrownIcon className="h-5 w-5" />
      </div>

      {/* Typing dots container with premium styling */}
      <div className="typing-container flex items-center gap-2 px-5 py-3 rounded-2xl">
        <span className="h-2.5 w-2.5 rounded-full typing-dot-gold" />
        <span className="h-2.5 w-2.5 rounded-full typing-dot-gold" />
        <span className="h-2.5 w-2.5 rounded-full typing-dot-gold" />
      </div>
    </div>
  );
}

/**
 * Premium welcome screen with Emperor branding
 */
function WelcomeScreen() {
  return (
    <div className="welcome-container flex flex-1 flex-col items-center justify-center p-8 text-center min-h-[400px]">
      {/* Crown icon with floating animation */}
      <div className="crown-icon mb-8">
        <WelcomeCrownIcon className="h-20 w-20" />
      </div>

      {/* Title with gradient text */}
      <h2 className="welcome-title text-3xl font-semibold tracking-wide mb-4">
        Welcome to Emperor
      </h2>

      {/* Subtitle with elegant typography */}
      <p className="welcome-subtitle text-sm max-w-sm leading-relaxed">
        Your sovereign AI assistant awaits your command.
        <br />
        <span className="text-[var(--gold-muted)]">Speak or type to begin your audience.</span>
      </p>

      {/* Decorative element */}
      <div className="mt-10 flex items-center gap-4">
        <div className="h-px w-16 bg-gradient-to-r from-transparent to-[var(--gold-primary)]/40" />
        <div className="h-2 w-2 rounded-full bg-[var(--gold-primary)]/50" />
        <div className="h-px w-16 bg-gradient-to-l from-transparent to-[var(--gold-primary)]/40" />
      </div>

      {/* Hint text */}
      <div className="mt-8 opacity-50 text-xs text-[var(--gold-dark)]">
        Press Enter to send a message
      </div>
    </div>
  );
}

export function ChatPanel() {
  const [inputValue, setInputValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
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

  const handleRecordingStart = useCallback(() => {
    setIsRecording(true);
    // Visual feedback only - actual audio capture TBD
  }, []);

  const handleRecordingStop = useCallback(() => {
    setIsRecording(false);
    // Visual feedback only - actual audio processing TBD
  }, []);

  return (
    <div className="relative flex h-full flex-col bg-[var(--black-primary)]">
      {/* Messages area */}
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="flex flex-col py-4">
          {messages.length === 0 ? (
            <WelcomeScreen />
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}

          {/* Typing indicator */}
          {isTyping && <TypingIndicator />}
        </div>
      </ScrollArea>

      {/* Floating Microphone Button - Right Side */}
      <div className="absolute right-4 bottom-24 z-10">
        <MicrophoneButton
          onRecordingStart={handleRecordingStart}
          onRecordingStop={handleRecordingStop}
          disabled={!isConnected}
        />
      </div>

      {/* Input area - Premium styling */}
      <div className="border-t border-[var(--gold-primary)]/10 bg-gradient-to-t from-[var(--black-secondary)] to-[var(--black-primary)] p-4">
        <form onSubmit={handleSubmit} className="flex gap-3 items-center">
          {/* Text input */}
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                isConnected
                  ? isRecording
                    ? "Listening..."
                    : "Type a message..."
                  : "Connecting..."
              }
              disabled={!isConnected || isRecording}
              className={cn(
                "w-full bg-[var(--black-tertiary)] border-[var(--gold-primary)]/20",
                "text-[var(--gold-light)] placeholder:text-[var(--gold-dark)]/50",
                "focus:border-[var(--gold-primary)]/50 focus:ring-[var(--gold-primary)]/30",
                "transition-all duration-200 rounded-xl py-3 px-4",
                isRecording && "animate-pulse"
              )}
            />
          </div>

          {/* Send button - Gold accent */}
          <Button
            type="submit"
            size="icon"
            disabled={!isConnected || !inputValue.trim() || isRecording}
            className={cn(
              "shrink-0 h-11 w-11 rounded-xl",
              "bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)]",
              "text-[var(--black-primary)]",
              "hover:from-[var(--gold-accent)] hover:to-[var(--gold-primary)]",
              "disabled:opacity-40 disabled:cursor-not-allowed",
              "transition-all duration-200",
              "shadow-lg hover:shadow-[0_0_20px_rgba(212,175,55,0.3)]",
              "focus-visible:ring-2 focus-visible:ring-[var(--gold-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--black-primary)]"
            )}
          >
            <Send className="h-5 w-5" />
          </Button>
        </form>

        {/* Recording indicator text */}
        {isRecording && (
          <div className="flex items-center justify-center gap-2 mt-2 text-xs text-[var(--gold-primary)]">
            <span className="h-2 w-2 rounded-full bg-[var(--gold-primary)] animate-pulse" />
            Recording...
          </div>
        )}
      </div>
    </div>
  );
}
