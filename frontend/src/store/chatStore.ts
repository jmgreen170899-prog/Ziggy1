import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  ChatMessage,
  ChatState,
  RAGQueryRequest,
  RAGQueryResponse,
  AgentRequest,
  AgentResponse,
} from "@/types/api";
import { apiClient } from "@/services/api";
import { streamChatCompletion } from "@/services/chatStream";

interface ChatStore extends ChatState {
  // Actions
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  sendMessage: (content: string) => Promise<void>;
  sendStreamingMessage: (content: string) => Promise<void>;
  sendRAGQuery: (content: string) => Promise<void>;
  sendAgentQuery: (content: string) => Promise<void>;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      error: null,
      currentModel: "ollama",

      // Actions
      addMessage: (message) => {
        const newMessage: ChatMessage = {
          ...message,
          id: generateId(),
          timestamp: new Date().toISOString(),
        };

        set((state) => ({
          messages: [...state.messages, newMessage],
        }));
      },

      sendMessage: async (content: string) => {
        const { addMessage, sendStreamingMessage } = get();

        // Add user message
        addMessage({
          content,
          role: "user",
        });

        // Use streaming chat by default for better UX
        await sendStreamingMessage(content);
      },

      sendStreamingMessage: async (content: string) => {
        const { messages, updateMessage } = get();

        set({ isLoading: true, error: null });

        // Add loading assistant message
        const assistantMessage: ChatMessage = {
          id: generateId(),
          content: "",
          role: "assistant",
          timestamp: new Date().toISOString(),
          isLoading: true,
        };

        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        try {
          // Build message history for context
          const chatMessages = messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => ({
              role: m.role as "user" | "assistant",
              content: m.content,
            }));

          // Add the new user message
          chatMessages.push({
            role: "user",
            content,
          });

          // Stream the response
          await streamChatCompletion(
            {
              messages: chatMessages,
              temperature: 0.7,
              max_tokens: 2000,
              stream: true,
            },
            {
              onChunk: (chunk: string) => {
                // Append chunk to assistant message
                updateMessage(assistantMessage.id, {
                  content:
                    get().messages.find((m) => m.id === assistantMessage.id)
                      ?.content + chunk || chunk,
                });
              },
              onComplete: (fullContent: string) => {
                // Finalize assistant message
                updateMessage(assistantMessage.id, {
                  content: fullContent,
                  isLoading: false,
                });
                set({ isLoading: false });
              },
              onError: (error: Error) => {
                console.error("Streaming failed:", error);
                set({ error: `Failed to stream response: ${error.message}` });

                updateMessage(assistantMessage.id, {
                  content:
                    "Sorry, I encountered an error while streaming the response. Please try again.",
                  isLoading: false,
                });
                set({ isLoading: false });
              },
            },
          );
        } catch (error) {
          console.error("Chat streaming error:", error);
          set({
            error: "Failed to get response from ZiggyAI. Please try again.",
          });

          updateMessage(assistantMessage.id, {
            content:
              "Sorry, I encountered an error while processing your request. Please try again.",
            isLoading: false,
          });
          set({ isLoading: false });
        }
      },

      sendRAGQuery: async (content: string) => {
        const { updateMessage } = get();

        set({ isLoading: true, error: null });

        // Add loading assistant message
        const assistantMessage: ChatMessage = {
          id: generateId(),
          content: "",
          role: "assistant",
          timestamp: new Date().toISOString(),
          isLoading: true,
        };

        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        try {
          const request: RAGQueryRequest = {
            query: content,
            context: "chat_interface",
            max_tokens: 1000,
          };

          const response: RAGQueryResponse = await apiClient.queryRAG(request);

          // Update the assistant message with the response
          updateMessage(assistantMessage.id, {
            content: response.response,
            sources: response.sources,
            confidence: response.confidence,
            isLoading: false,
          });
        } catch (error) {
          console.error("RAG query failed:", error);
          set({
            error: "Failed to get response from ZiggyAI. Please try again.",
          });

          // Update the assistant message with error
          updateMessage(assistantMessage.id, {
            content:
              "Sorry, I encountered an error while processing your request. Please try again.",
            isLoading: false,
          });
        } finally {
          set({ isLoading: false });
        }
      },

      sendAgentQuery: async (content: string) => {
        const { addMessage, updateMessage } = get();

        set({ isLoading: true, error: null });

        // Add loading assistant message
        const assistantMessage: ChatMessage = {
          id: generateId(),
          content: "",
          role: "assistant",
          timestamp: new Date().toISOString(),
          isLoading: true,
        };

        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        try {
          const request: AgentRequest = {
            message: content,
            agent_type: "financial_advisor",
            context: { interface: "chat" },
          };

          const response: AgentResponse = await apiClient.queryAgent(request);

          // Update the assistant message with the response
          updateMessage(assistantMessage.id, {
            content: response.response,
            isLoading: false,
          });

          // If there are suggestions, add them as a follow-up message
          if (response.suggestions && response.suggestions.length > 0) {
            setTimeout(() => {
              addMessage({
                content: `💡 **Suggestions:**\n${response.suggestions!.join("\n")}`,
                role: "assistant",
              });
            }, 500);
          }
        } catch (error) {
          console.error("Agent query failed:", error);
          set({
            error:
              "Failed to get response from ZiggyAI Agent. Please try again.",
          });

          // Update the assistant message with error
          updateMessage(assistantMessage.id, {
            content:
              "Sorry, I encountered an error while processing your request. Please try again.",
            isLoading: false,
          });
        } finally {
          set({ isLoading: false });
        }
      },

      clearMessages: () => {
        set({ messages: [], error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      updateMessage: (id: string, updates: Partial<ChatMessage>) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg,
          ),
        }));
      },
    }),
    {
      name: "ziggy-chat-store",
      partialize: (state) => ({
        messages: state.messages,
        currentModel: state.currentModel,
      }),
    },
  ),
);
