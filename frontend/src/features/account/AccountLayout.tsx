'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { 
  UserIcon, 
  ShieldIcon, 
  SmartphoneIcon, 
  CreditCardIcon,
  SettingsIcon 
} from 'lucide-react';

interface AccountLayoutProps {
  children: React.ReactNode;
}

const accountTabs = [
  {
    id: 'profile',
    label: 'Profile',
    href: '/account',
    icon: UserIcon,
    description: 'Manage your personal information',
  },
  {
    id: 'security',
    label: 'Security',
    href: '/account/security',
    icon: ShieldIcon,
    description: 'Password and two-factor authentication',
  },
  {
    id: 'devices',
    label: 'Devices',
    href: '/account/devices',
    icon: SmartphoneIcon,
    description: 'Manage your signed-in devices',
  },
  {
    id: 'billing',
    label: 'Billing',
    href: '/account/billing',
    icon: CreditCardIcon,
    description: 'Subscription and payment methods',
  },
];

export const AccountLayout: React.FC<AccountLayoutProps> = ({ children }) => {
  const pathname = usePathname();

  const getActiveTab = () => {
    if (pathname === '/account') return 'profile';
    if (pathname.startsWith('/account/security')) return 'security';
    if (pathname.startsWith('/account/devices')) return 'devices';
    if (pathname.startsWith('/account/billing')) return 'billing';
    return 'profile';
  };

  const activeTab = getActiveTab();

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <div className="bg-panel border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-4 py-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                <SettingsIcon className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-fg">Account Settings</h1>
                <p className="text-sm text-fg-muted">
                  Manage your account preferences and security settings
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <Card className="p-0 overflow-hidden bg-panel border-border">
              <nav className="space-y-1">
                {accountTabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  
                  return (
                    <Link
                      key={tab.id}
                      href={tab.href}
                      className={`
                        flex items-center space-x-3 px-4 py-3 text-sm font-medium transition-colors
                        hover:bg-surface focus:outline-none focus:ring-2 focus:ring-accent focus:ring-inset
                        ${isActive 
                          ? 'bg-accent text-white border-r-2 border-accent-hover' 
                          : 'text-fg hover:text-fg-hover border-r-2 border-transparent'
                        }
                      `}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-fg-muted'}`} />
                      <div className="flex-1">
                        <div className={`font-medium ${isActive ? 'text-white' : 'text-fg'}`}>
                          {tab.label}
                        </div>
                        <div className={`text-xs ${isActive ? 'text-white/80' : 'text-fg-muted'} hidden sm:block`}>
                          {tab.description}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </nav>
            </Card>
            
            {/* Help Card */}
            <Card className="mt-6 p-4 bg-accent/5 border-accent/20">
              <div className="text-center space-y-2">
                <h3 className="text-sm font-medium text-fg">Need Help?</h3>
                <p className="text-xs text-fg-muted">
                  Visit our support center for guides and assistance
                </p>
                <Link
                  href="/support"
                  className="inline-block text-xs text-accent hover:text-accent-hover transition-colors font-medium"
                >
                  Visit Support →
                </Link>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};