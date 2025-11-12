'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { AuthCard } from '@/components/auth/AuthCard';
import { PasswordField } from '@/components/auth/PasswordField';
import { OtpInput } from '@/components/auth/OtpInput';
import { DevLoginButton } from '@/components/auth/DevLoginButton';
import { useAuthStore } from '@/store/authStore';
import { AlertCircleIcon, CheckCircleIcon } from 'lucide-react';

export default function SignIn() {
  const router = useRouter();
  const { signIn, isLoading, error, clearError, requireTotp } = useAuthStore();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember: false,
    totpCode: '',
  });
  
  const [showTotp, setShowTotp] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  
  React.useEffect(() => {
    setShowTotp(requireTotp);
  }, [requireTotp]);
  
  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccessMessage('');
    
    try {
      await signIn({
        email: formData.email,
        password: formData.password,
        remember: formData.remember,
        totpCode: showTotp ? formData.totpCode : undefined,
      });
      
      if (!requireTotp) {
        setSuccessMessage('Successfully signed in!');
        const searchParams = new URLSearchParams(window.location.search);
        const next = searchParams.get('next') || '/';
        setTimeout(() => {
          router.push(next);
        }, 1000);
      }
    } catch {
      // Error is handled by the store
    }
  };
  
  const handleTotpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(e);
  };

  if (showTotp) {
    return (
      <AuthCard
        title="Two-Factor Authentication"
        description="Enter the 6-digit code from your authenticator app"
      >
        <form onSubmit={handleTotpSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-md border border-danger/20">
              <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}
          
          <div className="space-y-4">
            <OtpInput
              value={formData.totpCode}
              onChange={(value) => setFormData(prev => ({ ...prev, totpCode: value }))}
              autoFocus
              error={!!error}
              aria-describedby={error ? 'totp-error' : undefined}
            />
            
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || formData.totpCode.length !== 6}
            >
              {isLoading ? 'Verifying...' : 'Verify'}
            </Button>
          </div>
          
          <div className="text-center">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowTotp(false);
                setFormData(prev => ({ ...prev, totpCode: '' }));
                clearError();
              }}
            >
              ← Back to sign in
            </Button>
          </div>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Welcome back"
      description="Sign in to your ZiggyAI account"
    >
      <DevLoginButton />
      
      <form onSubmit={handleSubmit} className="space-y-6">
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

        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="text-sm font-medium text-fg">
              Email or Username <span className="text-danger">*</span>
            </label>
            <input
              type="text"
              id="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="Enter your email or username"
              required
              disabled={isLoading}
              className="mt-1 w-full px-3 py-2 text-sm bg-surface border border-border rounded-md placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
            />
          </div>

          <PasswordField
            value={formData.password}
            onChange={(value) => setFormData(prev => ({ ...prev, password: value }))}
            label="Password"
            id="password"
            placeholder="Enter your password"
            required
            disabled={isLoading}
          />

          <div className="flex items-center justify-between">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={formData.remember}
                onChange={(e) => setFormData(prev => ({ ...prev, remember: e.target.checked }))}
                disabled={isLoading}
                className="rounded border-border text-accent focus:ring-accent focus:ring-offset-0"
              />
              <span className="text-fg">Remember me</span>
            </label>
            
            <Link 
              href="/auth/forgot-password"
              className="text-sm text-accent hover:text-accent-hover transition-colors"
            >
              Forgot password?
            </Link>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !formData.email || !formData.password}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </div>

        <div className="text-center">
          <span className="text-sm text-fg-muted">
            Don&apos;t have an account?{' '}
            <Link 
              href="/auth/sign-up"
              className="text-accent hover:text-accent-hover transition-colors font-medium"
            >
              Sign up
            </Link>
          </span>
        </div>
      </form>
      
      {/* Developer Info Panel */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
          <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
            🚀 Development Access
          </h3>
          <p className="text-xs text-blue-700 dark:text-blue-300 mb-2">
            Use the admin credentials to access the ZiggyClean platform:
          </p>
          <div className="space-y-1 text-xs font-mono bg-blue-100 dark:bg-blue-900/40 p-2 rounded border">
            <div><strong>Email:</strong> admin</div>
            <div><strong>Password:</strong> admin</div>
          </div>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
            This panel only appears in development mode.
          </p>
        </div>
      )}
    </AuthCard>
  );
}