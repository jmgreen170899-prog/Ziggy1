'use client';

import { ReactNode } from 'react';
import { useAuthStore } from '@/store/authStore';
import { LoadingState } from '@/components/ui/Loading';

interface AdminGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * AdminGuard component protects routes/content for admin users only.
 * Shows loading state while checking authentication, then either shows
 * content (for admin users) or fallback component (for non-admin users).
 */
export function AdminGuard({ children, fallback }: AdminGuardProps) {
  const { user, isLoading, isAuthenticated } = useAuthStore();

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingState />
      </div>
    );
  }

  // Not authenticated - show access denied
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-6xl">🔒</div>
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="text-gray-600">Authentication required</p>
        </div>
      </div>
    );
  }

  // Check if user has admin role
  if (user.role !== 'admin') {
    return fallback || (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-6xl">⚠️</div>
          <h1 className="text-2xl font-bold text-orange-600">Admin Access Required</h1>
          <p className="text-gray-600">
            This section requires administrator privileges.
          </p>
          <p className="text-sm text-gray-500">
            Contact your system administrator for access.
          </p>
        </div>
      </div>
    );
  }

  // User is admin - show protected content
  return <>{children}</>;
}

/**
 * Hook to check if current user is admin
 */
export function useIsAdmin(): boolean {
  const { user, isAuthenticated } = useAuthStore();
  return isAuthenticated && user?.role === 'admin';
}