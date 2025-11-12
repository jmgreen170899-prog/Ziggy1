'use client';

import React, { useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { LoadingState } from '@/components/ui/Loading';

interface AuthGuardProps {
  children: ReactNode;
}

const PUBLIC_ROUTES = [
  '/auth/signin',
  '/auth/signup', 
  '/auth/forgot-password',
  '/auth/verify',
];

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, checkSession } = useAuthStore();

  // Check if current route is public
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));

  useEffect(() => {
    // Check session on mount
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    // Redirect logic after auth state is determined
    if (!isLoading) {
      if (!isAuthenticated && !isPublicRoute) {
        // User not authenticated and trying to access protected route
        router.push('/auth/signin');
      } else if (isAuthenticated && isPublicRoute) {
        // User authenticated but on auth page, redirect to dashboard
        router.push('/');
      }
    }
  }, [isAuthenticated, isLoading, isPublicRoute, router, pathname]);

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingState />
      </div>
    );
  }

  // For public routes, always show content
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // For protected routes, only show if authenticated
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // Should not reach here due to redirect, but just in case
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <LoadingState />
    </div>
  );
}