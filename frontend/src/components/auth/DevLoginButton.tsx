'use client';

import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/Button';

export const DevLoginButton: React.FC = () => {
  const { signIn, isLoading } = useAuthStore();
  const isDevelopment = process.env.NODE_ENV === 'development';

  if (!isDevelopment) {
    return null;
  }

  const handleDevLogin = async () => {
    try {
      await signIn({
        email: 'admin@ziggyclean.com',
        password: 'admin',
        remember: true
      });
    } catch (error) {
      console.error('Dev login failed:', error);
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="text-sm text-blue-800 mb-2">
        🔧 Development Mode
      </div>
      <Button 
        onClick={handleDevLogin}
        disabled={isLoading}
        className="bg-blue-600 hover:bg-blue-700 text-white"
        size="sm"
      >
        {isLoading ? 'Signing in...' : 'Quick Login (Admin)'}
      </Button>
    </div>
  );
};