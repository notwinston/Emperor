import { useEffect, useRef, useCallback } from "react";
import { useConversationStore } from "@/stores/conversationStore";
import { generateId } from "@/lib/utils";
import type {
  WSEvent,
  AssistantMessagePayload,
  TypingPayload,
  ErrorPayload,
} from "@/types";

const WS_URL = "ws://localhost:8765/ws";
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { setStatus, addMessage, updateMessage, setTyping } =
    useConversationStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WSEvent = JSON.parse(event.data);

        switch (data.event_type) {
          case "assistant.message": {
            const payload = data.payload as unknown as AssistantMessagePayload;
            if (payload.is_streaming) {
              // Update existing streaming message
              updateMessage(
                payload.message_id,
                payload.content,
                payload.is_complete
              );
            } else {
              // Add new message
              addMessage({
                id: payload.message_id,
                role: "assistant",
                content: payload.content,
                timestamp: new Date(data.timestamp),
                metadata: {
                  isStreaming: !payload.is_complete,
                  messageId: payload.message_id,
                },
              });
            }
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
            console.error("WebSocket error:", payload.message);
            addMessage({
              id: generateId(),
              role: "system",
              content: `Error: ${payload.message}`,
              timestamp: new Date(),
            });
            setTyping(false);
            break;
          }

          case "heartbeat":
            // Respond to heartbeat if needed
            break;

          default:
            console.log("Unknown event type:", data.event_type);
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    },
    [addMessage, updateMessage, setTyping]
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
    sendMessage,
  };
}
