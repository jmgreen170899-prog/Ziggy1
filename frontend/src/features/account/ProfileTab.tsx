'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { UserIcon, UploadIcon, CheckCircleIcon, AlertCircleIcon } from 'lucide-react';

export const ProfileTab: React.FC = () => {
  const { user, updateProfile, isLoading, error, clearError } = useAuthStore();
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    avatarUrl: user?.avatarUrl || '',
    timezone: user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  
  const [isDirty, setIsDirty] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  
  React.useEffect(() => {
    if (user) {
      setFormData({
        name: user.name,
        avatarUrl: user.avatarUrl || '',
        timezone: user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
    }
  }, [user]);
  
  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
    clearError();
    setSuccessMessage('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccessMessage('');
    
    if (!formData.name.trim()) {
      return;
    }
    
    try {
      await updateProfile({
        name: formData.name.trim(),
        avatarUrl: formData.avatarUrl,
        timezone: formData.timezone,
      });
      
      setIsDirty(false);
      setSuccessMessage('Profile updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      // Error is handled by the store
    }
  };

  const handleCancel = () => {
    if (user) {
      setFormData({
        name: user.name,
        avatarUrl: user.avatarUrl || '',
        timezone: user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
    }
    setIsDirty(false);
    clearError();
    setSuccessMessage('');
  };

  const handleAvatarUpload = () => {
    // Example avatar upload - in a real app, this would open a file picker
    const avatarExamples = [
      'https://api.dicebear.com/7.x/avataaars/svg?seed=1',
      'https://api.dicebear.com/7.x/avataaars/svg?seed=2',
      'https://api.dicebear.com/7.x/avataaars/svg?seed=3',
      'https://api.dicebear.com/7.x/avataaars/svg?seed=4',
    ];
    
  const randomAvatar = avatarExamples[Math.floor(Math.random() * avatarExamples.length)];
    handleInputChange('avatarUrl', randomAvatar);
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-fg-muted">Loading profile...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <p className="text-sm text-fg-muted">
            Update your personal information and preferences.
          </p>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-md border border-danger/20 mb-4">
              <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}
          
          {successMessage && (
            <div className="flex items-center space-x-2 text-success bg-success/10 p-3 rounded-md border border-success/20 mb-4">
              <CheckCircleIcon className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Avatar Section */}
            <div className="flex items-center space-x-6">
              <div className="relative">
                {formData.avatarUrl ? (
                  <Image
                    src={formData.avatarUrl}
                    alt="Profile avatar"
                    width={80}
                    height={80}
                    className="w-20 h-20 rounded-full object-cover border-2 border-border"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-surface border-2 border-border flex items-center justify-center">
                    <UserIcon className="w-8 h-8 text-fg-muted" />
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-fg">Profile Picture</h3>
                <div className="flex space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleAvatarUpload}
                    disabled={isLoading}
                  >
                    <UploadIcon className="w-4 h-4 mr-2" />
                    Upload
                  </Button>
                  {formData.avatarUrl && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleInputChange('avatarUrl', '')}
                      disabled={isLoading}
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <p className="text-xs text-fg-muted">
                  Recommended: Square image, at least 200x200px
                </p>
              </div>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-fg mb-2">
                  Full name <span className="text-danger">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Enter your full name"
                  required
                  disabled={isLoading}
                  className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-md placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent hover:border-border-hover disabled:opacity-50"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-fg mb-2">
                  Email address
                </label>
                <input
                  type="email"
                  id="email"
                  value={user.email}
                  disabled
                  className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-md text-fg-muted cursor-not-allowed opacity-50"
                />
                <p className="text-xs text-fg-muted mt-1">
                  Contact support to change your email address
                </p>
              </div>

              <div className="md:col-span-2">
                <label htmlFor="timezone" className="block text-sm font-medium text-fg mb-2">
                  Timezone
                </label>
                <select
                  id="timezone"
                  value={formData.timezone}
                  onChange={(e) => handleInputChange('timezone', e.target.value)}
                  disabled={isLoading}
                  className="w-full px-3 py-2 text-sm bg-surface border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent hover:border-border-hover disabled:opacity-50"
                >
                  <option value="America/New_York">Eastern Time (ET)</option>
                  <option value="America/Chicago">Central Time (CT)</option>
                  <option value="America/Denver">Mountain Time (PT)</option>
                  <option value="America/Los_Angeles">Pacific Time (PT)</option>
                  <option value="Europe/London">London (GMT)</option>
                  <option value="Europe/Paris">Paris (CET)</option>
                  <option value="Asia/Tokyo">Tokyo (JST)</option>
                  <option value="Asia/Shanghai">Shanghai (CST)</option>
                  <option value="Australia/Sydney">Sydney (AEDT)</option>
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-border">
              <div className="text-sm text-fg-muted">
                Member since {new Date(user.createdAt).toLocaleDateString()}
              </div>
              
              <div className="flex space-x-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleCancel}
                  disabled={isLoading || !isDirty}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading || !isDirty || !formData.name.trim()}
                >
                  {isLoading ? 'Saving...' : 'Save changes'}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Account Status */}
      <Card>
        <CardHeader>
          <CardTitle>Account Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${user.emailVerified ? 'bg-success' : 'bg-warning'}`} />
                <span className="text-sm font-medium text-fg">Email verification</span>
              </div>
              <span className={`text-sm ${user.emailVerified ? 'text-success' : 'text-warning'}`}>
                {user.emailVerified ? 'Verified' : 'Pending'}
              </span>
            </div>
            
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${user.totpEnabled ? 'bg-success' : 'bg-fg-muted'}`} />
                <span className="text-sm font-medium text-fg">Two-factor authentication</span>
              </div>
              <span className={`text-sm ${user.totpEnabled ? 'text-success' : 'text-fg-muted'}`}>
                {user.totpEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 rounded-full bg-success" />
                <span className="text-sm font-medium text-fg">Account type</span>
              </div>
              <span className="text-sm text-fg capitalize">
                {user.role}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};