'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PageLayout, ThemedButton, ThemedCard, StatusIndicator } from '@/components/layout/PageLayout';
import { formatPercentage, formatDateTime } from '@/utils';
import { apiClient } from '@/services/api';

// Learning System Types
interface LearningStatus {
  system_ready: boolean;
  recent_data: {
    total_decisions: number;
    completed_trades: number;
    data_window_days: number;
    last_decision: string | null;
  };
  learning_config: {
    data_window_days: number;
    train_split: number;
    valid_split: number;
    test_split: number;
    min_records: number;
  };
}

interface LearningDataSummary {
  total_records: number;
  completed_trades: number;
  date_range: string | null;
  symbols: string[];
  regimes: string[];
  signal_types: string[];
  message?: string;
}

interface LearningResults {
  latest_session?: {
    id: string;
    timestamp: string;
    performance_before: Record<string, number>;
    performance_after: Record<string, number>;
    improvements: Record<string, number>;
    rule_changes: Array<{
      parameter: string;
      old_value: number;
      new_value: number;
      improvement: number;
    }>;
  };
  history: Array<{
    id: string;
    timestamp: string;
    performance_improvement: number;
    rules_changed: number;
  }>;
}

interface LearningGates {
  data_threshold_met: boolean;
  performance_threshold_met: boolean;
  user_consent: boolean;
  frequency_check: boolean;
  overall_ready: boolean;
}

function LearningStatusCard({ status }: { status: LearningStatus | null }) {
  if (!status) {
    return (
      <ThemedCard>
        <CardHeader>
          <CardTitle>Learning System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500">Loading status...</div>
        </CardContent>
      </ThemedCard>
    );
  }

  return (
    <ThemedCard>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Learning System Status
          <StatusIndicator status={status.system_ready ? 'active' : 'inactive'} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">{status.recent_data.total_decisions}</div>
            <div className="text-sm text-gray-500">Total Decisions</div>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">{status.recent_data.completed_trades}</div>
            <div className="text-sm text-gray-500">Completed Trades</div>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">{status.recent_data.data_window_days}</div>
            <div className="text-sm text-gray-500">Data Window (Days)</div>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">{status.learning_config.min_records}</div>
            <div className="text-sm text-gray-500">Min Records Required</div>
          </div>
        </div>
        {status.recent_data.last_decision && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Last Decision: {formatDateTime(status.recent_data.last_decision)}
            </div>
          </div>
        )}
      </CardContent>
    </ThemedCard>
  );
}

function DataSummaryCard({ summary }: { summary: LearningDataSummary | null }) {
  if (!summary) {
    return (
      <ThemedCard>
        <CardHeader>
          <CardTitle>Learning Data Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500">Loading data summary...</div>
        </CardContent>
      </ThemedCard>
    );
  }

  return (
    <ThemedCard>
      <CardHeader>
        <CardTitle>Learning Data Summary</CardTitle>
      </CardHeader>
      <CardContent>
        {summary.total_records === 0 ? (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">🧠</div>
            <div className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
              Learning System Ready
            </div>
            <div className="text-sm text-gray-500">
              {summary.message || 'No trading data available yet. Start trading to enable learning.'}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-xl font-bold">{summary.total_records}</div>
                <div className="text-sm text-gray-500">Total Records</div>
              </div>
              <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="text-xl font-bold">{summary.completed_trades}</div>
                <div className="text-sm text-gray-500">Completed Trades</div>
              </div>
            </div>
            
            {summary.symbols.length > 0 && (
              <div>
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Symbols Analyzed ({summary.symbols.length})
                </div>
                <div className="flex flex-wrap gap-1">
                  {summary.symbols.slice(0, 10).map(symbol => (
                    <span key={symbol} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-xs rounded">
                      {symbol}
                    </span>
                  ))}
                  {summary.symbols.length > 10 && (
                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded">
                      +{summary.symbols.length - 10} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {summary.date_range && (
              <div className="text-sm text-gray-500">
                Data Range: {summary.date_range}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </ThemedCard>
  );
}

function LearningResultsCard({ results }: { results: LearningResults | null }) {
  return (
    <ThemedCard>
      <CardHeader>
        <CardTitle>Learning Results</CardTitle>
      </CardHeader>
      <CardContent>
        {!results || results.history.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📊</div>
            <div className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
              No Learning Sessions Yet
            </div>
            <div className="text-sm text-gray-500">
              Learning sessions will appear here after the system has enough data to train.
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {results.latest_session && (
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="font-medium text-green-800 dark:text-green-200 mb-2">
                  Latest Learning Session
                </div>
                <div className="text-sm text-green-700 dark:text-green-300">
                  {formatDateTime(results.latest_session.timestamp)}
                </div>
                {results.latest_session.rule_changes.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-green-600 dark:text-green-400 mb-1">
                      Rule Changes ({results.latest_session.rule_changes.length})
                    </div>
                    <div className="space-y-1">
                      {results.latest_session.rule_changes.slice(0, 3).map((change, index) => (
                        <div key={index} className="text-xs text-green-700 dark:text-green-300">
                          {change.parameter}: {change.old_value.toFixed(3)} → {change.new_value.toFixed(3)} 
                          ({change.improvement > 0 ? '+' : ''}{formatPercentage(change.improvement)} improvement)
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div>
              <div className="font-medium mb-2">Learning History</div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {results.history.slice(0, 10).map((session, index) => (
                  <div key={session.id} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                    <div>
                      <div className="text-sm font-medium">Session #{index + 1}</div>
                      <div className="text-xs text-gray-500">{formatDateTime(session.timestamp)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-green-600">
                        +{formatPercentage(session.performance_improvement)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {session.rules_changed} rules changed
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </ThemedCard>
  );
}

function LearningGatesCard({ gates }: { gates: LearningGates | null }) {
  if (!gates) {
    return (
      <ThemedCard>
        <CardHeader>
          <CardTitle>Learning Gates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-gray-500">Loading gates status...</div>
        </CardContent>
      </ThemedCard>
    );
  }

  const gateItems = [
    { name: 'Data Threshold', met: gates.data_threshold_met, description: 'Sufficient trading data available' },
    { name: 'Performance Threshold', met: gates.performance_threshold_met, description: 'Baseline performance established' },
    { name: 'User Consent', met: gates.user_consent, description: 'User permission for learning' },
    { name: 'Frequency Check', met: gates.frequency_check, description: 'Appropriate time since last learning' }
  ];

  return (
    <ThemedCard>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Learning Gates
          <StatusIndicator status={gates.overall_ready ? 'active' : 'warning'} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {gateItems.map((gate, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div>
                <div className="text-sm font-medium">{gate.name}</div>
                <div className="text-xs text-gray-500">{gate.description}</div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${gate.met ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={`text-sm ${gate.met ? 'text-green-600' : 'text-red-600'}`}>
                  {gate.met ? 'Ready' : 'Not Ready'}
                </span>
              </div>
            </div>
          ))}
        </div>
        
        <div className={`mt-4 p-3 rounded-lg border ${
          gates.overall_ready 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
            : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
        }`}>
          <div className={`font-medium ${
            gates.overall_ready 
              ? 'text-green-800 dark:text-green-200' 
              : 'text-yellow-800 dark:text-yellow-200'
          }`}>
            {gates.overall_ready ? '✅ System Ready for Learning' : '⏳ System Not Ready for Learning'}
          </div>
          <div className={`text-sm ${
            gates.overall_ready 
              ? 'text-green-700 dark:text-green-300' 
              : 'text-yellow-700 dark:text-yellow-300'
          }`}>
            {gates.overall_ready 
              ? 'All conditions met. Learning can proceed when triggered.'
              : 'Some conditions need to be met before learning can begin.'
            }
          </div>
        </div>
      </CardContent>
    </ThemedCard>
  );
}

export default function LearningPage() {
  const [status, setStatus] = useState<LearningStatus | null>(null);
  const [dataSummary, setDataSummary] = useState<LearningDataSummary | null>(null);
  const [results, setResults] = useState<LearningResults | null>(null);
  const [gates, setGates] = useState<LearningGates | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'data' | 'results' | 'settings'>('overview');

  useEffect(() => {
    const fetchLearningData = async () => {
      try {
        if (!refreshing) setLoading(true);
        
        // Fetch all learning data in parallel
        const [statusResponse, summaryData, resultsData, gatesData] = await Promise.all([
          apiClient.getAdaptationMetrics(),
          apiClient.getLearningDataSummary(),
          apiClient.getLearningResults(),
          apiClient.getLearningGates()
        ]);

        // Transform AdaptationMetrics to LearningStatus structure
        const statusData: LearningStatus = {
          system_ready: statusResponse.accuracy > 0, // Use accuracy as proxy for system readiness
          recent_data: {
            total_decisions: 0, // Example data - should come from different endpoint
            completed_trades: 0, // Example data - should come from different endpoint  
            data_window_days: 30, // Default window
            last_decision: null // Example data
          },
          learning_config: {
            data_window_days: 30,
            train_split: 0.7,
            valid_split: 0.15,
            test_split: 0.15,
            min_records: 100
          }
        };

        setStatus(statusData);
        setDataSummary(summaryData);
        setResults(resultsData);
        setGates(gatesData);
      } catch (error) {
        console.error('Error fetching learning data:', error);
        // Keep existing state on error
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    };

    fetchLearningData();
    
    // Refresh every 60 seconds (learning data changes less frequently)
    const interval = setInterval(fetchLearningData, 60000);
    return () => clearInterval(interval);
  }, [refreshing]);

  const handleRefresh = () => {
    setRefreshing(true);
  };

  const handleTriggerLearning = async () => {
    try {
      await apiClient.triggerLearningUpdate();
      // Refresh data after triggering learning
      handleRefresh();
    } catch (error) {
      console.error('Error triggering learning update:', error);
    }
  };

  const tabs = [
    { id: 'overview' as const, name: '📊 Overview', icon: '📊' },
    { id: 'data' as const, name: '📈 Data Analysis', icon: '📈' },
    { id: 'results' as const, name: '🎯 Results', icon: '🎯' },
    { id: 'settings' as const, name: '⚙️ Settings', icon: '⚙️' }
  ];

  if (loading) {
    return (
      <RequireAuth>
        <PageLayout title="Learning System">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading learning system data...</p>
            </div>
          </div>
        </PageLayout>
      </RequireAuth>
    );
  }

  return (
    <RequireAuth>
      <PageLayout
        title="🧠 Learning System"
        subtitle="AI adaptation and performance optimization"
        theme="dashboard"
        actions={
          <div className="flex items-center space-x-3">
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="ghost"
              className="text-sm"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </Button>
            <Button
              onClick={handleTriggerLearning}
              disabled={!gates?.overall_ready}
              variant="primary"
              className="text-sm"
            >
              🚀 Trigger Learning
            </Button>
          </div>
        }
      >
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <ThemedButton
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                variant={activeTab === tab.id ? 'primary' : 'secondary'}
              >
                {tab.icon} {tab.name}
              </ThemedButton>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LearningStatusCard status={status} />
            <LearningGatesCard gates={gates} />
            <DataSummaryCard summary={dataSummary} />
            <LearningResultsCard results={results} />
          </div>
        )}

        {activeTab === 'data' && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <DataSummaryCard summary={dataSummary} />
            </div>
            <div>
              <LearningStatusCard status={status} />
            </div>
          </div>
        )}

        {activeTab === 'results' && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <LearningResultsCard results={results} />
            <LearningGatesCard gates={gates} />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="grid grid-cols-1 gap-6">
            <ThemedCard>
              <CardHeader>
                <CardTitle>Learning Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                      Automatic Learning
                    </div>
                    <div className="text-sm text-blue-700 dark:text-blue-300">
                      The learning system automatically optimizes trading rules based on historical performance. 
                      All changes are transparent and reversible.
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="font-medium text-green-800 dark:text-green-200 mb-2">
                      Privacy & Security
                    </div>
                    <div className="text-sm text-green-700 dark:text-green-300">
                      All learning happens locally. No personal trading data is shared externally. 
                      You maintain full control over your data and learning preferences.
                    </div>
                  </div>
                </div>
              </CardContent>
            </ThemedCard>
          </div>
        )}
      </PageLayout>
    </RequireAuth>
  );
}