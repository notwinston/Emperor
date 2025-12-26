import { create } from "zustand";
import type { Message, Conversation, ConnectionStatus } from "@/types";
import { generateId } from "@/lib/utils";

interface ConversationState {
  // Connection state
  status: ConnectionStatus;

  // Messages in current conversation
  messages: Message[];

  // Typing indicator
  isTyping: boolean;

  // Conversation list
  conversations: Conversation[];

  // Current active conversation
  currentConversationId: string | null;

  // Actions
  setStatus: (status: ConnectionStatus) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, content: string, isComplete?: boolean) => void;
  upsertStreamingMessage: (
    id: string,
    content: string,
    isComplete: boolean
  ) => void;
  setTyping: (isTyping: boolean) => void;
  clearMessages: () => void;
  setCurrentConversation: (id: string | null) => void;
  createConversation: () => string;
  deleteConversation: (id: string) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  // Initial state
  status: "disconnected",
  messages: [],
  isTyping: false,
  conversations: [],
  currentConversationId: null,

  // Actions
  setStatus: (status) => set({ status }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, content, isComplete = false) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id
          ? {
              ...msg,
              content,
              metadata: {
                ...msg.metadata,
                isStreaming: !isComplete,
              },
            }
          : msg
      ),
    })),

  upsertStreamingMessage: (id, content, isComplete) =>
    set((state) => {
      const existingMessage = state.messages.find((msg) => msg.id === id);

      if (existingMessage) {
        // Update existing message
        return {
          messages: state.messages.map((msg) =>
            msg.id === id
              ? {
                  ...msg,
                  content,
                  metadata: {
                    ...msg.metadata,
                    isStreaming: !isComplete,
                  },
                }
              : msg
          ),
        };
      } else {
        // Create new message
        const newMessage: Message = {
          id,
          role: "assistant",
          content,
          timestamp: new Date(),
          metadata: {
            isStreaming: !isComplete,
          },
        };
        return {
          messages: [...state.messages, newMessage],
        };
      }
    }),

  setTyping: (isTyping) => set({ isTyping }),

  clearMessages: () => set({ messages: [] }),

  setCurrentConversation: (id) => set({ currentConversationId: id }),

  createConversation: () => {
    const id = generateId();
    const now = new Date();
    const newConversation: Conversation = {
      id,
      title: "New Conversation",
      createdAt: now,
      updatedAt: now,
      messageCount: 0,
    };

    set((state) => ({
      conversations: [newConversation, ...state.conversations],
      currentConversationId: id,
      messages: [],
    }));

    return id;
  },

  deleteConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id
          ? null
          : state.currentConversationId,
      messages: state.currentConversationId === id ? [] : state.messages,
    })),
}));
