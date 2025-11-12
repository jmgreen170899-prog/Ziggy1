'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { AuthCard } from '@/components/auth/AuthCard';
import { useAuthStore } from '@/store/authStore';
import { AlertCircleIcon, CheckCircleIcon, KeyIcon } from 'lucide-react';

export default function ForgotPassword() {
  const router = useRouter();
  const { requestPasswordReset, isLoading, error, clearError } = useAuthStore();
  
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  
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
    
    if (!email.trim()) {
      return;
    }
    
    try {
      await requestPasswordReset({ email: email.trim().toLowerCase() });
      setIsSubmitted(true);
    } catch {
      // Error is handled by the store
    }
  };

  if (isSubmitted) {
    return (
      <AuthCard
        title="Check your email"
        description="If an account with that email exists, we've sent password reset instructions"
      >
        <div className="text-center space-y-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-success/10 rounded-full">
            <CheckCircleIcon className="w-8 h-8 text-success" />
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-fg">
              We&apos;ve sent password reset instructions to:
            </p>
            <p className="text-sm font-medium text-fg">
              {email}
            </p>
          </div>
          
          <div className="space-y-2 text-sm text-fg-muted">
            <p>Please check your email and follow the instructions to reset your password.</p>
            <p>The reset link will expire in 10 minutes for security.</p>
          </div>
          
          <div className="space-y-3">
            <Button
              onClick={() => {
                router.push(`/auth/reset-password?email=${encodeURIComponent(email)}`);
              }}
              className="w-full"
            >
              I have the reset code
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setIsSubmitted(false);
                setEmail('');
                clearError();
              }}
              className="w-full"
            >
              Try a different email
            </Button>
          </div>
          
          <div className="text-center pt-2">
            <Link 
              href="/auth/signin"
              className="text-sm text-accent hover:text-accent-hover transition-colors"
            >
              ← Back to sign in
            </Link>
          </div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Reset your password"
      description="Enter your email address and we'll send you a reset code"
    >
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-accent/10 rounded-full mb-4">
          <KeyIcon className="w-8 h-8 text-accent" />
        </div>
        <p className="text-sm text-fg-muted">
          Don&apos;t worry, it happens to the best of us. Enter your email address below and we&apos;ll send you a code to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="flex items-center space-x-2 text-danger bg-danger/10 p-3 rounded-md border border-danger/20">
            <AlertCircleIcon className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div>
          <label htmlFor="email" className="text-sm font-medium text-fg">
            Email address <span className="text-danger">*</span>
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            required
            disabled={isLoading}
            autoFocus
            className="mt-1 w-full px-3 py-2 text-sm bg-surface border border-border rounded-md placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent hover:border-border-hover disabled:opacity-50"
          />
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={isLoading || !email.trim()}
        >
          {isLoading ? 'Sending reset code...' : 'Send reset code'}
        </Button>

        <div className="text-center space-y-2">
          <p className="text-sm text-fg-muted">
            Remember your password?
          </p>
          <Link 
            href="/auth/signin"
            className="text-sm text-accent hover:text-accent-hover transition-colors font-medium"
          >
            ← Back to sign in
          </Link>
        </div>
      </form>
    </AuthCard>
  );
}