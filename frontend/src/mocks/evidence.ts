import type { Evidence } from "./types";

// Mock evidence data for ZiggyClean AI Trading Platform
export const mockEvidence: Evidence[] = [
  {
    predictionId: "pred_001", // NVDA
    sentiment: {
      score: 0.72,
      label: "bullish",
      sources: 147,
      confidence: 89,
    },
    headlines: [
      {
        title: "NVIDIA Reports Record Q3 Earnings, Beats Estimates by 15%",
        source: "Reuters",
        date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        url: "https://reuters.com/nvidia-earnings",
        sentiment: 0.85,
        relevance: 95,
        impact: "high",
      },
      {
        title: "AI Chip Demand Surge Continues, NVIDIA Leading Market Share",
        source: "Bloomberg",
        date: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        url: "https://bloomberg.com/ai-chip-demand",
        sentiment: 0.78,
        relevance: 88,
        impact: "high",
      },
      {
        title: "Institutional Flows Show Strong NVIDIA Accumulation",
        source: "Financial Times",
        date: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        url: "https://ft.com/nvidia-flows",
        sentiment: 0.65,
        relevance: 82,
        impact: "medium",
      },
    ],
    indicators: {
      rsi: { value: 58.2, signal: "neutral" },
      macd: { value: 12.5, signal: 8.2, histogram: 4.3, trend: "bullish" },
      sma50: 842.3,
      sma200: 785.6,
      volume_ratio: 1.35,
      atr: 28.5,
      volatility: 0.42,
    },
    history: {
      similarSetups: [
        {
          date: "2023-11-15",
          outcome: "win",
          movePercent: 12.3,
          similarity: 87,
          timeframe: "7d",
        },
        {
          date: "2023-08-22",
          outcome: "win",
          movePercent: 8.7,
          similarity: 82,
          timeframe: "5d",
        },
        {
          date: "2023-05-18",
          outcome: "loss",
          movePercent: -3.2,
          similarity: 79,
          timeframe: "3d",
        },
      ],
      successRate: 78,
      avgReturn: 6.8,
      avgHoldTime: "5.2 days",
    },
    patterns: {
      chartPattern: "Bull Flag",
      supportLevel: 850.0,
      resistanceLevel: 890.0,
      trendDirection: "up",
      strength: 85,
    },
  },
  {
    predictionId: "pred_002", // TSLA
    sentiment: {
      score: -0.45,
      label: "bearish",
      sources: 98,
      confidence: 76,
    },
    headlines: [
      {
        title: "Tesla Shanghai Plant Faces Production Bottlenecks",
        source: "Bloomberg",
        date: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
        url: "https://bloomberg.com/tesla-production",
        sentiment: -0.68,
        relevance: 92,
        impact: "high",
      },
      {
        title:
          "EV Competition Intensifies as Traditional Automakers Gain Ground",
        source: "Wall Street Journal",
        date: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        url: "https://wsj.com/ev-competition",
        sentiment: -0.42,
        relevance: 78,
        impact: "medium",
      },
      {
        title: "Q4 Delivery Targets Under Pressure from Supply Chain Issues",
        source: "TechCrunch",
        date: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString(),
        url: "https://techcrunch.com/tesla-deliveries",
        sentiment: -0.55,
        relevance: 85,
        impact: "high",
      },
    ],
    indicators: {
      rsi: { value: 42.8, signal: "neutral" },
      macd: { value: -3.2, signal: -1.8, histogram: -1.4, trend: "bearish" },
      sma50: 202.15,
      sma200: 218.4,
      volume_ratio: 1.28,
      atr: 12.8,
      volatility: 0.38,
    },
    history: {
      similarSetups: [
        {
          date: "2023-10-12",
          outcome: "win",
          movePercent: -7.2,
          similarity: 83,
          timeframe: "3d",
        },
        {
          date: "2023-07-28",
          outcome: "loss",
          movePercent: 2.1,
          similarity: 76,
          timeframe: "2d",
        },
        {
          date: "2023-04-15",
          outcome: "win",
          movePercent: -5.8,
          similarity: 81,
          timeframe: "4d",
        },
      ],
      successRate: 72,
      avgReturn: -4.3,
      avgHoldTime: "3.1 days",
    },
    patterns: {
      chartPattern: "Bear Flag",
      supportLevel: 188.0,
      resistanceLevel: 205.0,
      trendDirection: "down",
      strength: 78,
    },
  },
  {
    predictionId: "pred_003", // AAPL
    sentiment: {
      score: 0.15,
      label: "neutral",
      sources: 124,
      confidence: 68,
    },
    headlines: [
      {
        title: "Apple Announces AI Features for iPhone 16, Mixed Reception",
        source: "TechCrunch",
        date: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        url: "https://techcrunch.com/apple-ai",
        sentiment: 0.25,
        relevance: 88,
        impact: "medium",
      },
      {
        title: "iPhone Sales Steady but Growth Slowing in Key Markets",
        source: "Reuters",
        date: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        url: "https://reuters.com/iphone-sales",
        sentiment: -0.12,
        relevance: 82,
        impact: "medium",
      },
      {
        title: "Services Revenue Remains Strong Growth Driver",
        source: "Financial Times",
        date: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        url: "https://ft.com/apple-services",
        sentiment: 0.42,
        relevance: 75,
        impact: "low",
      },
    ],
    indicators: {
      rsi: { value: 52.1, signal: "neutral" },
      macd: { value: 0.8, signal: 0.5, histogram: 0.3, trend: "bullish" },
      sma50: 154.2,
      sma200: 151.8,
      volume_ratio: 0.95,
      atr: 3.2,
      volatility: 0.22,
    },
    history: {
      similarSetups: [
        {
          date: "2023-09-20",
          outcome: "win",
          movePercent: 2.8,
          similarity: 75,
          timeframe: "2d",
        },
        {
          date: "2023-06-15",
          outcome: "loss",
          movePercent: -1.5,
          similarity: 72,
          timeframe: "1d",
        },
        {
          date: "2023-03-10",
          outcome: "win",
          movePercent: 1.9,
          similarity: 68,
          timeframe: "3d",
        },
      ],
      successRate: 58,
      avgReturn: 1.1,
      avgHoldTime: "2.0 days",
    },
    patterns: {
      chartPattern: "Symmetrical Triangle",
      supportLevel: 152.0,
      resistanceLevel: 158.0,
      trendDirection: "sideways",
      strength: 62,
    },
  },
  {
    predictionId: "pred_004", // MSFT
    sentiment: {
      score: 0.68,
      label: "bullish",
      sources: 132,
      confidence: 84,
    },
    headlines: [
      {
        title: "Microsoft Azure Growth Accelerates to 29% in Latest Quarter",
        source: "Bloomberg",
        date: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
        url: "https://bloomberg.com/azure-growth",
        sentiment: 0.82,
        relevance: 94,
        impact: "high",
      },
      {
        title: "AI Integration Driving Enterprise Adoption Across Office Suite",
        source: "Wall Street Journal",
        date: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        url: "https://wsj.com/office-ai",
        sentiment: 0.74,
        relevance: 87,
        impact: "high",
      },
      {
        title: "Cloud Segment Guidance Raised on Strong Enterprise Demand",
        source: "Reuters",
        date: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        url: "https://reuters.com/msft-guidance",
        sentiment: 0.65,
        relevance: 91,
        impact: "high",
      },
    ],
    indicators: {
      rsi: { value: 62.4, signal: "neutral" },
      macd: { value: 8.2, signal: 5.8, histogram: 2.4, trend: "bullish" },
      sma50: 307.8,
      sma200: 295.4,
      volume_ratio: 1.22,
      atr: 8.4,
      volatility: 0.28,
    },
    history: {
      similarSetups: [
        {
          date: "2023-10-25",
          outcome: "win",
          movePercent: 8.4,
          similarity: 89,
          timeframe: "6d",
        },
        {
          date: "2023-07-18",
          outcome: "win",
          movePercent: 5.9,
          similarity: 85,
          timeframe: "4d",
        },
        {
          date: "2023-04-20",
          outcome: "win",
          movePercent: 7.2,
          similarity: 82,
          timeframe: "5d",
        },
      ],
      successRate: 82,
      avgReturn: 7.2,
      avgHoldTime: "5.0 days",
    },
    patterns: {
      chartPattern: "Ascending Triangle",
      supportLevel: 310.0,
      resistanceLevel: 325.0,
      trendDirection: "up",
      strength: 88,
    },
  },
];

// Helper functions for evidence analysis
export function getEvidenceByPrediction(
  predictionId: string,
): Evidence | undefined {
  return mockEvidence.find(
    (evidence) => evidence.predictionId === predictionId,
  );
}

export function getBullishEvidence(): Evidence[] {
  return mockEvidence.filter(
    (evidence) => evidence.sentiment.label === "bullish",
  );
}

export function getBearishEvidence(): Evidence[] {
  return mockEvidence.filter(
    (evidence) => evidence.sentiment.label === "bearish",
  );
}

export function getHighConfidenceEvidence(
  minConfidence: number = 80,
): Evidence[] {
  return mockEvidence.filter(
    (evidence) => evidence.sentiment.confidence >= minConfidence,
  );
}

export function getRecentHeadlines(hours: number = 24): Evidence[] {
  const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
  return mockEvidence.filter((evidence) =>
    evidence.headlines.some((headline) => new Date(headline.date) > cutoff),
  );
}

export function getStrongPatterns(minStrength: number = 80): Evidence[] {
  return mockEvidence.filter(
    (evidence) => evidence.patterns.strength >= minStrength,
  );
}

export function calculateSentimentTrend(evidence: Evidence[]): {
  overall: number;
  trend: "improving" | "deteriorating" | "stable";
  confidence: number;
} {
  const scores = evidence.map((e) => e.sentiment.score);
  const overall = scores.reduce((sum, score) => sum + score, 0) / scores.length;

  // Simple trend calculation based on recent vs older scores
  const recent = scores.slice(-3);
  const older = scores.slice(0, -3);

  const recentAvg =
    recent.reduce((sum, score) => sum + score, 0) / recent.length;
  const olderAvg =
    older.length > 0
      ? older.reduce((sum, score) => sum + score, 0) / older.length
      : recentAvg;

  const diff = recentAvg - olderAvg;
  const trend =
    diff > 0.1 ? "improving" : diff < -0.1 ? "deteriorating" : "stable";

  const avgConfidence =
    evidence.reduce((sum, e) => sum + e.sentiment.confidence, 0) /
    evidence.length;

  return {
    overall,
    trend,
    confidence: avgConfidence,
  };
}
