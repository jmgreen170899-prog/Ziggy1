/**
 * Paper Trading API Service
 * 
 * Provides interface to ZiggyAI Paper Trading Lab backend endpoints.
 * Admin-only functionality for monitoring autonomous trading operations.
 */

import axios, { AxiosInstance } from 'axios';

// Paper Trading Types
export interface PaperRun {
  id: string;
  user_id: string;
  symbols: string[];
  start_time: string;
  end_time?: string;
  status: 'active' | 'stopped' | 'error';
  initial_balance: number;
  current_balance: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  max_drawdown: number;
  params: Record<string, unknown>;
  created_at: string;
}

export interface Trade {
  id: string;
  run_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  theory_used: string;
  signal_confidence: number;
  execution_latency_ms: number;
  slippage_bps: number;
  commission: number;
  pnl?: number;
  outcome_1h?: number;
}

export interface TheoryPerformance {
  id: string;
  run_id: string;
  theory_name: string;
  total_signals: number;
  successful_signals: number;
  avg_confidence: number;
  avg_pnl: number;
  allocation_weight: number;
  win_rate: number;
  sharpe_ratio: number;
  last_updated: string;
}

export interface ModelSnapshot {
  id: string;
  run_id: string;
  model_type: string;
  feature_count: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  calibration_score: number;
  model_size_bytes: number;
  created_at: string;
}

export interface TradingSession {
  id: string;
  run_id: string;
  start_time: string;
  end_time?: string;
  trades_count: number;
  pnl: number;
  max_drawdown: number;
  theories_used: string[];
  avg_trade_duration_minutes: number;
}

export interface PaperRunStats {
  total_pnl: number;
  total_trades: number;
  win_rate: number;
  avg_trade_pnl: number;
  max_drawdown: number;
  sharpe_ratio: number;
  current_positions: number;
  theories_performance: TheoryPerformance[];
  recent_trades: Trade[];
  model_performance: ModelSnapshot[];
}

export interface SystemHealth {
  worker_status: 'running' | 'stopped' | 'error';
  last_trade_time?: string;
  trades_per_minute: number;
  error_count: number;
  memory_usage_mb: number;
  active_theories: string[];
  data_freshness_seconds: number;
}

export interface CreateRunRequest {
  symbols: string[];
  max_trades_per_minute?: number;
  max_trades_per_hour?: number;
  max_position_size?: number;
  max_daily_loss?: number;
  enable_learning?: boolean;
  theory_allocation_method?: 'thompson_sampling' | 'ucb1' | 'epsilon_greedy';
  learning_frequency?: number;
}

class PaperTradingAPIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_PAPER_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          window.location.href = '/auth/signin';
        }
        return Promise.reject(error);
      }
    );
  }

  // Paper Run Management
  async createRun(params: CreateRunRequest): Promise<PaperRun> {
    const response = await this.client.post('/api/paper/runs', params);
    return response.data;
  }

  async getRuns(limit: number = 50): Promise<PaperRun[]> {
    const response = await this.client.get(`/api/paper/runs?limit=${limit}`);
    return response.data;
  }

  async getRun(runId: string): Promise<PaperRun> {
    const response = await this.client.get(`/api/paper/runs/${runId}`);
    return response.data;
  }

  async stopRun(runId: string): Promise<void> {
    await this.client.post(`/api/paper/runs/${runId}/stop`);
  }

  async deleteRun(runId: string): Promise<void> {
    await this.client.delete(`/api/paper/runs/${runId}`);
  }

  // Trade Data
  async getTrades(runId: string, limit: number = 100): Promise<Trade[]> {
    const response = await this.client.get(`/api/paper/runs/${runId}/trades?limit=${limit}`);
    return response.data;
  }

  async getRecentTrades(limit: number = 50): Promise<Trade[]> {
    const response = await this.client.get(`/api/paper/trades/recent?limit=${limit}`);
    return response.data;
  }

  // Theory Performance
  async getTheoryPerformance(runId: string): Promise<TheoryPerformance[]> {
    const response = await this.client.get(`/api/paper/runs/${runId}/theories`);
    return response.data;
  }

  async getAllTheoryPerformance(): Promise<TheoryPerformance[]> {
    const response = await this.client.get('/api/paper/theories/performance');
    return response.data;
  }

  // Model Snapshots
  async getModelSnapshots(runId: string): Promise<ModelSnapshot[]> {
    const response = await this.client.get(`/api/paper/runs/${runId}/models`);
    return response.data;
  }

  // Statistics and Analytics
  async getRunStats(runId: string): Promise<PaperRunStats> {
    const response = await this.client.get(`/api/paper/runs/${runId}/stats`);
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.client.get('/api/paper/health');
    return response.data;
  }

  // Trading Sessions
  async getTradingSessions(runId: string): Promise<TradingSession[]> {
    const response = await this.client.get(`/api/paper/runs/${runId}/sessions`);
    return response.data;
  }

  // Emergency Controls
  async emergencyStop(): Promise<void> {
    await this.client.post('/api/paper/emergency-stop');
  }

  async pauseTrading(): Promise<void> {
    await this.client.post('/api/paper/pause');
  }

  async resumeTrading(): Promise<void> {
    await this.client.post('/api/paper/resume');
  }

  // System Configuration
  async updateConfig(config: Partial<CreateRunRequest>): Promise<void> {
    await this.client.post('/api/paper/config', config);
  }

  async getConfig(): Promise<CreateRunRequest> {
    const response = await this.client.get('/api/paper/config');
    return response.data;
  }
}

// Create singleton instance
export const paperTradingApi = new PaperTradingAPIClient();