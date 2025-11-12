'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatPercentage, timeAgo, cn } from '@/utils';
import { apiClient } from '@/services/api';
import type { TradingSignal } from '@/types/api';

type Prediction = {
  id: string;
  symbol: string;
  timeframe: '1d' | '4h' | '1h';
  signal: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  expectedMovePct: number;
  rationale: string[];
  quality: number;
  createdAt: string;
  expiresAt: string;
  evidence: {
    technicalWeight: number;
    fundamentalWeight: number;
    sentimentWeight: number;
    macroWeight: number;
  };
  riskReward: {
    probability: number;
    sharpeRatio: number;
  };
};

interface PredictionCardProps {
  prediction: Prediction;
  onSimulate: (prediction: Prediction) => void;
  onCreateAlert: (prediction: Prediction) => void;
  onAutoplan: (prediction: Prediction) => void;
}

function PredictionCard({ prediction, onSimulate, onCreateAlert, onAutoplan }: PredictionCardProps) {
  const signalColors = {
    bullish: 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300',
    bearish: 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300',
    neutral: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300',
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityColor = (quality: number) => {
    if (quality >= 85) return 'text-green-500';
    if (quality >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const isExpiringSoon = () => {
    const now = new Date();
    const expiry = new Date(prediction.expiresAt);
    const hoursUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60);
    return hoursUntilExpiry <= 24;
  };

  return (
    <Card className={cn(
      "hover:shadow-lg transition-all duration-200 cursor-pointer border-l-4",
      prediction.signal === 'bullish' && "border-l-green-500",
      prediction.signal === 'bearish' && "border-l-red-500",
      prediction.signal === 'neutral' && "border-l-yellow-500",
      isExpiringSoon() && "ring-2 ring-orange-200 dark:ring-orange-800"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-xl font-bold">{prediction.symbol}</CardTitle>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${signalColors[prediction.signal]}`}>
                {prediction.signal.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">{prediction.timeframe}</span>
              {isExpiringSoon() && (
                <span className="px-2 py-1 rounded-full text-xs font-medium text-orange-600 bg-orange-100 dark:bg-orange-900">
                  Expiring Soon
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className={`text-lg font-bold ${getConfidenceColor(prediction.confidence)}`}>
              {prediction.confidence}%
            </div>
            <div className="text-xs text-gray-500">Confidence</div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Expected Move and Quality */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Expected Move</div>
              <div className={cn(
                "text-lg font-bold",
                prediction.expectedMovePct >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {prediction.expectedMovePct >= 0 ? '+' : ''}{formatPercentage(prediction.expectedMovePct)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Quality Score</div>
              <div className={`text-lg font-bold ${getQualityColor(prediction.quality)}`}>
                {prediction.quality}/100
              </div>
            </div>
          </div>

          {/* Risk/Reward Metrics */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Probability: </span>
              <span className="font-medium">{prediction.riskReward.probability}%</span>
            </div>
            <div>
              <span className="text-gray-500">Sharpe: </span>
              <span className="font-medium">{prediction.riskReward.sharpeRatio.toFixed(1)}</span>
            </div>
          </div>

          {/* Evidence Weights */}
          <div className="space-y-2">
            <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">Evidence Weights</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between">
                <span>Technical:</span>
                <span className="font-medium">{prediction.evidence.technicalWeight}%</span>
              </div>
              <div className="flex justify-between">
                <span>Fundamental:</span>
                <span className="font-medium">{prediction.evidence.fundamentalWeight}%</span>
              </div>
              <div className="flex justify-between">
                <span>Sentiment:</span>
                <span className="font-medium">{prediction.evidence.sentimentWeight}%</span>
              </div>
              <div className="flex justify-between">
                <span>Macro:</span>
                <span className="font-medium">{prediction.evidence.macroWeight}%</span>
              </div>
            </div>
          </div>

          {/* Rationale */}
          <div className="space-y-2">
            <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">Key Rationale</div>
            <div className="space-y-1">
              {prediction.rationale.slice(0, 3).map((reason, index) => (
                <div key={index} className="text-xs text-gray-700 dark:text-gray-300 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <span>{reason}</span>
                </div>
              ))}
              {prediction.rationale.length > 3 && (
                <div className="text-xs text-gray-500 italic">
                  +{prediction.rationale.length - 3} more reasons...
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onSimulate(prediction)}
              className="flex-1"
            >
              Simulate
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => onCreateAlert(prediction)}
              className="flex-1"
            >
              Alert
            </Button>
            <Button 
              size="sm" 
              variant="primary"
              onClick={() => onAutoplan(prediction)}
              className="flex-1"
            >
              Auto-Plan
            </Button>
          </div>

          {/* Metadata */}
          <div className="flex justify-between items-center text-xs text-gray-400 pt-2">
            <span>Created {timeAgo(prediction.createdAt)}</span>
            <span>Expires {timeAgo(prediction.expiresAt)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface PredictionsHubProps {
  className?: string;
}

export function PredictionsHub({ className }: PredictionsHubProps) {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'bullish' | 'bearish' | 'neutral'>('all');
  const [sortBy, setSortBy] = useState<'confidence' | 'quality' | 'created' | 'expires'>('confidence');

  useEffect(() => {
    loadPredictions();
  }, []);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const signals: TradingSignal[] = await apiClient.getTradingSignals();
      // Map trading signals to local prediction view model
      const mapped: Prediction[] = signals.map((s, idx) => ({
        id: `pred_${s.symbol}_${idx}`,
        symbol: s.symbol,
        timeframe: '1d',
        signal: s.signal_type === 'BUY' ? 'bullish' : s.signal_type === 'SELL' ? 'bearish' : 'neutral',
        confidence: Math.round(s.confidence ?? 0),
        expectedMovePct: typeof s.price_target === 'number' ? ((s.price_target - 0) / (s.price_target || 1)) * 100 : 0,
        rationale: s.reasoning ? [s.reasoning] : [],
        quality: Math.min(100, Math.max(0, Math.round((s.strength ?? s.confidence ?? 0)))),
        createdAt: s.timestamp,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        evidence: { technicalWeight: 25, fundamentalWeight: 25, sentimentWeight: 25, macroWeight: 25 },
        riskReward: { probability: Math.round(s.confidence ?? 0), sharpeRatio: 1 }
      }));
      setPredictions(mapped);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load predictions');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = (prediction: Prediction) => {
    console.log('Simulate prediction:', prediction.id);
    // TODO: Open scenario simulator with this prediction
  };

  const handleCreateAlert = (prediction: Prediction) => {
    console.log('Create alert for prediction:', prediction.id);
    // TODO: Open alert creation modal
  };

  const handleAutoplan = (prediction: Prediction) => {
    console.log('Auto-plan for prediction:', prediction.id);
    // TODO: Open plan builder with auto-generated plan
  };

  const filteredAndSortedPredictions = React.useMemo(() => {
    let filtered = predictions;
    
    // Apply filter
    if (filter !== 'all') {
      filtered = filtered.filter(p => p.signal === filter);
    }
    
    // Apply sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence;
        case 'quality':
          return b.quality - a.quality;
        case 'created':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        case 'expires':
          return new Date(a.expiresAt).getTime() - new Date(b.expiresAt).getTime();
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [predictions, filter, sortBy]);

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center h-96", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("text-center py-8", className)}>
        <div className="text-red-600 mb-2">Failed to load predictions</div>
        <div className="text-sm text-gray-500">{error}</div>
        <Button onClick={loadPredictions} className="mt-4">Retry</Button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header and Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">AI Predictions</h2>
          <p className="text-gray-500 dark:text-gray-400">
            {filteredAndSortedPredictions.length} active predictions
          </p>
        </div>
        
        {/* Controls */}
        <div className="flex gap-3">
          {/* Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as typeof filter)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-sm"
          >
            <option value="all">All Signals</option>
            <option value="bullish">Bullish</option>
            <option value="bearish">Bearish</option>
            <option value="neutral">Neutral</option>
          </select>
          
          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-sm"
          >
            <option value="confidence">Confidence</option>
            <option value="quality">Quality</option>
            <option value="created">Created</option>
            <option value="expires">Expires</option>
          </select>
          
          <Button onClick={loadPredictions} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {/* Predictions Grid */}
      {filteredAndSortedPredictions.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No predictions match the current filter
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAndSortedPredictions.map((prediction) => (
            <PredictionCard
              key={prediction.id}
              prediction={prediction}
              onSimulate={handleSimulate}
              onCreateAlert={handleCreateAlert}
              onAutoplan={handleAutoplan}
            />
          ))}
        </div>
      )}
    </div>
  );
}