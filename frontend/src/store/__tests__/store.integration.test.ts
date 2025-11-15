import { renderHook, act } from "@testing-library/react";
import { useAuthStore } from "@/store/authStore";
import { useChatStore } from "@/store/chatStore";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

describe("Store Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset chat store state before each test
    useChatStore.getState().clearMessages();
  });

  describe("useAuthStore", () => {
    it("should initialize with default state", () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should handle loading state", () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it("should clear errors", () => {
      const { result } = renderHook(() => useAuthStore());

      // Simulate an error state (normally set by async actions)
      const store = useAuthStore.getState();
      store.error = "Test error";

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it("should have sign up functionality", () => {
      const { result } = renderHook(() => useAuthStore());

      expect(typeof result.current.signUp).toBe("function");
      expect(typeof result.current.signIn).toBe("function");
      expect(typeof result.current.signOut).toBe("function");
    });

    it("should have password reset functionality", () => {
      const { result } = renderHook(() => useAuthStore());

      expect(typeof result.current.requestPasswordReset).toBe("function");
      expect(typeof result.current.resetPassword).toBe("function");
    });

    it("should have profile management functionality", () => {
      const { result } = renderHook(() => useAuthStore());

      expect(typeof result.current.updateProfile).toBe("function");
      expect(typeof result.current.updateEmail).toBe("function");
      expect(typeof result.current.updatePassword).toBe("function");
    });

    it("should have security features", () => {
      const { result } = renderHook(() => useAuthStore());

      expect(typeof result.current.enableTotp).toBe("function");
      expect(typeof result.current.verifyTotp).toBe("function");
      expect(typeof result.current.disableTotp).toBe("function");
      expect(typeof result.current.getSecurityLog).toBe("function");
      expect(typeof result.current.getDevices).toBe("function");
      expect(typeof result.current.revokeDevice).toBe("function");
    });
  });

  describe("useChatStore", () => {
    it("should initialize with default state", () => {
      const { result } = renderHook(() => useChatStore());

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should add messages correctly", () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.addMessage({
          content: "Hello",
          role: "user",
        });
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toBe("Hello");
      expect(result.current.messages[0].role).toBe("user");
    });

    it("should handle loading state", () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it("should handle errors", () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setError("Failed to send message");
      });

      expect(result.current.error).toBe("Failed to send message");

      act(() => {
        result.current.setError(null);
      });

      expect(result.current.error).toBeNull();
    });

    it("should clear messages", () => {
      const { result } = renderHook(() => useChatStore());

      // Add some messages first
      act(() => {
        result.current.addMessage({
          content: "Hello",
          role: "user",
        });
        result.current.addMessage({
          content: "Hi!",
          role: "assistant",
        });
      });

      expect(result.current.messages).toHaveLength(2);

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toEqual([]);
    });

    it("should maintain message order", () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.addMessage({
          content: "First message",
          role: "user",
        });
        result.current.addMessage({
          content: "Second message",
          role: "assistant",
        });
        result.current.addMessage({
          content: "Third message",
          role: "user",
        });
      });

      expect(result.current.messages).toHaveLength(3);
      expect(result.current.messages[0].content).toBe("First message");
      expect(result.current.messages[1].content).toBe("Second message");
      expect(result.current.messages[2].content).toBe("Third message");
    });

    it("should have chat functionality", () => {
      const { result } = renderHook(() => useChatStore());

      expect(typeof result.current.sendMessage).toBe("function");
      expect(typeof result.current.sendRAGQuery).toBe("function");
      expect(typeof result.current.sendAgentQuery).toBe("function");
      expect(typeof result.current.updateMessage).toBe("function");
    });
  });

  describe("Store error handling", () => {
    it("should handle auth store errors gracefully", () => {
      const { result } = renderHook(() => useAuthStore());

      // Should not throw when calling functions
      expect(() => {
        result.current.clearError();
        result.current.setLoading(false);
      }).not.toThrow();
    });

    it("should handle chat store errors gracefully", () => {
      const { result } = renderHook(() => useChatStore());

      // Should not throw when calling functions
      expect(() => {
        result.current.setError(null);
        result.current.setLoading(false);
        result.current.clearMessages();
      }).not.toThrow();
    });
  });
});
