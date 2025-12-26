import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User } from "lucide-react";
import { cn, formatTime } from "@/lib/utils";
import type { Message } from "@/types";

interface ChatMessageProps {
  message: Message;
}

/**
 * Crown SVG icon for Emperor/Assistant avatar
 * Premium gold styling with gradient
 */
function CrownIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="crownGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="50%" stopColor="#D4AF37" />
          <stop offset="100%" stopColor="#B8860B" />
        </linearGradient>
      </defs>
      <path
        d="M2.5 19h19v2h-19v-2zm19.57-9.36c-.21-.8-1.04-1.28-1.84-1.06l-5.31 1.42-2.76-5.2a1.5 1.5 0 00-2.66 0l-2.76 5.2-5.31-1.42c-.8-.22-1.63.26-1.84 1.06-.21.8.26 1.62 1.06 1.83l5.31 1.42.02 4.11h11.54l.02-4.11 5.31-1.42c.8-.21 1.27-1.03 1.06-1.83z"
        fill="url(#crownGradient)"
      />
    </svg>
  );
}

/**
 * User avatar with initial letter
 */
function UserAvatar() {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--gold-primary)] to-[var(--gold-dark)] text-[var(--black-primary)] shadow-lg">
      <User className="h-5 w-5" />
    </div>
  );
}

/**
 * Assistant/Emperor avatar with crown icon
 */
function AssistantAvatar() {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--black-secondary)] to-[var(--black-tertiary)] border border-[var(--gold-primary)]/30 shadow-lg gold-glow">
      <CrownIcon className="h-5 w-5" />
    </div>
  );
}

/**
 * System message avatar (warning/error)
 */
function SystemAvatar() {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-destructive/20 text-destructive border border-destructive/30 shadow-lg">
      <span className="text-lg font-bold">!</span>
    </div>
  );
}

export const ChatMessage = memo(function ChatMessage({
  message,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div
      className={cn(
        "flex gap-4 px-6 py-4",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      {isUser ? (
        <UserAvatar />
      ) : isSystem ? (
        <SystemAvatar />
      ) : (
        <AssistantAvatar />
      )}

      {/* Message content */}
      <div
        className={cn(
          "flex max-w-[75%] flex-col gap-2",
          isUser && "items-end"
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm transition-all duration-200",
            isUser && "message-bubble-user text-[var(--black-primary)] font-medium",
            !isUser && !isSystem && "message-bubble-assistant text-[var(--gold-light)]",
            isSystem && "bg-destructive/10 text-destructive border border-destructive/20"
          )}
        >
          {isUser || isSystem ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose prose-sm prose-invert max-w-none prose-headings:text-[var(--gold-light)] prose-p:text-[var(--gold-light)] prose-strong:text-[var(--gold-accent)] prose-code:text-[var(--gold-primary)] prose-code:bg-[var(--black-tertiary)] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-[var(--black-primary)] prose-pre:border prose-pre:border-[var(--gold-primary)]/10 prose-a:text-[var(--gold-primary)] prose-a:no-underline hover:prose-a:text-[var(--gold-accent)]">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-[var(--gold-dark)]/70 px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
});
