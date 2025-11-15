// Mock Authentication Provider for ZiggyAI
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

// Mock data generators (admin-only mode)
const generateSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const generateToken = () =>
  `mock_token_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;

// Simple client-side password hashing (for mock purposes only)
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

// Mock IPs and locations for device sessions
const MOCK_IPS = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "203.0.113.45"];
const MOCK_LOCATIONS = [
  "New York, NY",
  "London, UK",
  "Tokyo, JP",
  "Sydney, AU",
];

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
    ip: MOCK_IPS[Math.floor(Math.random() * MOCK_IPS.length)],
    userAgent: navigator.userAgent,
    location: MOCK_LOCATIONS[Math.floor(Math.random() * MOCK_LOCATIONS.length)],
  };

  events.unshift(newEvent);
  // Keep only last 100 events
  if (events.length > 100) {
    events.splice(100);
  }

  setStorageItem(STORAGE_KEYS.SECURITY_LOG, events);
};

// Mock Authentication Provider Implementation
export class MockAuthProvider {
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
    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    const userIndex = users.findIndex((u) => u.email === email);
    if (userIndex === -1) {
      throw new Error("User not found");
    }

    users[userIndex].emailVerified = true;
    setStorageItem("ziggy_mock_users", users);

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
      ip: "127.0.0.1", // Mock IP
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

    // Mark current session as inactive
    const deviceSessions = getStorageItem<DeviceSession[]>(
      STORAGE_KEYS.DEVICE_SESSIONS,
      [],
    );
    deviceSessions.forEach((session) => {
      if (session.isCurrent && session.userId === user?.id) {
        session.isCurrent = false;
      }
    });
    setStorageItem(STORAGE_KEYS.DEVICE_SESSIONS, deviceSessions);

    // Clear auth data
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.TOKENS);
  }

  async requestPasswordReset({
    email,
  }: PasswordResetRequest): Promise<{ ok: boolean }> {
    await simulateDelay();

    // Disable password reset - admin access only
    logSecurityEvent({
      type: "password_reset_requested",
      success: false,
      details: `Password reset blocked for ${email}`,
    });

    throw new Error(
      "Password reset is disabled. Contact administrator for assistance.",
    );
  }

  async resetPassword({
    email,
    code,
    newPassword,
  }: ResetPasswordRequest): Promise<{ ok: boolean }> {
    await simulateDelay();

    const resetData = getStorageItem<PasswordResetData | null>(
      `ziggy_password_reset_${email}`,
      null,
    );
    if (
      !resetData ||
      resetData.code !== code ||
      Date.now() > resetData.expiresAt
    ) {
      throw new Error("Invalid or expired reset code");
    }

    if (newPassword.length < 8) {
      throw new Error("Password must be at least 8 characters long");
    }

    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    const user = users.find(
      (u) => u.email.toLowerCase() === email.toLowerCase(),
    );

    if (!user) {
      throw new Error("User not found");
    }

    // Update password
    const hashedPassword = await hashPassword(newPassword);
    setStorageItem(`ziggy_mock_password_${user.id}`, hashedPassword);

    // Clear reset data
    localStorage.removeItem(`ziggy_password_reset_${email}`);

    logSecurityEvent({
      type: "password_change",
      success: true,
      details: "Password reset completed",
    });

    return { ok: true };
  }

  async getSession(): Promise<{
    user: User | null;
    accessToken?: string;
    refreshToken?: string;
  }> {
    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    const tokens = getStorageItem<AuthTokens | null>(STORAGE_KEYS.TOKENS, null);

    if (!user || !tokens) {
      return { user: null };
    }

    // Check token expiration
    if (Date.now() > tokens.expiresAt) {
      // Clear expired session
      await this.signOut();
      return { user: null };
    }

    return {
      user,
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    };
  }

  async refresh(): Promise<{ accessToken: string; refreshToken: string }> {
    await simulateDelay(100, 300);

    const tokens = getStorageItem<AuthTokens | null>(STORAGE_KEYS.TOKENS, null);
    if (!tokens || Date.now() > tokens.expiresAt) {
      throw new Error("Refresh token expired");
    }

    const newTokens: AuthTokens = {
      accessToken: generateToken(),
      refreshToken: generateToken(),
      expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 1 day
    };

    setStorageItem(STORAGE_KEYS.TOKENS, newTokens);

    return {
      accessToken: newTokens.accessToken,
      refreshToken: newTokens.refreshToken,
    };
  }

  async enableTotp(): Promise<TotpSetupResponse> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    const secret = `JBSWY3DPEHPK3PXP${Math.random().toString(36).substr(2, 8).toUpperCase()}`;
    const otpauthUrl = `otpauth://totp/ZiggyAI:${user.email}?secret=${secret}&issuer=ZiggyAI`;
    const recoveryCodes = Array.from({ length: 8 }, () =>
      Math.random().toString(36).substr(2, 8).toUpperCase(),
    );

    setStorageItem(`${STORAGE_KEYS.TOTP_SECRETS}_${user.id}`, {
      secret,
      recoveryCodes,
    });

    return {
      secret,
      otpauthUrl,
      recoveryCodes,
    };
  }

  async verifyTotp({ code }: { code: string }): Promise<{ enabled: boolean }> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    // Mock verification (in real implementation, use TOTP library)
    const validCodes = ["123456", "654321"];
    if (!validCodes.includes(code)) {
      throw new Error("Invalid authentication code");
    }

    // Enable TOTP for user
    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    const userIndex = users.findIndex((u) => u.id === user.id);
    if (userIndex !== -1) {
      users[userIndex].totpEnabled = true;
      setStorageItem("ziggy_mock_users", users);
      setStorageItem(STORAGE_KEYS.USER, users[userIndex]);
    }

    logSecurityEvent({
      type: "totp_enable",
      success: true,
      details: "Two-factor authentication enabled",
    });

    return { enabled: true };
  }

  async disableTotp({ code }: { code: string }): Promise<{ enabled: boolean }> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    // Mock verification
    const validCodes = ["123456", "654321"];
    if (!validCodes.includes(code)) {
      throw new Error("Invalid authentication code");
    }

    // Disable TOTP for user
    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    const userIndex = users.findIndex((u) => u.id === user.id);
    if (userIndex !== -1) {
      users[userIndex].totpEnabled = false;
      setStorageItem("ziggy_mock_users", users);
      setStorageItem(STORAGE_KEYS.USER, users[userIndex]);
    }

    // Remove TOTP secret
    localStorage.removeItem(`${STORAGE_KEYS.TOTP_SECRETS}_${user.id}`);

    logSecurityEvent({
      type: "totp_disable",
      success: true,
      details: "Two-factor authentication disabled",
    });

    return { enabled: false };
  }

  async getSecurityLog(): Promise<SecurityEvent[]> {
    await simulateDelay(100, 200);
    return getStorageItem<SecurityEvent[]>(STORAGE_KEYS.SECURITY_LOG, []);
  }

  async getDevices(): Promise<DeviceSession[]> {
    await simulateDelay(100, 200);
    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      return [];
    }

    const allSessions = getStorageItem<DeviceSession[]>(
      STORAGE_KEYS.DEVICE_SESSIONS,
      [],
    );
    return allSessions.filter((session) => session.userId === user.id);
  }

  async revokeDevice({
    sessionId,
  }: {
    sessionId: string;
  }): Promise<{ ok: boolean }> {
    await simulateDelay();

    const deviceSessions = getStorageItem<DeviceSession[]>(
      STORAGE_KEYS.DEVICE_SESSIONS,
      [],
    );
    const sessionIndex = deviceSessions.findIndex((s) => s.id === sessionId);

    if (sessionIndex === -1) {
      throw new Error("Session not found");
    }

    deviceSessions.splice(sessionIndex, 1);
    setStorageItem(STORAGE_KEYS.DEVICE_SESSIONS, deviceSessions);

    logSecurityEvent({
      type: "device_revoke",
      success: true,
      details: `Device session revoked: ${sessionId}`,
    });

    return { ok: true };
  }

  async updateProfile({
    name,
    avatarUrl,
    timezone,
  }: UpdateProfileRequest): Promise<{ user: User }> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    const userIndex = users.findIndex((u) => u.id === user.id);

    if (userIndex === -1) {
      throw new Error("User not found");
    }

    // Update user data
    if (name !== undefined) users[userIndex].name = name;
    if (avatarUrl !== undefined) users[userIndex].avatarUrl = avatarUrl;
    if (timezone !== undefined) users[userIndex].timezone = timezone;

    setStorageItem("ziggy_mock_users", users);
    setStorageItem(STORAGE_KEYS.USER, users[userIndex]);

    return { user: users[userIndex] };
  }

  async updateEmail({
    newEmail,
    code,
  }: UpdateEmailRequest): Promise<{ user: User }> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    // Check if email is already taken
    const users = getStorageItem<User[]>("ziggy_mock_users", []);
    if (
      users.some(
        (u) =>
          u.email.toLowerCase() === newEmail.toLowerCase() && u.id !== user.id,
      )
    ) {
      throw new Error("Email is already in use");
    }

    // In a real implementation, you'd send a verification code first
    // For mock, we'll require the code '123456'
    if (code !== "123456") {
      throw new Error("Invalid verification code");
    }

    const userIndex = users.findIndex((u) => u.id === user.id);
    users[userIndex].email = newEmail.toLowerCase();

    setStorageItem("ziggy_mock_users", users);
    setStorageItem(STORAGE_KEYS.USER, users[userIndex]);

    return { user: users[userIndex] };
  }

  async updatePassword({
    currentPassword,
    newPassword,
  }: UpdatePasswordRequest): Promise<{ ok: boolean }> {
    await simulateDelay();

    const user = getStorageItem<User | null>(STORAGE_KEYS.USER, null);
    if (!user) {
      throw new Error("Not authenticated");
    }

    // Verify current password
    const storedPasswordHash = getStorageItem(
      `ziggy_mock_password_${user.id}`,
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
    setStorageItem(`ziggy_mock_password_${user.id}`, newPasswordHash);

    logSecurityEvent({
      type: "password_change",
      success: true,
      details: "Password changed successfully",
    });

    return { ok: true };
  }
}

// Export singleton instance
export const mockAuthProvider = new MockAuthProvider();

// Provider factory function for easy swapping
export const createAuthProvider = (type: "mock" | "api" = "mock") => {
  switch (type) {
    case "mock":
      return mockAuthProvider;
    case "api":
      // TODO: Return real API provider when implemented
      throw new Error("API provider not yet implemented");
    default:
      return mockAuthProvider;
  }
};
