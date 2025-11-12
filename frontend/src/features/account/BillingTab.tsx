'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { 
  CreditCardIcon, 
  DownloadIcon, 
  CheckCircleIcon, 
  AlertCircleIcon,
  CalendarIcon,
  DollarSignIcon,
  TrendingUpIcon,
  FileTextIcon,
  StarIcon,
  ZapIcon,
  CrownIcon
} from 'lucide-react';

interface BillingHistory {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  invoiceUrl?: string;
}

interface UsageData {
  period: string;
  apiCalls: number;
  dataProcessed: number; // GB
  alerts: number;
  limit: {
    apiCalls: number;
    dataProcessed: number;
    alerts: number;
  };
}

export const BillingTab: React.FC = () => {
  const { user, isLoading, error, clearError } = useAuthStore();
  
  const [successMessage, setSuccessMessage] = useState('');
  const [activeSection, setActiveSection] = useState<string | null>(null);
  
  // Example billing data
  const [currentPlan] = useState({
    name: 'Professional',
    price: 49,
    period: 'month',
    features: [
      'Unlimited API calls',
      '50GB data processing',
      '1000 alerts per month',
      'Advanced analytics',
      'Priority support',
      'Custom integrations'
    ],
    nextBilling: '2024-02-15',
  });

  const [billingHistory] = useState<BillingHistory[]>([
    {
      id: '1',
      date: '2024-01-15',
      description: 'Professional Plan - January 2024',
      amount: 49.00,
      status: 'paid',
      invoiceUrl: '#',
    },
    {
      id: '2',
      date: '2023-12-15',
      description: 'Professional Plan - December 2023',
      amount: 49.00,
      status: 'paid',
      invoiceUrl: '#',
    },
    {
      id: '3',
      date: '2023-11-15',
      description: 'Professional Plan - November 2023',
      amount: 49.00,
      status: 'paid',
      invoiceUrl: '#',
    },
  ]);

  const [usageData] = useState<UsageData>({
    period: 'January 2024',
    apiCalls: 8750,
    dataProcessed: 32.5,
    alerts: 420,
    limit: {
      apiCalls: -1, // unlimited
      dataProcessed: 50,
      alerts: 1000,
    },
  });

  const plans = [
    {
      name: 'Starter',
      price: 9,
      period: 'month',
      icon: StarIcon,
      description: 'Perfect for individual traders',
      features: [
        '5,000 API calls/month',
        '2GB data processing',
        '50 alerts per month',
        'Basic analytics dashboard',
        'Email support',
        '5 custom watchlists',
      ],
      isCurrent: false,
      badge: null,
    },
    {
      name: 'Basic',
      price: 19,
      period: 'month',
      icon: StarIcon,
      description: 'Great for getting started',
      features: [
        '10,000 API calls/month',
        '5GB data processing',
        '100 alerts per month',
        'Basic analytics',
        'Email support',
        '10 custom watchlists',
        'Mobile app access',
      ],
      isCurrent: false,
      badge: null,
    },
    {
      name: 'Professional',
      price: 49,
      period: 'month',
      icon: ZapIcon,
      description: 'For growing businesses and active traders',
      features: [
        'Unlimited API calls',
        '50GB data processing',
        '1,000 alerts per month',
        'Advanced analytics',
        'Priority support',
        'Custom integrations',
        'Unlimited watchlists',
        'Real-time data feeds',
        'Portfolio analytics',
      ],
      isCurrent: true,
      badge: 'Most Popular',
    },
    {
      name: 'Premium',
      price: 99,
      period: 'month',
      icon: TrendingUpIcon,
      description: 'For serious traders and small teams',
      features: [
        'Unlimited API calls',
        '200GB data processing',
        '5,000 alerts per month',
        'Advanced analytics',
        'Priority support',
        'Custom integrations',
        'Multi-user access (5 seats)',
        'Advanced backtesting',
        'Risk management tools',
        'Custom indicators',
        'API access',
      ],
      isCurrent: false,
      badge: 'Best Value',
    },
    {
      name: 'Enterprise',
      price: 199,
      period: 'month',
      icon: CrownIcon,
      description: 'For large organizations and institutions',
      features: [
        'Unlimited everything',
        'Unlimited data processing',
        'Unlimited alerts',
        'Advanced analytics',
        'Dedicated support manager',
        'Custom integrations',
        'Unlimited user seats',
        'SLA guarantee (99.9% uptime)',
        'White-label options',
        'Custom deployment',
        'Advanced compliance tools',
        'Institutional data feeds',
      ],
      isCurrent: false,
      badge: null,
    },
    {
      name: 'Custom',
      price: null,
      period: 'contact us',
      icon: CrownIcon,
      description: 'Tailored solutions for enterprise needs',
      features: [
        'Custom API limits',
        'Dedicated infrastructure',
        'Custom data processing',
        'Unlimited everything',
        '24/7 dedicated support',
        'Custom integrations',
        'On-premise deployment',
        'Custom SLA agreements',
        'Regulatory compliance',
        'Custom training',
        'Dedicated account manager',
        'Custom reporting',
      ],
      isCurrent: false,
      badge: 'Contact Sales',
    },
  ];

  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'text-success';
      case 'pending':
        return 'text-warning';
      case 'failed':
        return 'text-danger';
      default:
        return 'text-fg-muted';
    }
  };

  const handlePlanChange = async (planName: string) => {
    clearError();
    setSuccessMessage('');
    
    try {
      // Mock plan change
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccessMessage(`Successfully upgraded to ${planName} plan!`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error handling would go here
    }
  };

  const handleCancelSubscription = async () => {
    clearError();
    setSuccessMessage('');
    
    try {
      // Mock subscription cancellation
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccessMessage('Subscription scheduled for cancellation at the end of billing period.');
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch {
      // Error handling would go here
    }
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-fg-muted">Loading billing information...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-md border border-danger/20">
          <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}
      
      {successMessage && (
        <div className="flex items-center space-x-2 text-success bg-success/10 p-3 rounded-md border border-success/20">
          <CheckCircleIcon className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{successMessage}</span>
        </div>
      )}

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CreditCardIcon className="w-5 h-5" />
            <span>Current Plan</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-fg">{currentPlan.name}</h3>
              <p className="text-2xl font-bold text-fg">
                {formatCurrency(currentPlan.price)}
                <span className="text-sm font-normal text-fg-muted">/{currentPlan.period}</span>
              </p>
              <div className="flex items-center space-x-1 text-sm text-fg-muted mt-1">
                <CalendarIcon className="w-4 h-4" />
                <span>Next billing: {new Date(currentPlan.nextBilling).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="text-right">
              <Button
                variant="outline"
                onClick={() => setActiveSection(activeSection === 'plans' ? null : 'plans')}
              >
                {activeSection === 'plans' ? 'Cancel' : 'Change plan'}
              </Button>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-border">
            <h4 className="text-sm font-medium text-fg mb-2">Plan includes:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {currentPlan.features.map((feature, index) => (
                <div key={index} className="flex items-center space-x-2 text-sm text-fg-muted">
                  <CheckCircleIcon className="w-4 h-4 text-success flex-shrink-0" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Plan Selection */}
      {activeSection === 'plans' && (
        <Card>
          <CardHeader>
            <CardTitle>Choose Your Plan</CardTitle>
            <p className="text-sm text-fg-muted">
              Select the plan that best fits your needs.
            </p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
              {plans.map((plan) => {
                const PlanIcon = plan.icon;
                return (
                  <div
                    key={plan.name}
                    className={`relative p-6 rounded-lg border-2 ${
                      plan.isCurrent 
                        ? 'border-accent bg-accent/5' 
                        : plan.badge === 'Best Value'
                        ? 'border-green-500 bg-green-50/50 hover:border-green-400'
                        : plan.badge === 'Most Popular'
                        ? 'border-blue-500 bg-blue-50/50 hover:border-blue-400'
                        : 'border-border bg-surface/50 hover:border-border-hover'
                    } transition-colors ${
                      plan.badge === 'Best Value' ? 'scale-105 shadow-lg' : ''
                    }`}
                  >
                    {plan.isCurrent && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span className="bg-accent text-accent-fg px-3 py-1 rounded-full text-xs font-medium">
                          Current Plan
                        </span>
                      </div>
                    )}
                    
                    {!plan.isCurrent && plan.badge && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          plan.badge === 'Most Popular' 
                            ? 'bg-blue-600 text-white'
                            : plan.badge === 'Best Value'
                            ? 'bg-green-600 text-white' 
                            : plan.badge === 'Contact Sales'
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-600 text-white'
                        }`}>
                          {plan.badge}
                        </span>
                      </div>
                    )}
                    
                    <div className="text-center">
                      <PlanIcon className="w-8 h-8 mx-auto mb-4 text-accent" />
                      <h3 className="text-lg font-semibold text-fg">{plan.name}</h3>
                      <p className="text-sm text-fg-muted mb-4">{plan.description}</p>
                      <div className="mb-6">
                        <span className="text-3xl font-bold text-fg">
                          {plan.price ? formatCurrency(plan.price) : 'Custom'}
                        </span>
                        <span className="text-sm text-fg-muted">
                          {plan.price ? `/${plan.period}` : ` ${plan.period}`}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3 mb-6">
                      {plan.features.map((feature, index) => (
                        <div key={index} className="flex items-start space-x-2 text-sm">
                          <CheckCircleIcon className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                          <span className="text-fg-muted">{feature}</span>
                        </div>
                      ))}
                    </div>
                    
                    <Button
                      className="w-full"
                      variant={plan.isCurrent ? "outline" : "primary"}
                      disabled={plan.isCurrent || isLoading}
                      onClick={() => handlePlanChange(plan.name)}
                    >
                      {plan.isCurrent 
                        ? 'Current Plan' 
                        : plan.price 
                          ? `Upgrade to ${plan.name}` 
                          : 'Contact Sales'
                      }
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUpIcon className="w-5 h-5" />
            <span>Usage Overview</span>
          </CardTitle>
          <p className="text-sm text-fg-muted">
            Current usage for {usageData.period}
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* API Calls */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-fg">API Calls</span>
                <span className="text-sm text-fg-muted">
                  {usageData.apiCalls.toLocaleString()} 
                  {usageData.limit.apiCalls === -1 ? ' / Unlimited' : ` / ${usageData.limit.apiCalls.toLocaleString()}`}
                </span>
              </div>
              <div className="w-full bg-surface rounded-full h-2">
                <div 
                  className="bg-accent h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: usageData.limit.apiCalls === -1 ? '45%' : `${getUsagePercentage(usageData.apiCalls, usageData.limit.apiCalls)}%` 
                  }}
                ></div>
              </div>
            </div>

            {/* Data Processing */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-fg">Data Processing</span>
                <span className="text-sm text-fg-muted">
                  {usageData.dataProcessed}GB / {usageData.limit.dataProcessed}GB
                </span>
              </div>
              <div className="w-full bg-surface rounded-full h-2">
                <div 
                  className="bg-accent h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${getUsagePercentage(usageData.dataProcessed, usageData.limit.dataProcessed)}%` 
                  }}
                ></div>
              </div>
            </div>

            {/* Alerts */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-fg">Alerts</span>
                <span className="text-sm text-fg-muted">
                  {usageData.alerts} / {usageData.limit.alerts.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-surface rounded-full h-2">
                <div 
                  className="bg-accent h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${getUsagePercentage(usageData.alerts, usageData.limit.alerts)}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileTextIcon className="w-5 h-5" />
            <span>Billing History</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {billingHistory.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-3 border-b border-border last:border-b-0">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1">
                    <DollarSignIcon className="w-4 h-4 text-fg-muted" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-fg">{item.description}</p>
                    <p className="text-xs text-fg-muted">{new Date(item.date).toLocaleDateString()}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
                    {formatCurrency(item.amount)}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    item.status === 'paid' ? 'bg-success/10 text-success' :
                    item.status === 'pending' ? 'bg-warning/10 text-warning' :
                    'bg-danger/10 text-danger'
                  }`}>
                    {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                  </span>
                  {item.invoiceUrl && (
                    <Button variant="ghost" size="sm">
                      <DownloadIcon className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-danger">
        <CardHeader>
          <CardTitle className="text-danger">Danger Zone</CardTitle>
          <p className="text-sm text-fg-muted">
            Irreversible and destructive actions.
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-fg">Cancel subscription</h3>
              <p className="text-sm text-fg-muted">
                Your subscription will remain active until the end of the current billing period.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={handleCancelSubscription}
              disabled={isLoading}
              className="text-danger border-danger hover:bg-danger hover:text-white"
            >
              Cancel subscription
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};