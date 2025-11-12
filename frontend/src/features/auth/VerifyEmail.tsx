'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { AuthCard } from '@/components/auth/AuthCard';
import { OtpInput } from '@/components/auth/OtpInput';
import { useAuthStore } from '@/store/authStore';
import { AlertCircleIcon, CheckCircleIcon, MailIcon } from 'lucide-react';

export default function VerifyEmail() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyEmail, isLoading, error, clearError } = useAuthStore();
  
  const [verificationCode, setVerificationCode] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [canResend, setCanResend] = useState(false);
  const [resendTimer, setResendTimer] = useState(60);
  
  const email = searchParams?.get('email') || '';
  
  useEffect(() => {
    if (!email) {
      router.push('/auth/sign-up');
      return;
    }
    
    // Start resend timer
    const timer = setInterval(() => {
      setResendTimer(prev => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [email, router]);
  
  useEffect(() => {
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
    
    if (verificationCode.length !== 6) {
      return;
    }
    
    try {
      await verifyEmail(email, verificationCode);
      setSuccessMessage('Email verified successfully! Redirecting to dashboard...');
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } catch {
      // Error is handled by the store
    }
  };
  
  const handleResendCode = async () => {
    if (!canResend) return;
    
    setCanResend(false);
    setResendTimer(60);
    clearError();
    
    // In a real app, you'd call a resend verification email endpoint
    // For now, we'll just simulate it
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccessMessage('Verification code sent! Please check your email.');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      setCanResend(true);
      setResendTimer(0);
    }
  };

  return (
    <AuthCard
      title="Verify your email"
      description={`We've sent a verification code to ${email}`}
    >
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-accent/10 rounded-full mb-4">
          <MailIcon className="w-8 h-8 text-accent" />
        </div>
        <p className="text-sm text-fg-muted">
          Enter the 6-digit code we sent to your email address to complete your account setup.
        </p>
      </div>

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
            <label htmlFor="verification-code" className="block text-sm font-medium text-fg mb-2">
              Verification code
            </label>
            <OtpInput
              value={verificationCode}
              onChange={setVerificationCode}
              autoFocus
              error={!!error}
              aria-label="Enter 6-digit verification code"
              aria-describedby={error ? 'verify-error' : undefined}
            />
            {error && (
              <p id="verify-error" className="mt-2 text-sm text-danger" role="alert">
                Please check your code and try again
              </p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || verificationCode.length !== 6}
          >
            {isLoading ? 'Verifying...' : 'Verify email'}
          </Button>
        </div>

        <div className="text-center space-y-3">
          <p className="text-sm text-fg-muted">
            Didn&apos;t receive the code?
          </p>
          
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleResendCode}
            disabled={!canResend || isLoading}
            className="text-accent hover:text-accent-hover"
          >
            {canResend 
              ? 'Resend code' 
              : `Resend code in ${resendTimer}s`
            }
          </Button>
          
          <div className="pt-2">
            <Link 
              href="/auth/sign-up"
              className="text-sm text-accent hover:text-accent-hover transition-colors"
            >
              ← Back to sign up
            </Link>
          </div>
        </div>
      </form>
    </AuthCard>
  );
}