'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Sparkline } from './PerformanceVisualization';
import { InlineTooltip } from '@/components/ui/Tooltip';
import { getTermTooltip } from '@/utils/glossary';

interface AdvancedMetric {
  label: string;
  value: number;
  benchmark?: number;
  format: 'percentage' | 'ratio' | 'currency' | 'number';
  description: string;
  trend?: number[];
  status: 'excellent' | 'good' | 'fair' | 'poor';
}

interface AdvancedPortfolioMetricsProps {
  portfolioValue: number;
}

export function AdvancedPortfolioMetrics({ portfolioValue }: AdvancedPortfolioMetricsProps) {
  // Example advanced metrics - in real implementation, these would be calculated from portfolio data
  const advancedMetrics: AdvancedMetric[] = [
    {
      label: 'Sharpe Ratio',
      value: 1.42,
      benchmark: 1.1,
      format: 'ratio',
      description: 'Risk-adjusted return efficiency (higher is better)',
      trend: [1.1, 1.2, 1.3, 1.35, 1.4, 1.38, 1.42],
      status: 'excellent'
    },
    {
      label: 'Beta',
      value: 0.85,
      benchmark: 1.0,
      format: 'ratio',
      description: 'Portfolio volatility vs market (1.0 = market volatility)',
      trend: [0.9, 0.88, 0.87, 0.86, 0.84, 0.83, 0.85],
      status: 'good'
    },
    {
      label: 'Volatility',
      value: 18.5,
      benchmark: 22.0,
      format: 'percentage',
      description: 'Annualized standard deviation of returns',
      trend: [22, 21, 20, 19.5, 19, 18.8, 18.5],
      status: 'good'
    },
    {
      label: 'Max Drawdown',
      value: -8.2,
      benchmark: -15.0,
      format: 'percentage',
      description: 'Largest peak-to-trough decline',
      trend: [-12, -10, -9, -8.5, -8.3, -8.1, -8.2],
      status: 'excellent'
    },
    {
      label: 'Sortino Ratio',
      value: 2.18,
      benchmark: 1.5,
      format: 'ratio',
      description: 'Downside risk-adjusted returns',
      trend: [1.8, 1.9, 2.0, 2.1, 2.15, 2.16, 2.18],
      status: 'excellent'
    },
    {
      label: 'Alpha',
      value: 3.2,
      benchmark: 0.0,
      format: 'percentage',
      description: 'Excess return over market benchmark',
      trend: [2.1, 2.4, 2.8, 3.0, 3.1, 3.0, 3.2],
      status: 'excellent'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-success bg-success/10 border-success/30';
      case 'good':
        return 'text-primary-tech-blue bg-primary-tech-blue/10 border-primary-tech-blue/30';
      case 'fair':
        return 'text-warning bg-warning/10 border-warning/30';
      default:
        return 'text-danger bg-danger/10 border-danger/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent':
        return '🎯';
      case 'good':
        return '✅';
      case 'fair':
        return '⚡';
      default:
        return '⚠️';
    }
  };

  const formatValue = (value: number, format: string) => {
    switch (format) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'ratio':
        return value.toFixed(2);
      case 'currency':
        return `$${value.toLocaleString()}`;
      default:
        return value.toFixed(2);
    }
  };

  const getSparklineColor = (current: number, benchmark?: number) => {
    if (!benchmark) return 'blue';
    return current > benchmark ? 'green' : current < benchmark ? 'red' : 'blue';
  };

  const getMetricKey = (label: string): string => {
    // Map metric labels to glossary keys
    const labelMap: Record<string, string> = {
      'Sharpe Ratio': 'sharpeRatio',
      'Beta': 'beta',
      'Volatility': 'volatility',
      'Max Drawdown': 'maxDrawdown',
      'Sortino Ratio': 'sortinoRatio',
      'Alpha': 'alpha'
    };
    return labelMap[label] || '';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>📊 Advanced Portfolio Metrics</span>
          <div className="text-sm text-fg-muted">
            Portfolio: ${portfolioValue.toLocaleString()}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {advancedMetrics.map((metric, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${getStatusColor(metric.status)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-1 mb-1">
                    <span>{getStatusIcon(metric.status)}</span>
                    <h4 className="font-semibold text-sm">{metric.label}</h4>
                    <InlineTooltip 
                      content={
                        <div className="space-y-2">
                          <div>{getTermTooltip(getMetricKey(metric.label))}</div>
                        </div>
                      } 
                    />
                  </div>
                  <p className="text-2xl font-bold font-mono mb-1">
                    {formatValue(metric.value, metric.format)}
                  </p>
                  
                  {metric.benchmark && (
                    <div className="flex items-center space-x-2 text-xs">
                      <span className="text-fg-muted">vs benchmark:</span>
                      <span className={`font-medium font-mono ${
                        metric.value > metric.benchmark ? 'text-success' : 
                        metric.value < metric.benchmark ? 'text-danger' : 'text-gray-600'
                      }`}>
                        {formatValue(metric.benchmark, metric.format)}
                      </span>
                    </div>
                  )}
                </div>
                
                {metric.trend && (
                  <div className="flex flex-col items-end">
                    <Sparkline 
                      data={metric.trend} 
                      color={getSparklineColor(metric.value, metric.benchmark)}
                      width={50}
                      height={20}
                    />
                    <span className="text-xs text-fg-muted mt-1">7D</span>
                  </div>
                )}
              </div>
              
              <p className="text-xs text-fg-muted mt-2">
                {metric.description}
              </p>
            </div>
          ))}
        </div>

  {/* Risk-Return Scatter Plot preview */}
        <div className="mt-6 p-4 bg-surface border border-border rounded-lg">
          <h4 className="font-semibold mb-3 flex items-center space-x-2">
            <span>📈</span>
            <span>Risk-Return Profile</span>
          </h4>
          <div className="relative h-32 bg-gradient-to-br from-primary-tech-blue/5 to-success/5 rounded-lg flex items-center justify-center border border-border">
            <div className="text-center">
              <div className="text-2xl mb-2">📊</div>
              <p className="text-sm text-fg-muted">Risk-Return Scatter Plot</p>
              <p className="text-xs text-fg-muted">Interactive chart placeholder</p>
            </div>
            
            {/* Example data points */}
            <div className="absolute top-4 right-8 w-2 h-2 bg-success rounded-full" title="Your Portfolio"></div>
            <div className="absolute bottom-8 left-12 w-2 h-2 bg-primary-tech-blue rounded-full" title="S&P 500"></div>
            <div className="absolute top-12 left-20 w-2 h-2 bg-danger rounded-full" title="High Risk Asset"></div>
          </div>
          <div className="flex justify-between text-xs text-fg-muted mt-2">
            <span>Lower Risk →</span>
            <span>← Higher Return</span>
          </div>
        </div>

        {/* 52-Week Performance Indicators */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-surface border border-border rounded-lg">
            <h5 className="font-semibold mb-3 flex items-center space-x-2">
              <span>📅</span>
              <span>52-Week Performance</span>
            </h5>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-fg-muted">52W High:</span>
                <span className="font-semibold font-mono text-success">$135,420</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-primary-tech-blue to-ai-purple rounded-full h-2" style={{ width: '78%' }}></div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-fg-muted">52W Low:</span>
                <span className="font-semibold font-mono text-danger">$89,650</span>
              </div>
              <div className="text-center text-sm text-fg-muted">
                Current: 78% of 52W range
              </div>
            </div>
          </div>

          <div className="p-4 bg-surface border border-border rounded-lg">
            <h5 className="font-semibold mb-3 flex items-center space-x-2">
              <span>🎯</span>
              <span>Performance vs Benchmarks</span>
            </h5>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-fg-muted">vs S&P 500:</span>
                <span className="font-semibold text-green-600">+15.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-fg-muted">vs NASDAQ:</span>
                <span className="font-semibold text-green-600">+8.7%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-fg-muted">vs Russell 2000:</span>
                <span className="font-semibold text-green-600">+22.1%</span>
              </div>
              <div className="text-center text-sm text-accent font-medium">
                Outperforming all benchmarks 🎉
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}