/**
 * Message role types
 */
export type MessageRole = "user" | "assistant" | "system";

/**
 * Tool call status
 */
export type ToolCallStatus = "pending" | "running" | "completed" | "error";

/**
 * Connection status for WebSocket
 */
export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

/**
 * Tool call information
 */
export interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
  output?: string;
  status: ToolCallStatus;
}

/**
 * Message metadata
 */
export interface MessageMetadata {
  toolCalls?: ToolCall[];
  tokens?: number;
  model?: string;
  isStreaming?: boolean;
  messageId?: string;
  errorCode?: string;
  recoverable?: boolean;
}

/**
 * Chat message
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

/**
 * Conversation summary
 */
export interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}

/**
 * WebSocket event types
 */
export type WSEventType =
  | "user.message"
  | "assistant.message"
  | "assistant.typing"
  | "tool.execution"
  | "approval.request"
  | "error"
  | "heartbeat";

/**
 * WebSocket event payload
 */
export interface WSEvent {
  event_id: string;
  event_type: WSEventType;
  source: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

/**
 * User message payload
 */
export interface UserMessagePayload {
  content: string;
  conversation_id?: string;
}

/**
 * Assistant message payload
 */
export interface AssistantMessagePayload {
  content: string;
  message_id: string;
  is_streaming?: boolean;
  is_complete?: boolean;
}

/**
 * Typing indicator payload
 */
export interface TypingPayload {
  is_typing: boolean;
}

/**
 * Error payload
 */
export interface ErrorPayload {
  code: string;
  message: string;
  recoverable?: boolean;
  details?: Record<string, unknown>;
}

/**
 * Approval request payload
 */
export interface ApprovalRequestPayload {
  request_id: string;
  action: string;
  description: string;
  risk_level: "low" | "medium" | "high";
  details: Record<string, unknown>;
  timeout_seconds: number;
}
