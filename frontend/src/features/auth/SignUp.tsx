'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { AuthCard } from '@/components/auth/AuthCard';
import { PasswordField } from '@/components/auth/PasswordField';
import { useAuthStore } from '@/store/authStore';
import { AlertCircleIcon, CheckCircleIcon } from 'lucide-react';

export default function SignUp() {
  const router = useRouter();
  const { signUp, isLoading, error, clearError } = useAuthStore();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });
  
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState('');
  
  React.useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }
    
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters long';
    }
    
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
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
      const result = await signUp({
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      });
      
      if (result.needEmailVerify) {
        setSuccessMessage('Account created! Please check your email for verification instructions.');
        setTimeout(() => {
          router.push(`/auth/verify-email?email=${encodeURIComponent(formData.email)}`);
        }, 2000);
      }
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <AuthCard
      title="Create your account"
      description="Get started with ZiggyAI today"
    >
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
            <label htmlFor="name" className="text-sm font-medium text-fg">
              Full name <span className="text-danger">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Enter your full name"
              required
              disabled={isLoading}
              aria-describedby={fieldErrors.name ? 'name-error' : undefined}
              aria-invalid={fieldErrors.name ? 'true' : 'false'}
              className={`mt-1 w-full px-3 py-2 text-sm bg-surface border rounded-md placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50 ${
                fieldErrors.name ? 'border-danger focus:ring-danger' : 'border-border hover:border-border-hover'
              }`}
            />
            {fieldErrors.name && (
              <p id="name-error" className="mt-1 text-sm text-danger" role="alert">
                {fieldErrors.name}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="text-sm font-medium text-fg">
              Email address <span className="text-danger">*</span>
            </label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="Enter your email"
              required
              disabled={isLoading}
              aria-describedby={fieldErrors.email ? 'email-error' : undefined}
              aria-invalid={fieldErrors.email ? 'true' : 'false'}
              className={`mt-1 w-full px-3 py-2 text-sm bg-surface border rounded-md placeholder:text-fg-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50 ${
                fieldErrors.email ? 'border-danger focus:ring-danger' : 'border-border hover:border-border-hover'
              }`}
            />
            {fieldErrors.email && (
              <p id="email-error" className="mt-1 text-sm text-danger" role="alert">
                {fieldErrors.email}
              </p>
            )}
          </div>

          <PasswordField
            value={formData.password}
            onChange={(value) => setFormData(prev => ({ ...prev, password: value }))}
            label="Password"
            id="password"
            placeholder="Create a strong password"
            required
            disabled={isLoading}
            showStrengthMeter
            error={fieldErrors.password}
          />

          <PasswordField
            value={formData.confirmPassword}
            onChange={(value) => setFormData(prev => ({ ...prev, confirmPassword: value }))}
            label="Confirm password"
            id="confirmPassword"
            placeholder="Confirm your password"
            required
            disabled={isLoading}
            error={fieldErrors.confirmPassword}
          />

          <div className="space-y-2">
            <label className="flex items-start space-x-2 text-sm">
              <input
                type="checkbox"
                checked={formData.acceptTerms}
                onChange={(e) => setFormData(prev => ({ ...prev, acceptTerms: e.target.checked }))}
                disabled={isLoading}
                aria-describedby={fieldErrors.acceptTerms ? 'terms-error' : undefined}
                aria-invalid={fieldErrors.acceptTerms ? 'true' : 'false'}
                className={`mt-0.5 rounded border text-accent focus:ring-accent focus:ring-offset-0 ${
                  fieldErrors.acceptTerms ? 'border-danger' : 'border-border'
                }`}
              />
              <span className="text-fg">
                I agree to the{' '}
                <Link href="/terms" className="text-accent hover:text-accent-hover">
                  Terms of Service
                </Link>
                {' '}and{' '}
                <Link href="/privacy" className="text-accent hover:text-accent-hover">
                  Privacy Policy
                </Link>
                <span className="text-danger ml-1">*</span>
              </span>
            </label>
            {fieldErrors.acceptTerms && (
              <p id="terms-error" className="text-sm text-danger" role="alert">
                {fieldErrors.acceptTerms}
              </p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </Button>
        </div>

        <div className="text-center">
          <span className="text-sm text-fg-muted">
            Already have an account?{' '}
            <Link 
              href="/auth/signin"
              className="text-accent hover:text-accent-hover transition-colors font-medium"
            >
              Sign in
            </Link>
          </span>
        </div>
      </form>
    </AuthCard>
  );
}