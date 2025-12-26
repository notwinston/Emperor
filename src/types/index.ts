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
  // Core message events
  | "user.message"
  | "assistant.message"
  | "assistant.typing"
  | "error"
  | "heartbeat"
  // Agent status events
  | "agent.status"
  // Lead events
  | "lead.received"
  | "lead.planning"
  | "lead.progress"
  | "lead.complete"
  | "lead.error"
  // Worker events
  | "worker.start"
  | "worker.progress"
  | "worker.complete"
  | "worker.error"
  // Tool events
  | "tool.execute"
  | "tool.progress"
  | "tool.result"
  | "tool.error"
  // Approval events
  | "approval.request"
  | "approval.response"
  | "approval.timeout"
  // System events
  | "system.error";

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
  agent: string;
}

/**
 * Approval response payload
 */
export interface ApprovalResponsePayload {
  request_id: string;
  approved: boolean;
  reason?: string;
}

/**
 * Agent status types
 */
export type AgentStatus = "started" | "idle" | "busy" | "stopped";

/**
 * Agent type categories
 */
export type AgentType = "orchestrator" | "lead" | "worker";

/**
 * Lead type categories
 */
export type LeadType = "code" | "research" | "task";

/**
 * Worker type categories
 */
export type WorkerType =
  | "programmer"
  | "reviewer"
  | "documentor"
  | "researcher"
  | "analyst"
  | "executor"
  | "monitor";

/**
 * Agent status payload
 */
export interface AgentStatusPayload {
  agent_name: string;
  agent_type: AgentType;
  status: AgentStatus;
  task_id?: string;
  message?: string;
}

/**
 * Lead progress payload
 */
export interface LeadProgressPayload {
  lead_type: LeadType;
  task_id: string;
  progress: number; // 0.0 to 1.0
  message?: string;
  subtasks_total?: number;
  subtasks_complete?: number;
  correlation_id?: string;
}

/**
 * Lead complete payload
 */
export interface LeadCompletePayload {
  lead_type: LeadType;
  task_id: string;
  result: string;
  files_modified?: string[];
  correlation_id?: string;
}

/**
 * Worker progress payload
 */
export interface WorkerProgressPayload {
  worker_type: WorkerType;
  task_id: string;
  progress: number; // 0.0 to 1.0
  message?: string;
  current_step?: string;
  correlation_id?: string;
}

/**
 * Worker complete payload
 */
export interface WorkerCompletePayload {
  worker_type: WorkerType;
  task_id: string;
  result: string;
  files_modified?: string[];
  correlation_id?: string;
}

/**
 * Tool execute payload
 */
export interface ToolExecutePayload {
  tool_name: string;
  tool_input: Record<string, unknown>;
  agent: string;
  requires_approval: boolean;
  correlation_id?: string;
}

/**
 * Tool result payload
 */
export interface ToolResultPayload {
  tool_name: string;
  success: boolean;
  output?: string;
  error?: string;
  execution_time_ms?: number;
  correlation_id?: string;
}

/**
 * Active agent info for UI display
 */
export interface ActiveAgent {
  name: string;
  type: AgentType;
  status: AgentStatus;
  task_id?: string;
  progress?: number;
  message?: string;
}

/**
 * Pending approval for UI display
 */
export interface PendingApproval {
  request_id: string;
  action: string;
  description: string;
  risk_level: "low" | "medium" | "high";
  details: Record<string, unknown>;
  timeout_seconds: number;
  agent: string;
  received_at: Date;
}

/**
 * Active tool execution for UI display
 */
export interface ActiveToolExecution {
  tool_name: string;
  agent: string;
  started_at: Date;
  requires_approval: boolean;
}
