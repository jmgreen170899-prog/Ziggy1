import type { AgentAction } from "./types";

// Mock agent queue data for ZiggyClean AI Trading Platform
export const mockAgentQueue: AgentAction[] = [
  {
    id: "agent_001",
    type: "monitor",
    symbol: "NVDA",
    priority: "high",
    payload: {
      conditions: ["price_above_875", "volume_spike_1.5x"],
      duration: "2h",
      alertThreshold: 2.5,
    },
    status: "in_progress",
    eta: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes
    progress: 65,
    createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
    startedAt: new Date(Date.now() - 40 * 60 * 1000).toISOString(),
    requiresApproval: false,
  },
  {
    id: "agent_002",
    type: "execute",
    symbol: "MSFT",
    priority: "urgent",
    payload: {
      action: "buy",
      quantity: 300,
      orderType: "limit",
      price: 312.0,
      planId: "plan_003",
    },
    status: "requires_approval",
    progress: 0,
    createdAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(), // 20 minutes ago
    requiresApproval: true,
    result: "Execution ready. Waiting for human approval for $93,600 order.",
  },
  {
    id: "agent_003",
    type: "alert",
    symbol: "TSLA",
    priority: "medium",
    payload: {
      alertType: "price_below",
      threshold: 195.0,
      message: "TSLA approaching short entry level",
    },
    status: "completed",
    progress: 100,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    startedAt: new Date(Date.now() - 118 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 minutes ago
    requiresApproval: false,
    result: "Alert created successfully. Monitoring TSLA price action.",
  },
  {
    id: "agent_004",
    type: "research",
    symbol: "AAPL",
    priority: "low",
    payload: {
      researchType: "sentiment_analysis",
      sources: ["news", "social", "analyst_reports"],
      timeframe: "24h",
    },
    status: "pending",
    progress: 0,
    createdAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 minutes ago
    requiresApproval: false,
  },
  {
    id: "agent_005",
    type: "plan",
    symbol: "GOOGL",
    priority: "medium",
    payload: {
      predictionId: "pred_005",
      riskAmount: 4500,
      accountRiskPct: 1.8,
      strategy: "swing_trade",
    },
    status: "in_progress",
    eta: new Date(Date.now() + 15 * 60 * 1000).toISOString(), // 15 minutes
    progress: 80,
    createdAt: new Date(Date.now() - 25 * 60 * 1000).toISOString(), // 25 minutes ago
    startedAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
    requiresApproval: true,
    result: "Plan generated. Risk analysis complete. Awaiting final approval.",
  },
  {
    id: "agent_006",
    type: "analyze",
    symbol: "AMD",
    priority: "medium",
    payload: {
      analysisType: "technical_pattern",
      indicators: ["rsi", "macd", "volume", "support_resistance"],
      timeframe: "4h",
    },
    status: "completed",
    progress: 100,
    createdAt: new Date(Date.now() - 35 * 60 * 1000).toISOString(), // 35 minutes ago
    startedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    requiresApproval: false,
    result:
      "Technical analysis complete. Bear flag pattern identified with 74% confidence.",
  },
  {
    id: "agent_007",
    type: "monitor",
    symbol: "SPY",
    priority: "high",
    payload: {
      conditions: ["vix_below_20", "market_breadth_positive"],
      duration: "4h",
      alertThreshold: 1.0,
    },
    status: "failed",
    progress: 0,
    createdAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hour ago
    startedAt: new Date(Date.now() - 55 * 60 * 1000).toISOString(),
    requiresApproval: false,
    error:
      "Market data feed timeout. Unable to establish monitoring connection.",
  },
  {
    id: "agent_008",
    type: "alert",
    symbol: "QQQ",
    priority: "low",
    payload: {
      alertType: "volume_spike",
      threshold: 1.5,
      message: "QQQ unusual volume activity detected",
    },
    status: "pending",
    progress: 0,
    createdAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
    requiresApproval: false,
  },
  {
    id: "agent_009",
    type: "execute",
    symbol: "NVDA",
    priority: "high",
    payload: {
      action: "sell",
      quantity: 50,
      orderType: "stop_loss",
      price: 825.0,
      planId: "plan_001",
    },
    status: "requires_approval",
    progress: 0,
    createdAt: new Date(Date.now() - 3 * 60 * 1000).toISOString(), // 3 minutes ago
    requiresApproval: true,
    result: "Stop loss order ready. Risk management protocol activated.",
  },
  {
    id: "agent_010",
    type: "research",
    symbol: "BTC",
    priority: "medium",
    payload: {
      researchType: "macro_analysis",
      factors: ["fed_policy", "inflation", "crypto_regulation"],
      timeframe: "7d",
    },
    status: "in_progress",
    eta: new Date(Date.now() + 45 * 60 * 1000).toISOString(), // 45 minutes
    progress: 40,
    createdAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
    startedAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    requiresApproval: false,
  },
];

// Helper functions for agent queue management
export function getActionsByStatus(
  status: AgentAction["status"],
): AgentAction[] {
  return mockAgentQueue.filter((action) => action.status === status);
}

export function getActionsByType(type: AgentAction["type"]): AgentAction[] {
  return mockAgentQueue.filter((action) => action.type === type);
}

export function getActionsByPriority(
  priority: AgentAction["priority"],
): AgentAction[] {
  return mockAgentQueue.filter((action) => action.priority === priority);
}

export function getActionsBySymbol(symbol: string): AgentAction[] {
  return mockAgentQueue.filter((action) => action.symbol === symbol);
}

export function getPendingActions(): AgentAction[] {
  return mockAgentQueue.filter(
    (action) => action.status === "pending" || action.status === "in_progress",
  );
}

export function getActionsRequiringApproval(): AgentAction[] {
  return mockAgentQueue.filter(
    (action) => action.status === "requires_approval",
  );
}

export function getCompletedActions(hours: number = 24): AgentAction[] {
  const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
  return mockAgentQueue.filter(
    (action) =>
      action.status === "completed" &&
      action.completedAt &&
      new Date(action.completedAt) > cutoff,
  );
}

export function getFailedActions(hours: number = 24): AgentAction[] {
  const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
  return mockAgentQueue.filter(
    (action) =>
      action.status === "failed" && new Date(action.createdAt) > cutoff,
  );
}

export function getHighPriorityActions(): AgentAction[] {
  return mockAgentQueue.filter(
    (action) => action.priority === "high" || action.priority === "urgent",
  );
}

export function getEstimatedCompletionTime(): Date | null {
  const inProgress = mockAgentQueue.filter(
    (action) => action.status === "in_progress" && action.eta,
  );

  if (inProgress.length === 0) return null;

  const latestEta = Math.max(
    ...inProgress.map((action) => new Date(action.eta!).getTime()),
  );

  return new Date(latestEta);
}

export function getQueueStatistics() {
  const total = mockAgentQueue.length;
  const pending = getActionsByStatus("pending").length;
  const inProgress = getActionsByStatus("in_progress").length;
  const completed = getActionsByStatus("completed").length;
  const failed = getActionsByStatus("failed").length;
  const requiresApproval = getActionsRequiringApproval().length;

  return {
    total,
    pending,
    inProgress,
    completed,
    failed,
    requiresApproval,
    completionRate: total > 0 ? (completed / total) * 100 : 0,
    failureRate: total > 0 ? (failed / total) * 100 : 0,
  };
}

// Mock function to simulate approving an action
export function approveAction(
  actionId: string,
  approvedBy: string,
): AgentAction | null {
  const action = mockAgentQueue.find((a) => a.id === actionId);
  if (!action || action.status !== "requires_approval") return null;

  // Simulate approval
  action.status = "in_progress";
  action.approvedBy = approvedBy;
  action.approvedAt = new Date().toISOString();
  action.startedAt = new Date().toISOString();

  return action;
}

// Mock function to simulate completing an action
export function completeAction(
  actionId: string,
  result?: string,
): AgentAction | null {
  const action = mockAgentQueue.find((a) => a.id === actionId);
  if (!action || action.status !== "in_progress") return null;

  // Simulate completion
  action.status = "completed";
  action.progress = 100;
  action.completedAt = new Date().toISOString();
  if (result) action.result = result;

  return action;
}
