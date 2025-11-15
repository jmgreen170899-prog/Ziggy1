/*
 * WSClient — centralized WebSocket client with backoff, sendWhenOpen queue, and heartbeat
 */
export type Json = Record<string, unknown>;

export interface WSClientOptions {
  baseUrl?: string; // e.g., ws://localhost:8000 (no trailing slash)
  heartbeatIntervalMs?: number; // default 25000
  inactivityTimeoutMs?: number; // default 60000; force reconnect if no messages
  maxReconnectDelayMs?: number; // default 30000
  baseReconnectDelayMs?: number; // default 1000
  maxReconnectAttempts?: number; // 0 = infinite
  pingPayload?: Json | (() => Json);
}

export type WSState = "CONNECTING" | "OPEN" | "CLOSING" | "CLOSED" | "NONE";

export class WSClient {
  private urlPath: string;
  private opts: Required<WSClientOptions>;
  private socket: WebSocket | null = null;
  private queue: string[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private inactivityTimer: number | null = null;
  private lastActivity = 0;

  private onOpenHandlers: Array<() => void> = [];
  private onCloseHandlers: Array<(ev: CloseEvent) => void> = [];
  private onErrorHandlers: Array<(ev: Event) => void> = [];
  private onMessageHandlers: Array<(ev: MessageEvent) => void> = [];

  constructor(urlPath: string, options: WSClientOptions = {}) {
    this.urlPath = urlPath.startsWith("/") ? urlPath : `/${urlPath}`;

    const envUrl = (process.env.NEXT_PUBLIC_WS_URL || "").trim();
    const derivedBase = envUrl
      ? envUrl.replace(/\/$/, "")
      : typeof window !== "undefined" && window.location
        ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
        : "ws://localhost:8000";

    this.opts = {
      baseUrl: options.baseUrl?.replace(/\/$/, "") || derivedBase,
      heartbeatIntervalMs: options.heartbeatIntervalMs ?? 25000,
      inactivityTimeoutMs: options.inactivityTimeoutMs ?? 60000,
      maxReconnectDelayMs: options.maxReconnectDelayMs ?? 30000,
      baseReconnectDelayMs: options.baseReconnectDelayMs ?? 1000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 0,
      pingPayload: options.pingPayload ?? {
        type: "ping",
        ts: () => Date.now(),
      },
    };
  }

  connect(): void {
    if (typeof window === "undefined") return; // SSR guard

    const url = `${this.opts.baseUrl}${this.urlPath}`;
    try {
      this.socket = new WebSocket(url);
      this.lastActivity = Date.now();

      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        this.flushQueue();
        this.startHeartbeat();
        this.onOpenHandlers.forEach((fn) => fn());
      };

      this.socket.onmessage = (ev) => {
        this.lastActivity = Date.now();
        this.onMessageHandlers.forEach((fn) => fn(ev));
      };

      this.socket.onerror = (ev) => {
        this.onErrorHandlers.forEach((fn) => fn(ev));
      };

      this.socket.onclose = (ev) => {
        this.stopHeartbeat();
        this.onCloseHandlers.forEach((fn) => fn(ev));
        this.scheduleReconnect();
      };
    } catch {
      // schedule reconnect on construction failure
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      this.socket.close();
    }
    this.socket = null;
  }

  send(obj: Json): void {
    const payload = JSON.stringify(obj);
    if (!this.socket) {
      this.queue.push(payload);
      return;
    }
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(payload);
      return;
    }
    if (this.socket.readyState === WebSocket.CONNECTING) {
      this.queue.push(payload);
      return;
    }
    // CLOSED/CLOSING — queue and reconnect
    this.queue.push(payload);
    this.scheduleReconnect();
  }

  onOpen(fn: () => void): void {
    this.onOpenHandlers.push(fn);
  }
  onClose(fn: (ev: CloseEvent) => void): void {
    this.onCloseHandlers.push(fn);
  }
  onError(fn: (ev: Event) => void): void {
    this.onErrorHandlers.push(fn);
  }
  onMessage(fn: (ev: MessageEvent) => void): void {
    this.onMessageHandlers.push(fn);
  }

  get state(): WSState {
    if (!this.socket) return "NONE";
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return "CONNECTING";
      case WebSocket.OPEN:
        return "OPEN";
      case WebSocket.CLOSING:
        return "CLOSING";
      case WebSocket.CLOSED:
        return "CLOSED";
      default:
        return "NONE";
    }
  }

  private flushQueue(): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    while (this.queue.length) {
      const msg = this.queue.shift();
      if (msg) {
        try {
          this.socket.send(msg);
        } catch {
          /* ignore */
        }
      }
    }
  }

  private startHeartbeat(): void {
    // Send ping periodically and ensure inactivity reconnect
    this.stopHeartbeat();
    if (this.opts.heartbeatIntervalMs > 0) {
      this.heartbeatTimer = setInterval(() => {
        const pingValue =
          typeof this.opts.pingPayload === "function"
            ? (this.opts.pingPayload as () => Json)()
            : (this.opts.pingPayload as Json);
        this.send(pingValue);
      }, this.opts.heartbeatIntervalMs) as unknown as number;
    }
    if (this.opts.inactivityTimeoutMs > 0) {
      this.inactivityTimer = setInterval(
        () => {
          const idle = Date.now() - this.lastActivity;
          if (idle > this.opts.inactivityTimeoutMs) {
            // Force reconnect to refresh a stale connection
            try {
              this.socket?.close();
            } catch {
              /* ignore */
            }
          }
        },
        Math.min(this.opts.inactivityTimeoutMs, 10000),
      ) as unknown as number;
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    if (this.inactivityTimer) {
      clearInterval(this.inactivityTimer);
      this.inactivityTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (typeof window === "undefined") return;
    if (this.reconnectTimer) return;

    // respect max attempts (0 = infinite)
    if (
      this.opts.maxReconnectAttempts > 0 &&
      this.reconnectAttempts >= this.opts.maxReconnectAttempts
    ) {
      // Keep trying periodically at max delay
      this.reconnectAttempts = this.opts.maxReconnectAttempts; // cap
    } else {
      this.reconnectAttempts += 1;
    }

    const expDelay =
      this.opts.baseReconnectDelayMs *
      Math.pow(2, Math.max(0, this.reconnectAttempts - 1));
    const jitter = 0.85 + Math.random() * 0.3; // 85%-115%
    const delay = Math.min(
      Math.floor(expDelay * jitter),
      this.opts.maxReconnectDelayMs,
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay) as unknown as number;
  }
}

export default WSClient;
