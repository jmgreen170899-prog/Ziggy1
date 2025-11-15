// Local Authentication Provider for ZiggyAI
// Designed to be easily swappable with real API provider later

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  role: "user" | "admin";
  emailVerified: boolean;
  totpEnabled: boolean;
  totpSecret?: string | null;
  createdAt: string;
  lastLoginAt: string;
  timezone?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface SecurityEvent {
  id: string;
  type:
    | "sign_in"
    | "sign_out"
    | "password_change"
    | "totp_enable"
    | "totp_disable"
    | "device_revoke"
    | "failed_login"
    | "failed_signup"
    | "password_reset_requested";
  timestamp: string;
  ip: string;
  userAgent: string;
  location?: string;
  success: boolean;
  details?: string;
}

export interface DeviceSession {
  id: string;
  userId: string;
  userAgent: string;
  ip: string;
  location: string;
  lastActive: string;
  isCurrent: boolean;
  createdAt: string;
  deviceInfo?: {
    os?: string;
    browser?: string;
    device?: string;
  };
}

export interface SignUpRequest {
  email: string;
  password: string;
  name: string;
}

export interface SignUpResponse {
  user: User;
  needEmailVerify: boolean;
}

export interface VerifyEmailRequest {
  email: string;
  code: string;
}

export interface SignInRequest {
  email: string;
  password: string;
  remember?: boolean;
  totpCode?: string;
}

export interface SignInResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  requireTotp?: boolean;
}

export interface PasswordResetRequest {
  email: string;
}

export interface ResetPasswordRequest {
  email: string;
  code: string;
  newPassword: string;
}

export interface TotpSetupResponse {
  secret: string;
  otpauthUrl: string;
  recoveryCodes: string[];
}

export interface UpdateProfileRequest {
  name?: string;
  avatarUrl?: string;
  timezone?: string;
}

export interface UpdateEmailRequest {
  newEmail: string;
  code?: string;
}

export interface UpdatePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

interface PendingVerification {
  email: string;
  code: string;
  expiresAt: number;
}

interface PasswordResetData {
  code: string;
  expiresAt: number;
}

interface RateLimitData {
  [key: string]: boolean;
}

// Storage keys
const STORAGE_KEYS = {
  USER: "ziggy_auth_user",
  TOKENS: "ziggy_auth_tokens",
  SECURITY_LOG: "ziggy_security_log",
  DEVICE_SESSIONS: "ziggy_device_sessions",
  RATE_LIMITS: "ziggy_auth_rate_limits",
  PENDING_VERIFICATION: "ziggy_pending_verification",
  TOTP_SECRETS: "ziggy_totp_secrets",
} as const;

// Rate limiting configuration
const RATE_LIMITS = {
  SIGN_IN_ATTEMPTS: 5,
  PASSWORD_RESET_REQUESTS: 3,
  EMAIL_VERIFICATION_REQUESTS: 3,
  LOCKOUT_DURATION: 15 * 60 * 1000, // 15 minutes
};

// Local data generators (admin-only mode)
const generateSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const generateToken = () =>
  `local_token_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;

// Simple client-side password hashing (local dev purposes only)
const hashPassword = async (password: string): Promise<string> => {
  const encoder = new TextEncoder();
  const data = encoder.encode(password + "ziggy_salt");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
};

// Simulate network delay
const simulateDelay = (min = 200, max = 600) =>
  new Promise((resolve) =>
    setTimeout(resolve, Math.random() * (max - min) + min),
  );

// Local IPs and locations for device sessions
const DEV_IPS = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "203.0.113.45"];
const DEV_LOCATIONS = ["New York, NY", "London, UK", "Tokyo, JP", "Sydney, AU"];

// Helper functions for localStorage operations
const getStorageItem = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
};

const setStorageItem = (key: string, value: unknown): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn("Failed to save to localStorage:", error);
  }
};

// Rate limiting helpers
const checkRateLimit = (action: string, limit: number): boolean => {
  const rateLimits = getStorageItem<RateLimitData>(
    STORAGE_KEYS.RATE_LIMITS,
    {},
  );
  const key = `${action}_${Date.now()}`;
  const now = Date.now();

  // Clean old entries
  Object.keys(rateLimits).forEach((k) => {
    if (
      now - parseInt(k.split("_").pop() || "0") >
      RATE_LIMITS.LOCKOUT_DURATION
    ) {
      delete rateLimits[k];
    }
  });

  // Count recent attempts
  const recentAttempts = Object.keys(rateLimits).filter((k) =>
    k.startsWith(action),
  ).length;

  if (recentAttempts >= limit) {
    throw new Error(`Too many attempts. Please try again later.`);
  }

  rateLimits[key] = true;
  setStorageItem(STORAGE_KEYS.RATE_LIMITS, rateLimits);
  return true;
};

// Security event logging
const logSecurityEvent = (
  event: Omit<
    SecurityEvent,
    "id" | "timestamp" | "ip" | "userAgent" | "location"
  >,
): void => {
  const events = getStorageItem<SecurityEvent[]>(STORAGE_KEYS.SECURITY_LOG, []);
  const newEvent: SecurityEvent = {
    ...event,
    id: `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString(),
    ip: DEV_IPS[Math.floor(Math.random() * DEV_IPS.length)],
    userAgent: navigator.userAgent,
    location: DEV_LOCATIONS[Math.floor(Math.random() * DEV_LOCATIONS.length)],
  };

  events.unshift(newEvent);
  // Keep only last 100 events
  if (events.length > 100) {
    events.splice(100);
  }

  setStorageItem(STORAGE_KEYS.SECURITY_LOG, events);
};

// Local Authentication Provider Implementation
export class LocalAuthProvider {
  async signUp(data: SignUpRequest): Promise<SignUpResponse> {
    await simulateDelay();

    // Disable public registration - admin access only
    logSecurityEvent({
      type: "failed_signup",
      success: false,
      details: `Registration attempt blocked for ${data.email}`,
    });

    throw new Error(
      "Registration is disabled. Contact administrator for access.",
    );
  }

  async verifyEmail({
    email,
    code,
  }: VerifyEmailRequest): Promise<{ user: User }> {
    await simulateDelay();

    const pending = getStorageItem<PendingVerification | null>(
      STORAGE_KEYS.PENDING_VERIFICATION,
      null,
    );
    if (!pending || pending.email !== email || pending.code !== code) {
      throw new Error("Invalid verification code");
    }

    if (Date.now() > pending.expiresAt) {
      throw new Error("Verification code has expired");
    }

    // Update user as verified
    const users = getStorageItem<User[]>("ziggy_local_users", []);
    const userIndex = users.findIndex((u) => u.email === email);
    if (userIndex === -1) {
      throw new Error("User not found");
    }

    users[userIndex].emailVerified = true;
    setStorageItem("ziggy_local_users", users);

    // Clear pending verification
    localStorage.removeItem(STORAGE_KEYS.PENDING_VERIFICATION);

    return { user: users[userIndex] };
  }

  async signIn({
    email,
    password,
    remember = false,
  }: Omit<SignInRequest, "totpCode">): Promise<SignInResponse> {
    await simulateDelay();

    // Check rate limiting
    checkRateLimit("sign_in", RATE_LIMITS.SIGN_IN_ATTEMPTS);

    // Environment-based admin authentication
    const isDevMode = process.env.NODE_ENV === "development";
    const adminEnabled =
      process.env.NEXT_PUBLIC_AUTH_ENABLE_ADMIN === "true" || isDevMode;

    // Admin credentials check
    const isAdminEmail =
      email.toLowerCase() === "admin@ziggyclean.com" ||
      email.toLowerCase() === "admin";
    const isAdminPassword = password === "admin";

    // Dev user credentials check
    const isDevEmail =
      email.toLowerCase() === "user" || email.toLowerCase() === "dev@localhost";
    const isDevPassword = password === "user" || password === "secret";

    if (
      adminEnabled &&
      ((isAdminEmail && isAdminPassword) || (isDevEmail && isDevPassword))
    ) {
      // Allow admin or dev access
    } else {
      logSecurityEvent({
        type: "failed_login",
        success: false,
        details: `Invalid credentials - ${adminEnabled ? "admin access only" : "authentication disabled"}`,
      });

      if (!adminEnabled) {
        throw new Error(
          "Authentication is currently disabled. Please contact the administrator.",
        );
      } else {
        throw new Error("Access denied. Only administrator access is allowed.");
      }
    }

    // Create user based on credentials
    const user: User =
      isDevEmail && isDevPassword
        ? {
            id: "dev-user-001",
            email: "dev@localhost",
            name: "ZiggyAI Dev User",
            role: "admin", // Give admin role for paper trading access
            emailVerified: true,
            totpEnabled: false,
            totpSecret: null,
            avatarUrl: "",
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            createdAt: "2024-01-01T00:00:00Z",
            lastLoginAt: new Date().toISOString(),
          }
        : {
            id: "admin-001",
            email: "admin@ziggyclean.com",
            name: "ZiggyClean Administrator",
            role: "admin",
            emailVerified: true,
            totpEnabled: false,
            totpSecret: null,
            avatarUrl: "",
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            createdAt: "2024-01-01T00:00:00Z",
            lastLoginAt: new Date().toISOString(),
          };

    // Generate tokens
    const accessToken = generateToken();
    const refreshToken = generateToken();
    const expiresAt =
      Date.now() + (remember ? 30 * 24 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000); // 30 days or 1 day

    const tokens: AuthTokens = {
      accessToken,
      refreshToken,
      expiresAt,
    };

    // Store tokens and session
    setStorageItem(STORAGE_KEYS.TOKENS, tokens);
    setStorageItem(STORAGE_KEYS.USER, user);

    // Create device session
    const deviceSession: DeviceSession = {
      id: generateSessionId(),
      userId: user.id,
      userAgent: navigator.userAgent,
      ip: "127.0.0.1", // Local IP
      location: "Local Development",
      lastActive: new Date().toISOString(),
      isCurrent: true,
      createdAt: new Date().toISOString(),
      deviceInfo: {
        os: "Unknown",
        browser: "Browser",
        device: "Desktop",
      },
    };

    const sessions = getStorageItem<DeviceSession[]>(
      STORAGE_KEYS.DEVICE_SESSIONS,
      [],
    );
    sessions.push(deviceSession);
    setStorageItem(STORAGE_KEYS.DEVICE_SESSIONS, sessions);

    logSecurityEvent({
      type: "sign_in",
      success: true,
      details: "Admin login successful",
    });

    return {
      user: user,
      accessToken,
      refreshToken,
    };
  }

  async signOut(): Promise<void> {
    await simulateDelay(100, 200);

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (user) {
      logSecurityEvent({
        type: "sign_out",
        success: true,
        details: "User signed out",
      });
    }

    // Clear tokens and user
    localStorage.removeItem(STORAGE_KEYS.TOKENS);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }

  async requestPasswordReset({
    email,
  }: PasswordResetRequest): Promise<{ ok: true }> {
    await simulateDelay();

    checkRateLimit("password_reset", RATE_LIMITS.PASSWORD_RESET_REQUESTS);

    // Generate and store reset code
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const resetData: PasswordResetData = {
      code,
      expiresAt: Date.now() + 15 * 60 * 1000, // 15 minutes
    };

    setStorageItem(`ziggy_local_password_reset_${email}`, resetData);

    logSecurityEvent({
      type: "password_reset_requested",
      success: true,
      details: `Password reset code generated for ${email}`,
    });

    return { ok: true };
  }

  async resetPassword({
    email,
    code,
    newPassword,
  }: ResetPasswordRequest): Promise<{ ok: true }> {
    await simulateDelay();

    const resetData = getStorageItem<PasswordResetData | null>(
      `ziggy_local_password_reset_${email}`,
      null,
    );
    if (!resetData || resetData.code !== code) {
      throw new Error("Invalid reset code");
    }
    if (Date.now() > resetData.expiresAt) {
      throw new Error("Reset code has expired");
    }

    const newPasswordHash = await hashPassword(newPassword);
    setStorageItem(`ziggy_local_password_${email}`, newPasswordHash);

    logSecurityEvent({
      type: "password_change",
      success: true,
      details: "Password reset successfully",
    });

    return { ok: true };
  }

  async enableTotp(): Promise<TotpSetupResponse> {
    await simulateDelay();

    // Generate TOTP secret and backup codes (for local dev)
    const secret = Math.random().toString(36).substring(2, 18).toUpperCase();
    const recoveryCodes = Array.from({ length: 8 }, () =>
      Math.random().toString(36).substring(2, 11),
    );

    const otpauthUrl = `otpauth://totp/ZiggyAI:dev-user?secret=${secret}&issuer=ZiggyAI`;

    setStorageItem(STORAGE_KEYS.TOTP_SECRETS, { secret, recoveryCodes });

    logSecurityEvent({
      type: "totp_enable",
      success: true,
      details: "Two-factor authentication enabled",
    });

    return { secret, otpauthUrl, recoveryCodes };
  }

  async verifyTotp({ code }: { code: string }): Promise<{ ok: true }> {
    await simulateDelay();

    const totpData = getStorageItem<{
      secret: string;
      recoveryCodes: string[];
    } | null>(STORAGE_KEYS.TOTP_SECRETS, null);
    if (!totpData) {
      throw new Error("TOTP not set up");
    }

    // Verify format (dummy verification for local dev)
    if (!/^[0-9]{6}$/.test(code)) {
      throw new Error("Invalid code format");
    }

    logSecurityEvent({
      type: "totp_enable",
      success: true,
      details: "TOTP verified",
    });

    return { ok: true };
  }

  // Overload to accept either a string or an object with code
  async disableTotp(code: string): Promise<{ ok: true }>;
  async disableTotp(data: { code: string }): Promise<{ ok: true }>;
  async disableTotp(arg: string | { code: string }): Promise<{ ok: true }> {
    await simulateDelay();
    const code = typeof arg === "string" ? arg : arg?.code;
    // Accept any code in local dev
    if (!code) {
      throw new Error("Verification code required");
    }

    localStorage.removeItem(STORAGE_KEYS.TOTP_SECRETS);

    logSecurityEvent({
      type: "totp_disable",
      success: true,
      details: "Two-factor authentication disabled",
    });

    return { ok: true };
  }

  async updateProfile(
    data: UpdateProfileRequest,
  ): Promise<{ ok: true; user: User }> {
    await simulateDelay();

    const currentUser = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!currentUser) {
      throw new Error("Not authenticated");
    }

    const updatedUser: User = { ...currentUser, ...data };
    setStorageItem(STORAGE_KEYS.USER, updatedUser);

    logSecurityEvent({
      type: "sign_in",
      success: true,
      details: "Profile updated",
    });

    return { ok: true, user: updatedUser };
  }

  async updateEmail(
    data: UpdateEmailRequest,
  ): Promise<{ ok: true; user: User }> {
    await simulateDelay();

    const currentUser = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!currentUser) {
      throw new Error("Not authenticated");
    }

    // Generate verification code
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    const pending: PendingVerification = {
      email: data.newEmail,
      code,
      expiresAt: Date.now() + 15 * 60 * 1000,
    };

    setStorageItem(STORAGE_KEYS.PENDING_VERIFICATION, pending);

    logSecurityEvent({
      type: "sign_in",
      success: true,
      details: "Email update requested",
    });

    // For local dev, immediately update
    const updatedUser: User = { ...currentUser, email: data.newEmail };
    setStorageItem(STORAGE_KEYS.USER, updatedUser);

    return { ok: true, user: updatedUser };
  }

  async updatePassword(data: UpdatePasswordRequest): Promise<{ ok: true }> {
    await simulateDelay();

    const { currentPassword, newPassword } = data;
    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    // Verify current password
    const storedPasswordHash = getStorageItem(
      `ziggy_local_password_${user.id}`,
      "",
    );
    const currentPasswordHash = await hashPassword(currentPassword);

    if (storedPasswordHash !== currentPasswordHash) {
      throw new Error("Current password is incorrect");
    }

    if (newPassword.length < 8) {
      throw new Error("New password must be at least 8 characters long");
    }

    // Update password
    const newPasswordHash = await hashPassword(newPassword);
    setStorageItem(`ziggy_local_password_${user.id}`, newPasswordHash);

    logSecurityEvent({
      type: "password_change",
      success: true,
      details: "Password changed successfully",
    });

    return { ok: true };
  }

  // --- Methods to satisfy store expectations in dev/local mode ---
  async getSecurityLog(): Promise<SecurityEvent[]> {
    await simulateDelay(50, 150);
    return getStorageItem<SecurityEvent[]>(STORAGE_KEYS.SECURITY_LOG, []);
  }

  async getDevices(): Promise<DeviceSession[]> {
    await simulateDelay(50, 150);
    return getStorageItem<DeviceSession[]>(STORAGE_KEYS.DEVICE_SESSIONS, []);
  }

  async revokeDevice({
    sessionId,
  }: {
    sessionId: string;
  }): Promise<{ ok: true }> {
    await simulateDelay(50, 150);
    const sessions = getStorageItem<DeviceSession[]>(
      STORAGE_KEYS.DEVICE_SESSIONS,
      [],
    );
    const filtered = sessions.filter((s) => s.id !== sessionId);
    setStorageItem(STORAGE_KEYS.DEVICE_SESSIONS, filtered);
    logSecurityEvent({
      type: "device_revoke",
      success: true,
      details: `Revoked ${sessionId}`,
    });
    return { ok: true };
  }

  async refresh(): Promise<{ accessToken: string; refreshToken: string }> {
    await simulateDelay(50, 150);
    const tokens = getStorageItem<AuthTokens | null>(STORAGE_KEYS.TOKENS, null);
    if (!tokens) throw new Error("No tokens");
    const newTokens = {
      accessToken: generateToken(),
      refreshToken: generateToken(),
    };
    setStorageItem(STORAGE_KEYS.TOKENS, {
      ...tokens,
      ...newTokens,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    });
    return newTokens;
  }

  async getSession(): Promise<{
    user: User | null;
    accessToken?: string;
    refreshToken?: string;
  }> {
    await simulateDelay(50, 150);
    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    const tokens = getStorageItem<AuthTokens | null>(STORAGE_KEYS.TOKENS, null);
    return {
      user,
      accessToken: tokens?.accessToken,
      refreshToken: tokens?.refreshToken,
    };
  }
}

// Export singleton instance
export const localAuthProvider = new LocalAuthProvider();

// Provider factory function for easy swapping
export const createAuthProvider = (type: "local" | "api" = "local") => {
  switch (type) {
    case "local":
      return localAuthProvider;
    case "api":
      // TODO: Return real API provider when implemented
      throw new Error("API provider not yet implemented");
    default:
      return localAuthProvider;
  }
};
