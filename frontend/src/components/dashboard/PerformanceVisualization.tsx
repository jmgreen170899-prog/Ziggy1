'use client';

import React from 'react';

interface SparklineProps {
  data: number[];
  color?: 'green' | 'red' | 'blue' | 'gray';
  height?: number;
  width?: number;
}

export function Sparkline({ data, color = 'blue', height = 32, width = 80 }: SparklineProps) {
  // Basic guards for dimensions and data
  if (!data || data.length === 0 || !Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return null;
  }

  // Sanitize data to ensure numeric values only
  const series = data
    .map((v) => Number(v))
    .filter((v) => Number.isFinite(v));

  if (series.length === 0) return null;

  const max = Math.max(...series);
  const min = Math.min(...series);
  const range = max - min;

  const getColorClass = (color: string) => {
    switch (color) {
      case 'green':
        return 'fill-green-500';
      case 'red':
        return 'fill-red-500';
      case 'blue':
        return 'fill-blue-500';
      default:
        return 'fill-gray-400';
    }
  };

  // Helpers that avoid NaN/Infinity
  const getX = (index: number) => {
    if (series.length <= 1) return width / 2;
    return (index / (series.length - 1)) * width;
  };

  const getY = (value: number) => {
    if (range <= 0) return height / 2; // flat line when no variation
    return height - ((value - min) / range) * height;
  };

  // Create SVG path for the sparkline
  const pathData = (() => {
    if (series.length < 2 || range <= 0) {
      const yMid = height / 2;
      return `M 0 ${yMid} L ${width} ${yMid}`;
    }
    return series
      .map((value, index) => {
        const x = getX(index);
        const y = getY(value);
        return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  })();

  return (
    <div className="flex items-center">
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" className={getColorClass(color)} stopOpacity="0.8" />
            <stop offset="100%" className={getColorClass(color)} stopOpacity="0.1" />
          </linearGradient>
        </defs>
        
        {/* Fill area under the line */}
        <path
          d={`${pathData} L ${width} ${height} L 0 ${height} Z`}
          fill={`url(#gradient-${color})`}
          className="opacity-30"
        />
        
        {/* The sparkline itself */}
        <path
          d={pathData}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={getColorClass(color).replace('fill-', 'text-')}
        />
        
        {/* Data points */}
        {series.map((value, index) => {
          const x = getX(index);
          const y = getY(value);
          if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="1.5"
              className={getColorClass(color)}
            />
          );
        })}
      </svg>
    </div>
  );
}

interface MiniChartProps {
  data: { label: string; value: number }[];
  type: 'bar' | 'line';
  color?: string;
  height?: number;
}

export function MiniChart({ data, type, color = 'blue', height = 40 }: MiniChartProps) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data.map(d => d.value));
  const min = Math.min(...data.map(d => d.value));
  const range = max - min;

  const getColorClass = () => {
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'red':
        return 'bg-red-500';
      case 'blue':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  if (type === 'bar') {
    return (
      <div className="flex items-end space-x-1" style={{ height: `${height}px` }}>
        {data.map((item, index) => {
          const barHeight = range > 0 ? ((item.value - min) / range) * height : height / 2;
          return (
            <div
              key={index}
              className={`w-2 rounded-t ${getColorClass()} transition-all duration-300 hover:opacity-80`}
              style={{ height: `${barHeight}px` }}
              title={`${item.label}: ${item.value}`}
            />
          );
        })}
      </div>
    );
  }

  // Line chart implementation would go here
  return (
    <div className="text-xs text-fg-muted">
      Line chart implementation pending
    </div>
  );
}

interface PerformanceIndicatorProps {
  label: string;
  value: number;
  change: number;
  trend: number[];
  format?: 'currency' | 'percentage' | 'number';
}

export function PerformanceIndicator({ 
  label, 
  value, 
  change, 
  trend, 
  format = 'currency' 
}: PerformanceIndicatorProps) {
  const isPositive = change >= 0;
  const sparklineColor = isPositive ? 'green' : 'red';
  const changeIcon = isPositive ? '📈' : '📉';
  const pct = value ? (change / value) * 100 : 0;

  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return `$${val.toLocaleString()}`;
      case 'percentage':
        return `${val.toFixed(2)}%`;
      default:
        return val.toLocaleString();
    }
  };

  return (
    <div className="group relative bg-gradient-to-br from-white via-gray-50 to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900 border border-gray-200 dark:border-gray-700 rounded-xl p-5 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer">
      {/* Glow effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl opacity-0 group-hover:opacity-20 transition-opacity duration-300 -z-10"></div>
      
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isPositive ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
          <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
            {label}
          </p>
        </div>
        <span className="text-xl">{changeIcon}</span>
      </div>

      <div className="flex items-end justify-between">
        <div className="flex-1">
          <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {formatValue(value)}
          </p>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 text-sm font-bold rounded-full ${
              isPositive 
                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
            }`}>
              {isPositive ? '+' : ''}{formatValue(change)}
            </span>
            <span className={`text-xs font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              ({change > 0 ? '+' : ''}{pct.toFixed(2)}%)
            </span>
          </div>
        </div>
        
        <div className="flex flex-col items-end ml-4">
          <Sparkline data={trend} color={sparklineColor} width={80} height={32} />
          <span className="text-xs text-gray-500 mt-1 font-medium">7-day trend</span>
        </div>
      </div>
    </div>
  );
}

interface PnLVisualizerProps {
  dailyPnL: number;
  weeklyPnL: number;
  monthlyPnL: number;
  yearlyPnL: number;
  trend: number[];
}

export function PnLVisualizer({ 
  dailyPnL, 
  weeklyPnL, 
  monthlyPnL, 
  yearlyPnL, 
  trend 
}: PnLVisualizerProps) {
  const periods = [
    { label: '1D', value: dailyPnL, key: 'daily' },
    { label: '1W', value: weeklyPnL, key: 'weekly' },
    { label: '1M', value: monthlyPnL, key: 'monthly' },
    { label: '1Y', value: yearlyPnL, key: 'yearly' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">P&L Performance</h4>
        <div className="flex items-center space-x-2">
          <Sparkline data={trend} color={dailyPnL >= 0 ? 'green' : 'red'} width={80} height={32} />
          <span className="text-xs text-fg-muted">30D Trend</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {periods.map((period) => {
          const isPositive = period.value >= 0;
          return (
            <div key={period.key} className="text-center p-3 bg-surface border border-border rounded-lg">
              <p className="text-xs text-fg-muted mb-1">{period.label}</p>
              <p className={`text-sm font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}${period.value.toLocaleString()}
              </p>
              <div className="mt-2 flex justify-center">
                <div className={`w-full h-1 rounded-full ${isPositive ? 'bg-green-200' : 'bg-red-200'}`}>
                  <div 
                    className={`h-1 rounded-full ${isPositive ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(Math.abs(period.value) / 10000 * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}