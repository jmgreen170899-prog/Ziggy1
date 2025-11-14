'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/Card';

interface MarketSession {
  name: string;
  timezone: string;
  isOpen: boolean;
  openTime: string;
  closeTime: string;
  currentTime: string;
  nextSession?: string;
}

interface ConnectionStatus {
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  latency: number;
  lastUpdate: Date;
}

export function MarketStatusIndicators() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [connectionStatus] = useState<ConnectionStatus>({
    status: 'connected',
    latency: 45,
    lastUpdate: new Date()
  });

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Mock market sessions data
  const marketSessions: MarketSession[] = [
    {
      name: 'US Markets',
      timezone: 'EST',
      isOpen: true,
      openTime: '09:30',
      closeTime: '16:00',
      currentTime: currentTime.toLocaleTimeString('en-US', { 
        timeZone: 'America/New_York',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      }),
      nextSession: 'Pre-market opens at 04:00'
    },
    {
      name: 'European Markets',
      timezone: 'CET',
      isOpen: false,
      openTime: '09:00',
      closeTime: '17:30',
      currentTime: currentTime.toLocaleTimeString('en-US', { 
        timeZone: 'Europe/London',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      }),
      nextSession: 'Opens in 12h 30m'
    },
    {
      name: 'Asian Markets',
      timezone: 'JST',
      isOpen: false,
      openTime: '09:00',
      closeTime: '15:00',
      currentTime: currentTime.toLocaleTimeString('en-US', { 
        timeZone: 'Asia/Tokyo',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      }),
      nextSession: 'Opens in 8h 15m'
    }
  ];

  const getConnectionStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-success bg-success/10';
      case 'connecting':
        return 'text-warning bg-warning/10';
      case 'disconnected':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-danger bg-danger/10';
    }
  };

  const getConnectionIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return '🟢';
      case 'connecting':
        return '🟡';
      case 'disconnected':
        return '⚪';
      default:
        return '🔴';
    }
  };

  const getLatencyColor = (latency: number) => {
    if (latency < 50) return 'text-success';
    if (latency < 100) return 'text-warning';
    return 'text-danger';
  };

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <Card className="bg-gradient-to-br from-white to-blue-50 dark:from-gray-900 dark:to-blue-950 border-secondary-aqua/30 dark:border-secondary-aqua/50">
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-bold text-lg flex items-center space-x-2 text-primary-tech-blue dark:text-secondary-cyan">
              <div className="w-8 h-8 bg-primary-tech-blue/10 dark:bg-secondary-cyan/10 rounded-lg flex items-center justify-center">
                <span>📡</span>
              </div>
              <span>Live Connection</span>
            </h4>
            <div className={`px-3 py-1 rounded-full text-sm font-bold shadow-md ${getConnectionStatusColor(connectionStatus.status)}`}>
              {getConnectionIcon(connectionStatus.status)} {connectionStatus.status.toUpperCase()}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-surface/50 dark:bg-gray-800/50 p-3 rounded-lg border border-border">
              <span className="text-fg-muted text-sm">Latency:</span>
              <div className={`text-xl font-bold font-mono ${getLatencyColor(connectionStatus.latency)}`}>
                {connectionStatus.latency}ms
              </div>
            </div>
            <div className="bg-surface/50 dark:bg-gray-800/50 p-3 rounded-lg border border-border">
              <span className="text-fg-muted text-sm">Last Update:</span>
              <div className="text-sm font-medium font-mono text-fg">
                {connectionStatus.lastUpdate.toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </div>
            </div>
          </div>
          
          {/* Connection Quality Indicator */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-fg-muted mb-1">
              <span>Connection Quality</span>
              <span className="font-medium">Excellent</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="bg-success rounded-full h-2" style={{ width: '95%' }}></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Market Hours */}
      <Card>
        <CardContent className="p-4">
          <h4 className="font-semibold mb-3 flex items-center space-x-2">
            <span>🌍</span>
            <span>Global Market Hours</span>
          </h4>
          
          <div className="space-y-3">
            {marketSessions.map((session, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-surface border border-border rounded-lg hover:border-primary-tech-blue/50 transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${session.isOpen ? 'bg-success animate-pulse' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                  <div>
                    <p className="font-medium text-fg">{session.name}</p>
                    <p className="text-xs text-fg-muted font-mono">
                      {session.openTime} - {session.closeTime} {session.timezone}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="font-medium font-mono text-fg">{session.currentTime}</p>
                  <p className={`text-xs ${session.isOpen ? 'text-success font-medium' : 'text-fg-muted'}`}>
                    {session.isOpen ? 'OPEN' : session.nextSession}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Market Overview */}
      <Card>
        <CardContent className="p-4">
          <h4 className="font-semibold mb-3 flex items-center space-x-2">
            <span>📊</span>
            <span>Market Overview</span>
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            {/* Major Indices */}
            <div>
              <h5 className="text-sm font-medium text-fg-muted mb-2">Major Indices</h5>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">S&P 500</span>
                  <div className="text-right">
                    <span className="text-sm font-medium font-mono text-fg">4,567.89</span>
                    <span className="text-xs text-success ml-1 font-mono">+0.85%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">NASDAQ</span>
                  <div className="text-right">
                    <span className="text-sm font-medium font-mono text-fg">14,321.56</span>
                    <span className="text-xs text-success ml-1 font-mono">+1.24%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">Dow Jones</span>
                  <div className="text-right">
                    <span className="text-sm font-medium font-mono text-fg">34,785.23</span>
                    <span className="text-xs text-danger ml-1 font-mono">-0.42%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Market Sentiment */}
            <div>
              <h5 className="text-sm font-medium text-fg-muted mb-2">Market Sentiment</h5>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">Fear & Greed</span>
                  <span className="text-sm font-medium font-mono text-success">72 (Greed)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">VIX</span>
                  <span className="text-sm font-medium font-mono text-fg">18.45</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-fg-muted">Volume</span>
                  <span className="text-sm font-medium text-primary-tech-blue">Above Avg</span>
                </div>
              </div>
            </div>
          </div>

          {/* Economic Events */}
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <span>📅</span>
              <h5 className="text-sm font-medium text-yellow-800">Today&apos;s Economic Events</h5>
            </div>
            <div className="space-y-1 text-sm text-yellow-700">
              <div className="flex justify-between">
                <span>10:00 AM - Consumer Price Index</span>
                <span className="font-medium">High Impact</span>
              </div>
              <div className="flex justify-between">
                <span>2:00 PM - Fed Chair Speech</span>
                <span className="font-medium">Medium Impact</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}