import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  User,
  AuthTokens,
  SecurityEvent,
  DeviceSession,
  SignUpRequest,
  SignInRequest,
  PasswordResetRequest,
  ResetPasswordRequest,
  UpdateProfileRequest,
  UpdateEmailRequest,
  UpdatePasswordRequest,
  createAuthProvider,
} from "@/services/auth/localAuthProvider";

interface AuthState {
  // State
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  requireTotp: boolean;

  // Actions
  signUp: (data: SignUpRequest) => Promise<{ needEmailVerify: boolean }>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  signIn: (data: SignInRequest) => Promise<void>;
  signOut: () => Promise<void>;
  requestPasswordReset: (data: PasswordResetRequest) => Promise<void>;
  resetPassword: (data: ResetPasswordRequest) => Promise<void>;
  enableTotp: () => Promise<{
    secret: string;
    otpauthUrl: string;
    recoveryCodes: string[];
  }>;
  verifyTotp: (code: string) => Promise<void>;
  disableTotp: (code: string) => Promise<void>;
  updateProfile: (data: UpdateProfileRequest) => Promise<void>;
  updateEmail: (data: UpdateEmailRequest) => Promise<void>;
  updatePassword: (data: UpdatePasswordRequest) => Promise<void>;
  getSecurityLog: () => Promise<SecurityEvent[]>;
  getDevices: () => Promise<DeviceSession[]>;
  revokeDevice: (sessionId: string) => Promise<void>;
  refreshSession: () => Promise<void>;
  checkSession: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

// Get auth provider based on environment
const getAuthProvider = () => {
  const providerType = process.env.NEXT_PUBLIC_AUTH_PROVIDER || "local";
  return createAuthProvider(providerType as "local" | "api");
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      requireTotp: false,

      // Sign up action
      signUp: async (data: SignUpRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.signUp(data);
          set({ isLoading: false });
          return { needEmailVerify: result.needEmailVerify };
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : "Sign up failed",
          });
          throw error;
        }
      },

      // Verify email action
      verifyEmail: async (email: string, code: string) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.verifyEmail({ email, code });
          set({
            user: result.user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error
                ? error.message
                : "Email verification failed",
          });
          throw error;
        }
      },

      // Sign in action
      signIn: async (data: SignInRequest) => {
        set({ isLoading: true, error: null, requireTotp: false });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.signIn(data);

          if (result.requireTotp) {
            set({
              requireTotp: true,
              isLoading: false,
            });
            return;
          }

          // Calculate expiration based on Remember Me preference
          const sessionTTL = process.env.NEXT_PUBLIC_AUTH_SESSION_TTL_MIN
            ? parseInt(process.env.NEXT_PUBLIC_AUTH_SESSION_TTL_MIN) * 60 * 1000
            : data.remember
              ? 30 * 24 * 60 * 60 * 1000
              : 24 * 60 * 60 * 1000; // 30 days or 1 day

          const tokens: AuthTokens = {
            accessToken: result.accessToken,
            refreshToken: result.refreshToken,
            expiresAt: Date.now() + sessionTTL,
          };

          set({
            user: result.user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            requireTotp: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : "Sign in failed",
          });
          throw error;
        }
      },

      // Sign out action
      signOut: async () => {
        set({ isLoading: true });
        try {
          const authProvider = getAuthProvider();
          await authProvider.signOut();
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
            requireTotp: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : "Sign out failed",
          });
          throw error;
        }
      },

      // Request password reset
      requestPasswordReset: async (data: PasswordResetRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.requestPasswordReset(data);
          set({ isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error
                ? error.message
                : "Password reset request failed",
          });
          throw error;
        }
      },

      // Reset password
      resetPassword: async (data: ResetPasswordRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.resetPassword(data);
          set({ isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Password reset failed",
          });
          throw error;
        }
      },

      // Enable TOTP
      enableTotp: async () => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.enableTotp();
          set({ isLoading: false });
          return result;
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Failed to enable 2FA",
          });
          throw error;
        }
      },

      // Verify TOTP
      verifyTotp: async (code: string) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.verifyTotp({ code });

          // Update user in state
          const { user } = get();
          if (user) {
            set({
              user: { ...user, totpEnabled: true },
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error
                ? error.message
                : "2FA verification failed",
          });
          throw error;
        }
      },

      // Disable TOTP
      disableTotp: async (code: string) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.disableTotp({ code });

          // Update user in state
          const { user } = get();
          if (user) {
            set({
              user: { ...user, totpEnabled: false },
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Failed to disable 2FA",
          });
          throw error;
        }
      },

      // Update profile
      updateProfile: async (data: UpdateProfileRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.updateProfile(data);
          set({
            user: result.user,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Profile update failed",
          });
          throw error;
        }
      },

      // Update email
      updateEmail: async (data: UpdateEmailRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          const result = await authProvider.updateEmail(data);
          set({
            user: result.user,
            isLoading: false,
          });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Email update failed",
          });
          throw error;
        }
      },

      // Update password
      updatePassword: async (data: UpdatePasswordRequest) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.updatePassword(data);
          set({ isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error ? error.message : "Password update failed",
          });
          throw error;
        }
      },

      // Get security log
      getSecurityLog: async () => {
        try {
          const authProvider = getAuthProvider();
          return await authProvider.getSecurityLog();
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to load security log",
          });
          throw error;
        }
      },

      // Get devices
      getDevices: async () => {
        try {
          const authProvider = getAuthProvider();
          return await authProvider.getDevices();
        } catch (error) {
          set({
            error:
              error instanceof Error ? error.message : "Failed to load devices",
          });
          throw error;
        }
      },

      // Revoke device
      revokeDevice: async (sessionId: string) => {
        set({ isLoading: true, error: null });
        try {
          const authProvider = getAuthProvider();
          await authProvider.revokeDevice({ sessionId });
          set({ isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error:
              error instanceof Error
                ? error.message
                : "Failed to revoke device",
          });
          throw error;
        }
      },

      // Refresh session
      refreshSession: async () => {
        try {
          const { tokens } = get();
          if (!tokens) {
            throw new Error("No refresh token available");
          }

          const authProvider = getAuthProvider();
          const newTokens = await authProvider.refresh();

          set({
            tokens: {
              accessToken: newTokens.accessToken,
              refreshToken: newTokens.refreshToken,
              expiresAt: Date.now() + 24 * 60 * 60 * 1000,
            },
          });
        } catch (error) {
          // If refresh fails, sign out user
          await get().signOut();
          throw error;
        }
      },

      // Check session validity
      checkSession: async () => {
        try {
          const authProvider = getAuthProvider();
          const session = await authProvider.getSession();

          if (session.user && session.accessToken) {
            const tokens: AuthTokens = {
              accessToken: session.accessToken,
              refreshToken: session.refreshToken || "",
              expiresAt: Date.now() + 24 * 60 * 60 * 1000,
            };

            set({
              user: session.user,
              tokens,
              isAuthenticated: true,
            });
          } else {
            set({
              user: null,
              tokens: null,
              isAuthenticated: false,
            });
          }
        } catch {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
          });
        }
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Set loading
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: "ziggy_auth_store",
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);

// Auto-check session on app load
if (typeof window !== "undefined") {
  useAuthStore.getState().checkSession();
}

// Auto-refresh tokens before expiry
setInterval(() => {
  const { tokens, isAuthenticated, refreshSession } = useAuthStore.getState();
  if (isAuthenticated && tokens) {
    const timeToExpiry = tokens.expiresAt - Date.now();
    // Refresh if expiring in next 5 minutes
    if (timeToExpiry < 5 * 60 * 1000 && timeToExpiry > 0) {
      refreshSession().catch(() => {
        // Handle refresh failure silently - user will be signed out
      });
    }
  }
}, 60 * 1000); // Check every minute
