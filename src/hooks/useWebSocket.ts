import { useEffect, useRef, useCallback } from "react";
import { useConversationStore } from "@/stores/conversationStore";
import { generateId } from "@/lib/utils";
import { useAudioPlayer } from "./useAudioPlayer";
import type {
  WSEvent,
  AssistantMessagePayload,
  TypingPayload,
  ErrorPayload,
  AgentStatusPayload,
  ToolExecutePayload,
  ToolResultPayload,
  ApprovalRequestPayload,
  ApprovalResponsePayload,
  LeadProgressPayload,
  LeadCompletePayload,
  WorkerProgressPayload,
  WorkerCompletePayload,
  VoiceTranscriptionPayload,
  VoiceAudioChunkPayload,
  VoiceErrorPayload,
} from "@/types";

interface VoiceCallbacks {
  /** Called when transcription is received */
  onTranscription?: (text: string) => void;
  /** Called when TTS audio completes */
  onTTSComplete?: () => void;
  /** Called on voice error */
  onVoiceError?: (error: string, stage: "transcription" | "synthesis") => void;
}

const WS_URL = "ws://127.0.0.1:8765/ws";
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(voiceCallbacks?: VoiceCallbacks) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const voiceCallbacksRef = useRef(voiceCallbacks);

  // Keep callbacks ref updated
  voiceCallbacksRef.current = voiceCallbacks;

  const { setStatus, addMessage, upsertStreamingMessage, setTyping } =
    useConversationStore();

  // Audio player for TTS playback
  const audioPlayer = useAudioPlayer();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WSEvent = JSON.parse(event.data);

        switch (data.event_type) {
          // ===== Core Message Events =====
          case "assistant.message": {
            const payload = data.payload as unknown as AssistantMessagePayload;

            // Use upsert for all streaming messages (creates if not exists, updates if exists)
            upsertStreamingMessage(
              payload.message_id,
              payload.content,
              payload.is_complete ?? false
            );

            if (payload.is_complete) {
              setTyping(false);
            }
            break;
          }

          case "assistant.typing": {
            const payload = data.payload as unknown as TypingPayload;
            setTyping(payload.is_typing);
            break;
          }

          case "error": {
            const payload = data.payload as unknown as ErrorPayload;
            const errorCode = payload.code || "UNKNOWN";
            const errorMessage = payload.message || "An unknown error occurred";
            const isRecoverable = payload.recoverable !== false;

            console.error(`WebSocket error [${errorCode}]:`, errorMessage);

            // Only show user-facing errors (skip internal/debug errors)
            if (errorCode !== "INTERNAL_ERROR" || !isRecoverable) {
              addMessage({
                id: generateId(),
                role: "system",
                content: `⚠️ ${errorMessage}`,
                timestamp: new Date(),
                metadata: {
                  errorCode,
                  recoverable: isRecoverable,
                },
              });
            }

            setTyping(false);
            break;
          }

          case "heartbeat": {
            // Respond to server's heartbeat ping with pong
            const payload = data.payload as { status?: string };
            if (payload.status === "ping" && wsRef.current?.readyState === WebSocket.OPEN) {
              const pongEvent: WSEvent = {
                event_id: generateId(),
                event_type: "heartbeat",
                source: "frontend",
                timestamp: new Date().toISOString(),
                payload: { status: "pong" },
              };
              wsRef.current.send(JSON.stringify(pongEvent));
            }
            break;
          }

          // ===== Agent Status Events =====
          case "agent.status": {
            const payload = data.payload as unknown as AgentStatusPayload;
            console.log(`[Agent] ${payload.agent_name} (${payload.agent_type}): ${payload.status}`, payload.message || "");
            // TODO: Update agent store when implemented
            break;
          }

          // ===== Lead Events =====
          case "lead.received":
          case "lead.planning": {
            const payload = data.payload as Record<string, unknown>;
            console.log(`[Lead] ${data.event_type}:`, payload);
            break;
          }

          case "lead.progress": {
            const payload = data.payload as unknown as LeadProgressPayload;
            console.log(`[Lead ${payload.lead_type}] Progress: ${Math.round(payload.progress * 100)}%`, payload.message || "");
            // TODO: Update progress in agent store when implemented
            break;
          }

          case "lead.complete": {
            const payload = data.payload as unknown as LeadCompletePayload;
            console.log(`[Lead ${payload.lead_type}] Complete:`, payload.result);
            // TODO: Update agent store when implemented
            break;
          }

          case "lead.error": {
            const payload = data.payload as Record<string, unknown>;
            console.error(`[Lead Error]:`, payload);
            break;
          }

          // ===== Worker Events =====
          case "worker.start": {
            const payload = data.payload as Record<string, unknown>;
            console.log(`[Worker] Started:`, payload);
            break;
          }

          case "worker.progress": {
            const payload = data.payload as unknown as WorkerProgressPayload;
            console.log(`[Worker ${payload.worker_type}] Progress: ${Math.round(payload.progress * 100)}%`, payload.current_step || "");
            // TODO: Update progress in agent store when implemented
            break;
          }

          case "worker.complete": {
            const payload = data.payload as unknown as WorkerCompletePayload;
            console.log(`[Worker ${payload.worker_type}] Complete:`, payload.result);
            // TODO: Update agent store when implemented
            break;
          }

          case "worker.error": {
            const payload = data.payload as Record<string, unknown>;
            console.error(`[Worker Error]:`, payload);
            break;
          }

          // ===== Tool Events =====
          case "tool.execute": {
            const payload = data.payload as unknown as ToolExecutePayload;
            console.log(`[Tool] Executing: ${payload.tool_name}`, payload.requires_approval ? "(requires approval)" : "");
            // TODO: Update tool execution store when implemented
            break;
          }

          case "tool.progress": {
            const payload = data.payload as Record<string, unknown>;
            console.log(`[Tool] Progress:`, payload);
            break;
          }

          case "tool.result": {
            const payload = data.payload as unknown as ToolResultPayload;
            if (payload.success) {
              console.log(`[Tool] ${payload.tool_name} completed (${payload.execution_time_ms}ms)`);
            } else {
              console.error(`[Tool] ${payload.tool_name} failed:`, payload.error);
            }
            // TODO: Update tool execution store when implemented
            break;
          }

          case "tool.error": {
            const payload = data.payload as Record<string, unknown>;
            console.error(`[Tool Error]:`, payload);
            break;
          }

          // ===== Approval Events =====
          case "approval.request": {
            const payload = data.payload as unknown as ApprovalRequestPayload;
            console.log(`[Approval] Request: ${payload.action} (${payload.risk_level} risk)`, payload.description);
            // TODO: Show approval dialog in UI
            // For now, add a system message to alert the user
            addMessage({
              id: generateId(),
              role: "system",
              content: `🔐 Approval needed: ${payload.description}\nAction: ${payload.action}\nRisk: ${payload.risk_level}`,
              timestamp: new Date(),
              metadata: {
                approvalRequest: payload,
              },
            });
            break;
          }

          case "approval.response": {
            const payload = data.payload as unknown as ApprovalResponsePayload;
            console.log(`[Approval] Response: ${payload.approved ? "Approved" : "Denied"}`, payload.reason || "");
            // TODO: Update approval store when implemented
            break;
          }

          case "approval.timeout": {
            const payload = data.payload as Record<string, unknown>;
            console.warn(`[Approval] Timeout:`, payload);
            addMessage({
              id: generateId(),
              role: "system",
              content: `⏰ Approval request timed out`,
              timestamp: new Date(),
            });
            break;
          }

          // ===== System Events =====
          case "system.error": {
            const payload = data.payload as Record<string, unknown>;
            console.error(`[System Error]:`, payload);
            addMessage({
              id: generateId(),
              role: "system",
              content: `⚠️ System error: ${(payload as { error?: string }).error || "Unknown error"}`,
              timestamp: new Date(),
            });
            break;
          }

          // ===== Voice Events =====
          case "voice.transcription": {
            const payload = data.payload as unknown as VoiceTranscriptionPayload;
            console.log(`[Voice] Transcribed: ${payload.text}`);
            voiceCallbacksRef.current?.onTranscription?.(payload.text);
            break;
          }

          case "voice.audio_chunk": {
            const payload = data.payload as unknown as VoiceAudioChunkPayload;
            console.log(`[Voice] Audio chunk received (${payload.format})`);
            audioPlayer.playChunk(payload.audio);
            break;
          }

          case "voice.audio_complete": {
            console.log("[Voice] TTS complete");
            voiceCallbacksRef.current?.onTTSComplete?.();
            break;
          }

          case "voice.error": {
            const payload = data.payload as unknown as VoiceErrorPayload;
            console.error(`[Voice Error] ${payload.stage}:`, payload.error);
            voiceCallbacksRef.current?.onVoiceError?.(payload.error, payload.stage);

            // Show error message to user
            addMessage({
              id: generateId(),
              role: "system",
              content: `🎤 Voice error (${payload.stage}): ${payload.error}`,
              timestamp: new Date(),
              metadata: {
                recoverable: payload.recoverable,
              },
            });
            break;
          }

          default:
            console.log("Unknown event type:", data.event_type, data.payload);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    },
    [addMessage, upsertStreamingMessage, setTyping, audioPlayer]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus("connecting");

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setStatus("connected");
        reconnectAttemptsRef.current = 0;
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setStatus("disconnected");
        wsRef.current = null;

        // Attempt reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++;
          const delay = RECONNECT_DELAY * reconnectAttemptsRef.current;
          console.log(`Reconnecting in ${delay}ms...`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        } else {
          setStatus("error");
          console.error("Max reconnection attempts reached");
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("error");
      };

      ws.onmessage = handleMessage;

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      setStatus("error");
    }
  }, [setStatus, handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    reconnectAttemptsRef.current = MAX_RECONNECT_ATTEMPTS; // Prevent reconnect
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
  }, [setStatus]);

  const reconnect = useCallback(() => {
    // Reset reconnect attempts and try again
    reconnectAttemptsRef.current = 0;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    connect();
  }, [connect]);

  const sendMessage = useCallback(
    (text: string) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not connected");
        return;
      }

      const messageId = generateId();

      // Add user message to store
      addMessage({
        id: messageId,
        role: "user",
        content: text,
        timestamp: new Date(),
      });

      // Send to server
      const event: WSEvent = {
        event_id: generateId(),
        event_type: "user.message",
        source: "frontend",
        timestamp: new Date().toISOString(),
        payload: {
          content: text,
          message_id: messageId,
        },
      };

      wsRef.current.send(JSON.stringify(event));
    },
    [addMessage]
  );

  const sendApprovalResponse = useCallback(
    (requestId: string, approved: boolean, reason?: string) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not connected");
        return;
      }

      const event: WSEvent = {
        event_id: generateId(),
        event_type: "approval.response",
        source: "frontend",
        timestamp: new Date().toISOString(),
        payload: {
          request_id: requestId,
          approved,
          reason,
        },
      };

      wsRef.current.send(JSON.stringify(event));

      // Add a confirmation message
      addMessage({
        id: generateId(),
        role: "system",
        content: approved
          ? `✅ Action approved${reason ? `: ${reason}` : ""}`
          : `❌ Action denied${reason ? `: ${reason}` : ""}`,
        timestamp: new Date(),
      });
    },
    [addMessage]
  );

  /**
   * Send audio data to backend for transcription.
   * The transcribed text will be processed as a user message.
   */
  const sendAudio = useCallback(async (audioBlob: Blob) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }

    try {
      // Convert blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64Audio = btoa(binary);

      // Determine format from blob type
      const format = audioBlob.type.includes("webm")
        ? "webm"
        : audioBlob.type.includes("wav")
          ? "wav"
          : "webm";

      const event: WSEvent = {
        event_id: generateId(),
        event_type: "voice.audio",
        source: "frontend",
        timestamp: new Date().toISOString(),
        payload: {
          audio: base64Audio,
          format,
        },
      };

      wsRef.current.send(JSON.stringify(event));
      console.log(`[Voice] Sent ${bytes.length} bytes of audio (${format})`);
    } catch (error) {
      console.error("Failed to send audio:", error);
    }
  }, []);

  /**
   * Request TTS for text. Audio chunks will be played automatically.
   */
  const requestTTS = useCallback((text: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }

    const event: WSEvent = {
      event_id: generateId(),
      event_type: "voice.tts",
      source: "frontend",
      timestamp: new Date().toISOString(),
      payload: {
        text,
      },
    };

    wsRef.current.send(JSON.stringify(event));
    console.log(`[Voice] Requested TTS for: ${text.slice(0, 50)}...`);
  }, []);

  /**
   * Stop TTS playback
   */
  const stopTTS = useCallback(() => {
    audioPlayer.stop();
  }, [audioPlayer]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    reconnect,
    sendMessage,
    sendApprovalResponse,
    // Voice functions
    sendAudio,
    requestTTS,
    stopTTS,
    // Audio player state
    isPlayingTTS: audioPlayer.isPlaying,
  };
}
