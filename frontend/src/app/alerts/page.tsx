'use client';

import React, { useState, useEffect } from 'react';
import { RequireAuth } from '@/routes/RequireAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { PageLayout, ThemedButton, ThemedCard } from '@/components/layout/PageLayout';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { CardSkeleton } from '@/components/ui/Loading';
import { formatCurrency, formatDateTime } from '@/utils';
import apiClient from '@/services/api';
import type { Alert } from '@/types/api';

interface AlertCardProps {
  alert: Alert;
  onToggle?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

function AlertCard({ alert, onToggle, onEdit, onDelete }: AlertCardProps) {
  const getAlertTypeColor = (type: string) => {
    switch (type) {
      case 'price': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'volume': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'technical': return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300';
      case 'news': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getAlertTypeIcon = (type: string) => {
    switch (type) {
      case 'price': return '💰';
      case 'volume': return '📊';
      case 'technical': return '📈';
      case 'news': return '📰';
      default: return '🔔';
    }
  };

  const getConditionText = (condition: string, targetValue: number, symbol: string) => {
    switch (condition) {
      case 'price_above': return `${symbol} price > ${formatCurrency(targetValue)}`;
      case 'price_below': return `${symbol} price < ${formatCurrency(targetValue)}`;
      case 'volume_spike': return `${symbol} volume > ${(targetValue / 1000000).toFixed(1)}M`;
      case 'rsi_oversold': return `${symbol} RSI < ${targetValue}`;
      case 'rsi_overbought': return `${symbol} RSI > ${targetValue}`;
      case 'earnings_release': return `${symbol} earnings announcement`;
      default: return condition;
    }
  };

  const isCloseToTriggering = () => {
    if (!alert.is_active) return false;
    
    const diff = Math.abs(alert.current_value - alert.target_value);
    const threshold = alert.target_value * 0.02; // 2% threshold
    
    return diff <= threshold;
  };

  return (
    <Card className={`hover:shadow-md transition-shadow ${alert.triggered_at ? 'border-green-200 dark:border-green-800' : isCloseToTriggering() ? 'border-yellow-200 dark:border-yellow-800' : ''}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getAlertTypeIcon(alert.type)}</span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">{alert.symbol}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAlertTypeColor(alert.type)}`}>
                  {alert.type.toUpperCase()}
                </span>
                {alert.triggered_at && (
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                    TRIGGERED
                  </span>
                )}
                {!alert.is_active && !alert.triggered_at && (
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                    PAUSED
                  </span>
                )}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {getConditionText(alert.condition, alert.target_value, alert.symbol)}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              onClick={() => onToggle?.(alert.id)}
              variant="ghost"
              size="sm"
              className={alert.is_active ? 'text-green-600' : 'text-gray-400'}
            >
              {alert.is_active ? '🔔' : '🔕'}
            </Button>
            <Button onClick={() => onEdit?.(alert.id)} variant="ghost" size="sm">
              ✏️
            </Button>
            <Button onClick={() => onDelete?.(alert.id)} variant="ghost" size="sm" className="text-red-500">
              🗑️
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-sm">
            <span className="text-gray-500">Message:</span>
            <div className="font-medium mt-1">{alert.message}</div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Target:</span>
              <div className="font-medium">
                {alert.type === 'price' ? formatCurrency(alert.target_value) : 
                 alert.type === 'volume' ? `${(alert.target_value / 1000000).toFixed(1)}M` : 
                 alert.target_value.toString()}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Current:</span>
              <div className="font-medium">
                {alert.type === 'price' ? formatCurrency(alert.current_value) : 
                 alert.type === 'volume' ? `${(alert.current_value / 1000000).toFixed(1)}M` : 
                 alert.current_value.toString()}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Created:</span>
              <div className="font-medium">{formatDateTime(alert.created_at)}</div>
            </div>
            {alert.triggered_at && (
              <div>
                <span className="text-gray-500">Triggered:</span>
                <div className="font-medium text-green-600">{formatDateTime(alert.triggered_at)}</div>
              </div>
            )}
          </div>
          
          {isCloseToTriggering() && alert.is_active && (
            <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
              <div className="text-sm text-yellow-800 dark:text-yellow-200 font-medium">
                ⚡ Close to triggering!
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface CreateAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (alert: Partial<Alert>) => void;
}

function CreateAlertModal({ isOpen, onClose, onSave }: CreateAlertModalProps) {
  const [formData, setFormData] = useState({
    type: 'price' as Alert['type'],
    symbol: 'AAPL',
    condition: 'price_above',
    target_value: '',
    message: ''
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      target_value: parseFloat(formData.target_value),
      is_active: true,
      created_at: new Date().toISOString(),
      current_value: 0 // Would be fetched from API
    });
    onClose();
    setFormData({
      type: 'price',
      symbol: 'AAPL',
      condition: 'price_above',
      target_value: '',
      message: ''
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Create New Alert</CardTitle>
            <Button onClick={onClose} variant="ghost" size="sm">✕</Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
                Alert Type
              </label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as Alert['type'] })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                required
              >
                <option value="price">Price Alert</option>
                <option value="volume">Volume Alert</option>
                <option value="technical">Technical Alert</option>
                <option value="news">News Alert</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
                Symbol
              </label>
              <input
                type="text"
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                placeholder="AAPL"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
                Condition
              </label>
              <select
                value={formData.condition}
                onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                required
              >
                <option value="price_above">Price Above</option>
                <option value="price_below">Price Below</option>
                <option value="volume_spike">Volume Spike</option>
                <option value="rsi_oversold">RSI Oversold</option>
                <option value="rsi_overbought">RSI Overbought</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
                Target Value
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.target_value}
                onChange={(e) => setFormData({ ...formData, target_value: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                placeholder="180.00"
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2 block">
                Message
              </label>
              <textarea
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                rows={3}
                placeholder="Alert message..."
                required
              />
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" className="flex-1">
                Create Alert
              </Button>
              <Button type="button" onClick={onClose} variant="ghost" className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

interface AlertStatsProps {
  alerts: Alert[];
}

function AlertStats({ alerts }: AlertStatsProps) {
  const activeAlerts = alerts.filter(a => a.is_active).length;
  const triggeredAlerts = alerts.filter(a => a.triggered_at).length;
  const recentTriggers = alerts.filter(a => 
    a.triggered_at && 
    new Date(a.triggered_at) > new Date(Date.now() - 86400000)
  ).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardContent className="p-6 text-center">
          <div className="text-3xl font-bold text-blue-600">{activeAlerts}</div>
          <div className="text-sm text-gray-500 mt-1">Active Alerts</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6 text-center">
          <div className="text-3xl font-bold text-green-600">{triggeredAlerts}</div>
          <div className="text-sm text-gray-500 mt-1">Total Triggered</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-6 text-center">
          <div className="text-3xl font-bold text-yellow-600">{recentTriggers}</div>
          <div className="text-sm text-gray-500 mt-1">Last 24h</div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<'all' | 'active' | 'triggered'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const alertsData = await apiClient.getAlerts();
      setAlerts(alertsData);
    } catch (err) {
      console.error('Failed to load alerts:', err);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const filteredAlerts = alerts.filter(alert => {
    switch (filter) {
      case 'active': return alert.is_active && !alert.triggered_at;
      case 'triggered': return alert.triggered_at;
      default: return true;
    }
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAlerts();
    setRefreshing(false);
  };

  const handleToggleAlert = (id: string) => {
    setAlerts(alerts.map(alert => 
      alert.id === id ? { ...alert, is_active: !alert.is_active } : alert
    ));
  };

  const handleEditAlert = (id: string) => {
    alert(`Edit alert ${id} - This would open the edit modal`);
  };

  const handleDeleteAlert = (id: string) => {
    if (confirm('Are you sure you want to delete this alert?')) {
      setAlerts(alerts.filter(alert => alert.id !== id));
    }
  };

  const handleCreateAlert = (newAlert: Partial<Alert>) => {
    const alert: Alert = {
      ...newAlert as Alert,
      id: `alert_${Date.now()}`,
      current_value: 0 // Would be fetched from API
    };
    setAlerts([alert, ...alerts]);
  };

  return (
    <RequireAuth>
      <ErrorBoundary 
        fallback={
          <PageLayout 
            title="Price Alerts" 
            subtitle="Set up custom alerts for price movements, volume spikes, and market events"
            breadcrumbs={['Alerts']}
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <CardSkeleton showHeader contentLines={4} />
              </div>
              <div className="space-y-6">
                <CardSkeleton showHeader contentLines={3} />
              </div>
            </div>
          </PageLayout>
        }
      >
        <PageLayout 
          title="Price Alerts" 
          subtitle="Set up custom alerts for price movements, volume spikes, and market events"
          breadcrumbs={['Alerts']}
          rightContent={
            <div className="flex items-center gap-2">
              <ThemedButton onClick={() => setShowCreateModal(true)} variant="primary">
                + Create Alert
            </ThemedButton>
            <ThemedButton 
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
            >
              {refreshing ? '🔄' : '↻'} Refresh
            </ThemedButton>
          </div>
        }
      >
        <div className="space-y-6">
          {/* Alert Stats */}
          <AlertStats alerts={alerts} />

          {/* Filter Tabs */}
          <div className="flex gap-2">
            {[
              { key: 'all', label: 'All Alerts' },
              { key: 'active', label: 'Active' },
              { key: 'triggered', label: 'Triggered' }
            ].map(tab => (
              <ThemedButton
                key={tab.key}
                onClick={() => setFilter(tab.key as typeof filter)}
                variant={filter === tab.key ? 'primary' : 'outline'}
                size="sm"
              >
                {tab.label}
              </ThemedButton>
            ))}
          </div>

          {/* Alerts List */}
          <div className="space-y-4">
            {loading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <ThemedCard key={i} className="animate-pulse">
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                        </div>
                      </div>
                    </CardContent>
                  </ThemedCard>
                ))}
              </div>
            ) : error ? (
              <ThemedCard>
                <CardContent className="p-12 text-center">
                  <div className="text-red-500 text-6xl mb-4">⚠️</div>
                  <div className="text-xl font-medium text-red-600 dark:text-red-400 mb-2">
                    Failed to Load Alerts
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-500 mb-4">
                    {error}
                  </div>
                  <ThemedButton onClick={loadAlerts} variant="outline">
                    Try Again
                  </ThemedButton>
                </CardContent>
              </ThemedCard>
            ) : filteredAlerts.length === 0 ? (
              <ThemedCard>
                <CardContent className="p-12 text-center">
                  <div className="text-6xl mb-4">🔔</div>
                  <div className="text-xl font-medium text-gray-600 dark:text-gray-400">
                    No alerts found
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    {filter === 'all' ? 'Create your first alert to get started' : 
                     filter === 'active' ? 'No active alerts at the moment' : 
                     'No alerts have been triggered yet'}
                  </div>
                  {filter === 'all' && (
                    <ThemedButton onClick={() => setShowCreateModal(true)} className="mt-4">
                      Create Your First Alert
                    </ThemedButton>
                  )}
                </CardContent>
              </ThemedCard>
            ) : (
              filteredAlerts.map(alert => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onToggle={handleToggleAlert}
                  onEdit={handleEditAlert}
                  onDelete={handleDeleteAlert}
                />
              ))
            )}
          </div>

          {/* Create Alert Modal */}
          <CreateAlertModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            onSave={handleCreateAlert}
          />
        </div>
      </PageLayout>
      </ErrorBoundary>
    </RequireAuth>
  );
}