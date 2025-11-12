'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export function QuickActionsPanel() {
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isRebalancing, setIsRebalancing] = useState(false);

  const handleChatWithZiggy = () => {
    // This would navigate to the chat page with a pre-filled query
    console.log('Navigate to /chat with portfolio analysis query');
    // In real implementation: router.push('/chat?query=analyze-my-portfolio');
  };

  const handleGenerateReport = () => {
    setIsGeneratingReport(true);
    // Simulate report generation
    setTimeout(() => {
      setIsGeneratingReport(false);
      console.log('Portfolio report generated');
    }, 3000);
  };

  const handleRebalancePortfolio = () => {
    setIsRebalancing(true);
    // Simulate rebalancing process
    setTimeout(() => {
      setIsRebalancing(false);
      console.log('Portfolio rebalancing suggestions ready');
    }, 2500);
  };

  const handleScreenStocks = () => {
    console.log('Navigate to stock screener');
    // In real implementation: router.push('/market?action=screen');
  };

  const quickActions = [
    {
      id: 'chat',
      title: '💬 Ask ZiggyAI',
      description: 'Get AI-powered portfolio insights',
      action: handleChatWithZiggy,
      color: 'bg-accent text-accent-fg hover:bg-accent/90',
      shortcuts: ['Portfolio analysis', 'Market outlook', 'Risk assessment'],
      isLoading: false
    },
    {
      id: 'report',
      title: '📊 Generate Report',
      description: 'Create comprehensive portfolio report',
      action: handleGenerateReport,
      color: 'bg-blue-500 text-white hover:bg-blue-600',
      shortcuts: ['Performance summary', 'Risk analysis', 'Tax report'],
      isLoading: isGeneratingReport
    },
    {
      id: 'rebalance',
      title: '⚖️ Rebalance Portfolio',
      description: 'Get optimization recommendations',
      action: handleRebalancePortfolio,
      color: 'bg-green-500 text-white hover:bg-green-600',
      shortcuts: ['Asset allocation', 'Risk adjustment', 'Tax efficiency'],
      isLoading: isRebalancing
    },
    {
      id: 'screen',
      title: '🔍 Screen Stocks',
      description: 'Find new investment opportunities',
      action: handleScreenStocks,
      color: 'bg-purple-500 text-white hover:bg-purple-600',
      shortcuts: ['Growth stocks', 'Value picks', 'Dividend stocks'],
      isLoading: false
    }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span>⚡</span>
            <span>Quick Actions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickActions.map((action) => (
              <div
                key={action.id}
                className="p-4 border border-border rounded-lg hover:shadow-md transition-all duration-200 group"
              >
                <div className="flex flex-col space-y-3">
                  <Button
                    onClick={action.action}
                    disabled={action.isLoading}
                    className={`w-full justify-start text-left h-auto py-3 px-4 ${action.color}`}
                  >
                    <div className="flex items-center space-x-3 w-full">
                      {action.isLoading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      ) : (
                        <span className="text-lg">{action.title.split(' ')[0]}</span>
                      )}
                      <div className="flex-1 text-left">
                        <p className="font-medium">{action.title.split(' ').slice(1).join(' ')}</p>
                        <p className="text-xs opacity-90">{action.description}</p>
                      </div>
                    </div>
                  </Button>
                  
                  {/* Quick shortcuts */}
                  <div className="flex flex-wrap gap-1">
                    {action.shortcuts.map((shortcut, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          console.log(`Quick action: ${shortcut}`);
                          action.action();
                        }}
                        className="text-xs px-2 py-1 bg-surface border border-border rounded-full hover:bg-surface-hover transition-colors text-fg-muted hover:text-fg"
                      >
                        {shortcut}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Trading Shortcuts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span>🚀</span>
            <span>Trading Shortcuts</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button
              variant="ghost"
              className="h-auto py-3 flex flex-col items-center space-y-1 hover:bg-green-50 hover:text-green-700 hover:border-green-200"
              onClick={() => console.log('Quick buy action')}
            >
              <span className="text-xl">📈</span>
              <span className="text-xs">Quick Buy</span>
            </Button>
            
            <Button
              variant="ghost"
              className="h-auto py-3 flex flex-col items-center space-y-1 hover:bg-red-50 hover:text-red-700 hover:border-red-200"
              onClick={() => console.log('Quick sell action')}
            >
              <span className="text-xl">📉</span>
              <span className="text-xs">Quick Sell</span>
            </Button>
            
            <Button
              variant="ghost"
              className="h-auto py-3 flex flex-col items-center space-y-1 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200"
              onClick={() => console.log('Set alerts action')}
            >
              <span className="text-xl">🔔</span>
              <span className="text-xs">Set Alerts</span>
            </Button>
            
            <Button
              variant="ghost"
              className="h-auto py-3 flex flex-col items-center space-y-1 hover:bg-purple-50 hover:text-purple-700 hover:border-purple-200"
              onClick={() => console.log('View orders action')}
            >
              <span className="text-xl">📋</span>
              <span className="text-xs">View Orders</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span>📜</span>
              <span>Recent Actions</span>
            </div>
            <Button variant="ghost" size="sm" className="text-xs">
              View All
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { time: '10:30 AM', action: 'Generated portfolio report', type: 'report', status: 'completed' },
              { time: '09:45 AM', action: 'Asked ZiggyAI about AAPL', type: 'chat', status: 'completed' },
              { time: '09:20 AM', action: 'Screened growth stocks', type: 'screen', status: 'completed' },
              { time: 'Yesterday', action: 'Portfolio rebalancing', type: 'rebalance', status: 'pending' }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-2 rounded-lg hover:bg-surface-hover transition-colors">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    item.status === 'completed' ? 'bg-green-500' : 
                    item.status === 'pending' ? 'bg-yellow-500' : 'bg-gray-300'
                  }`}></div>
                  <div>
                    <p className="text-sm font-medium">{item.action}</p>
                    <p className="text-xs text-fg-muted">{item.time}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  item.status === 'completed' ? 'bg-green-100 text-green-700' :
                  item.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}