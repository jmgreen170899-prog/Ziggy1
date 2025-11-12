'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { AuthCard } from '@/components/auth/AuthCard';
import { PasswordField } from '@/components/auth/PasswordField';
import { OtpInput } from '@/components/auth/OtpInput';
import { useAuthStore } from '@/store/authStore';
import { AlertCircleIcon, CheckCircleIcon, ShieldCheckIcon } from 'lucide-react';

export default function ResetPassword() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { resetPassword, isLoading, error, clearError } = useAuthStore();
  
  const [formData, setFormData] = useState({
    code: '',
    newPassword: '',
    confirmPassword: '',
  });
  
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState('');
  
  const email = searchParams?.get('email') || '';
  
  useEffect(() => {
    if (!email) {
      router.push('/auth/forgot-password');
      return;
    }
  }, [email, router]);
  
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (formData.code.length !== 6) {
      errors.code = 'Please enter the 6-digit reset code';
    }
    
    if (!formData.newPassword) {
      errors.newPassword = 'Password is required';
    } else if (formData.newPassword.length < 8) {
      errors.newPassword = 'Password must be at least 8 characters long';
    }
    
    if (formData.newPassword !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccessMessage('');
    
    if (!validateForm()) {
      return;
    }
    
    try {
      await resetPassword({
        email,
        code: formData.code,
        newPassword: formData.newPassword,
      });
      
      setSuccessMessage('Password reset successfully! Redirecting to sign in...');
      setTimeout(() => {
        router.push('/auth/signin');
      }, 2000);
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <AuthCard
      title="Reset your password"
      description={`Enter the code sent to ${email} and your new password`}
    >
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-accent/10 rounded-full mb-4">
          <ShieldCheckIcon className="w-8 h-8 text-accent" />
        </div>
        <p className="text-sm text-fg-muted">
          Enter the 6-digit code from your email and choose a new secure password.
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
            <label htmlFor="reset-code" className="block text-sm font-medium text-fg mb-2">
              Reset code <span className="text-danger">*</span>
            </label>
            <OtpInput
              value={formData.code}
              onChange={(value) => setFormData(prev => ({ ...prev, code: value }))}
              autoFocus
              error={!!fieldErrors.code}
              aria-label="Enter 6-digit reset code"
              aria-describedby={fieldErrors.code ? 'code-error' : undefined}
            />
            {fieldErrors.code && (
              <p id="code-error" className="mt-2 text-sm text-danger" role="alert">
                {fieldErrors.code}
              </p>
            )}
          </div>

          <PasswordField
            value={formData.newPassword}
            onChange={(value) => setFormData(prev => ({ ...prev, newPassword: value }))}
            label="New password"
            id="newPassword"
            placeholder="Enter your new password"
            required
            disabled={isLoading}
            showStrengthMeter
            error={fieldErrors.newPassword}
          />

          <PasswordField
            value={formData.confirmPassword}
            onChange={(value) => setFormData(prev => ({ ...prev, confirmPassword: value }))}
            label="Confirm new password"
            id="confirmPassword"
            placeholder="Confirm your new password"
            required
            disabled={isLoading}
            error={fieldErrors.confirmPassword}
          />

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || formData.code.length !== 6 || !formData.newPassword}
          >
            {isLoading ? 'Resetting password...' : 'Reset password'}
          </Button>
        </div>

        <div className="text-center space-y-2">
          <p className="text-sm text-fg-muted">
            Didn&apos;t receive the code?
          </p>
          <Link 
            href="/auth/forgot-password"
            className="text-sm text-accent hover:text-accent-hover transition-colors"
          >
            Request a new code
          </Link>
          
          <div className="pt-2">
            <Link 
              href="/auth/signin"
              className="text-sm text-accent hover:text-accent-hover transition-colors"
            >
              ← Back to sign in
            </Link>
          </div>
        </div>
      </form>
    </AuthCard>
  );
}