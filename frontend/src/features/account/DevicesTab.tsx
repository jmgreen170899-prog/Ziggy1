'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { 
  MonitorIcon, 
  SmartphoneIcon, 
  TabletIcon,
  MapPinIcon,
  CalendarIcon,
  LogOutIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  WifiIcon,
  GlobeIcon
} from 'lucide-react';

interface DeviceSession {
  id: string;
  deviceType: 'desktop' | 'mobile' | 'tablet';
  deviceName: string;
  browser: string;
  os: string;
  location: string;
  ipAddress: string;
  lastActive: string;
  isCurrent: boolean;
  isActive: boolean;
}

export const DevicesTab: React.FC = () => {
  const { user, isLoading, error, clearError } = useAuthStore();
  
  const [successMessage, setSuccessMessage] = useState('');
  
  // Example device sessions data
  const [sessions] = useState<DeviceSession[]>([
    {
      id: '1',
      deviceType: 'desktop',
      deviceName: 'Windows PC',
      browser: 'Chrome 120.0',
      os: 'Windows 11',
      location: 'New York, NY',
      ipAddress: '192.168.1.100',
      lastActive: new Date().toISOString(),
      isCurrent: true,
      isActive: true,
    },
    {
      id: '2',
      deviceType: 'mobile',
      deviceName: 'iPhone 15 Pro',
      browser: 'Safari 17.1',
      os: 'iOS 17.2',
      location: 'New York, NY',
      ipAddress: '192.168.1.101',
      lastActive: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      isCurrent: false,
      isActive: true,
    },
    {
      id: '3',
      deviceType: 'tablet',
      deviceName: 'iPad Air',
      browser: 'Safari 17.0',
      os: 'iPadOS 17.1',
      location: 'Brooklyn, NY',
      ipAddress: '10.0.0.50',
      lastActive: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
      isCurrent: false,
      isActive: false,
    },
    {
      id: '4',
      deviceType: 'desktop',
      deviceName: 'MacBook Pro',
      browser: 'Chrome 119.5',
      os: 'macOS Sonoma',
      location: 'San Francisco, CA',
      ipAddress: '203.0.113.42',
      lastActive: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week ago
      isCurrent: false,
      isActive: false,
    },
  ]);

  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType) {
      case 'mobile':
        return SmartphoneIcon;
      case 'tablet':
        return TabletIcon;
      default:
        return MonitorIcon;
    }
  };

  const formatLastActive = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      return 'Just now';
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    clearError();
    setSuccessMessage('');
    
    try {
  // Simulated session revocation
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log('Revoking session:', sessionId);
      setSuccessMessage('Device session revoked successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error handling would go here
    }
  };

  const handleRevokeAllSessions = async () => {
    clearError();
    setSuccessMessage('');
    
    try {
  // Simulated revocation of all sessions except current
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccessMessage('All other sessions have been revoked!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error handling would go here
    }
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-fg-muted">Loading device sessions...</p>
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

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Sessions</CardTitle>
              <p className="text-sm text-fg-muted">
                Manage where you&apos;re signed in to ZiggyAI.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={handleRevokeAllSessions}
              disabled={isLoading}
              className="text-danger hover:text-danger"
            >
              <LogOutIcon className="w-4 h-4 mr-2" />
              Revoke all others
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.map((session) => {
              const DeviceIcon = getDeviceIcon(session.deviceType);
              
              return (
                <div
                  key={session.id}
                  className={`flex items-start justify-between p-4 rounded-lg border ${
                    session.isCurrent 
                      ? 'border-accent bg-accent/5' 
                      : 'border-border bg-surface/50'
                  }`}
                >
                  <div className="flex items-start space-x-4">
                    <div className={`p-2 rounded-md ${
                      session.isActive ? 'bg-success/10 text-success' : 'bg-fg-muted/10 text-fg-muted'
                    }`}>
                      <DeviceIcon className="w-5 h-5" />
                    </div>
                    
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-medium text-fg">
                          {session.deviceName}
                        </h3>
                        {session.isCurrent && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-accent text-accent-fg">
                            Current device
                          </span>
                        )}
                        {session.isActive && !session.isCurrent && (
                          <div className="flex items-center space-x-1 text-success">
                            <WifiIcon className="w-3 h-3" />
                            <span className="text-xs">Active</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="space-y-1 text-xs text-fg-muted">
                        <div className="flex items-center space-x-1">
                          <GlobeIcon className="w-3 h-3" />
                          <span>{session.browser} • {session.os}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <MapPinIcon className="w-3 h-3" />
                          <span>{session.location} • {session.ipAddress}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <CalendarIcon className="w-3 h-3" />
                          <span>Last active {formatLastActive(session.lastActive)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {!session.isCurrent && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRevokeSession(session.id)}
                      disabled={isLoading}
                      className="text-danger hover:text-danger hover:bg-danger/10"
                    >
                      <LogOutIcon className="w-4 h-4 mr-1" />
                      Revoke
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Security Settings</CardTitle>
          <p className="text-sm text-fg-muted">
            Configure session and device security options.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-fg">Session timeout</h3>
                <p className="text-sm text-fg-muted">
                  Automatically sign out inactive sessions
                </p>
              </div>
              <select className="px-3 py-2 text-sm bg-surface border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent">
                <option value="24h">24 hours</option>
                <option value="7d">7 days</option>
                <option value="30d">30 days</option>
                <option value="never">Never</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-fg">Email notifications</h3>
                <p className="text-sm text-fg-muted">
                  Get notified of new sign-ins from unrecognized devices
                </p>
              </div>
              <button
                type="button"
                className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-accent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                role="switch"
                aria-checked="true"
              >
                <span className="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out translate-x-5"></span>
              </button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-fg">Location tracking</h3>
                <p className="text-sm text-fg-muted">
                  Store approximate location data for security monitoring
                </p>
              </div>
              <button
                type="button"
                className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-accent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                role="switch"
                aria-checked="true"
              >
                <span className="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out translate-x-5"></span>
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Device Information */}
      <Card>
        <CardHeader>
          <CardTitle>Current Device Information</CardTitle>
          <p className="text-sm text-fg-muted">
            Information about this device and browser session.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-fg mb-1">Browser</h4>
              <p className="text-fg-muted">Chrome 120.0.6099.129</p>
            </div>
            <div>
              <h4 className="font-medium text-fg mb-1">Operating System</h4>
              <p className="text-fg-muted">Windows 11</p>
            </div>
            <div>
              <h4 className="font-medium text-fg mb-1">Screen Resolution</h4>
              <p className="text-fg-muted">1920 × 1080</p>
            </div>
            <div>
              <h4 className="font-medium text-fg mb-1">Time Zone</h4>
              <p className="text-fg-muted">Eastern Standard Time (EST)</p>
            </div>
            <div>
              <h4 className="font-medium text-fg mb-1">Language</h4>
              <p className="text-fg-muted">English (United States)</p>
            </div>
            <div>
              <h4 className="font-medium text-fg mb-1">Session Started</h4>
              <p className="text-fg-muted">{new Date().toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};