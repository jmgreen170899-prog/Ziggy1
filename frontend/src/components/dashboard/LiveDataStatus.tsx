/**
 * Live Data Status Indicator - Shows real-time connection status
 * Provides visual feedback about WebSocket connectivity
 */
'use client';

import React from 'react';
import { WifiOff, Activity, AlertCircle } from 'lucide-react';
import { useLiveData } from '@/hooks/useLiveData';
import { cn } from '@/utils';

interface LiveDataStatusProps {
  showLabel?: boolean;
  compact?: boolean;
  className?: string;
}

export function LiveDataStatus({ 
  showLabel = true, 
  compact = false,
  className 
}: LiveDataStatusProps) {
  const { connectionStatus, isConnected, error, stats } = useLiveData({
    autoConnect: true,
    symbols: ['SPY'], // Minimal connection for status only
  });

  const getStatusColor = () => {
    if (error) return 'text-red-500';
    if (isConnected) return 'text-green-500';
    return 'text-yellow-500';
  };

  const getStatusIcon = () => {
    if (error) return AlertCircle;
    if (isConnected) return Activity;
    return WifiOff;
  };

  const getStatusText = () => {
    if (error) return 'Error';
    if (isConnected) return 'Live';
    return 'Connecting';
  };

  const getConnectionDetails = () => {
    const connected = Object.values(connectionStatus).filter(Boolean).length;
    const total = Object.keys(connectionStatus).length;
    return `${connected}/${total}`;
  };

  const StatusIcon = getStatusIcon();

  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <StatusIcon className={cn("w-3 h-3", getStatusColor())} />
        {showLabel && (
          <span className={cn("text-xs font-medium", getStatusColor())}>
            {getStatusText()}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-2 p-2 rounded-lg bg-gray-50 border", className)}>
      <StatusIcon className={cn("w-4 h-4", getStatusColor())} />
      
      <div className="flex-1 min-w-0">
        {showLabel && (
          <div className="flex items-center justify-between">
            <span className={cn("text-sm font-medium", getStatusColor())}>
              {getStatusText()}
            </span>
            <span className="text-xs text-gray-500">
              {getConnectionDetails()}
            </span>
          </div>
        )}
        
        {isConnected && stats.totalQuotes > 0 && (
          <div className="text-xs text-gray-600 mt-1">
            {stats.totalQuotes} quotes • {stats.totalNews} news
          </div>
        )}
        
        {error && (
          <div className="text-xs text-red-600 mt-1 truncate">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveDataStatus;