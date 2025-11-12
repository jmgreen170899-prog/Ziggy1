'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

interface RequireAuthProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
  roles?: ('user' | 'admin')[];
}

export const RequireAuth: React.FC<RequireAuthProps> = ({
  children,
  fallback,
  redirectTo,
  roles,
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, isLoading, checkSession } = useAuthStore();
  const [hydrated, setHydrated] = useState(false);

  // Check if we're in development mode and should bypass auth
  const isDevelopment = process.env.NODE_ENV === 'development';
  const bypassAuth = isDevelopment && process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';

  useEffect(() => {
    // Hydrate from storage and check session on mount
    const hydrateAndCheck = async () => {
      if (!bypassAuth) {
        await checkSession();
      }
      setHydrated(true);
    };
    hydrateAndCheck();
  }, [checkSession, bypassAuth]);

  useEffect(() => {
    if (!bypassAuth && hydrated && !isLoading && !isAuthenticated) {
      const currentPath = pathname;
      const signInUrl = redirectTo || '/auth/signin';
      
      // Preserve the original route for post-login redirect
      const redirectUrl = currentPath !== '/auth/signin' && currentPath !== '/' 
        ? `${signInUrl}?next=${encodeURIComponent(currentPath)}` 
        : signInUrl;
      
      router.push(redirectUrl);
    }
  }, [isAuthenticated, isLoading, hydrated, router, pathname, redirectTo, bypassAuth]);

  // Show loading state while hydrating or checking authentication
  if (!hydrated || (!bypassAuth && isLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto"></div>
          <p className="text-sm text-fg-muted">Loading...</p>
        </div>
      </div>
    );
  }

  // If bypassing auth in dev mode, show app with a banner
  if (bypassAuth) {
    return (
      <>
        <div className="bg-yellow-500 text-black px-4 py-2 text-center text-sm font-medium">
          🚧 Development Mode: Authentication bypassed
        </div>
        {children}
      </>
    );
  }

  // If not authenticated, show fallback or redirect
  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : null;
  }

  // Check role-based access
  if (roles && user && !roles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg p-4">
        <div className="text-center space-y-4 max-w-md">
          <div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center mx-auto">
            <span className="text-2xl">🚫</span>
          </div>
          <h1 className="text-xl font-semibold text-fg">Access Denied</h1>
          <p className="text-fg-muted">
            You don&apos;t have permission to access this page.
          </p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // User is authenticated and has required role
  return <>{children}</>;
};

// Higher-order component version
export const withAuth = <P extends object>(
  Component: React.ComponentType<P>,
  options?: {
    fallback?: React.ReactNode;
    redirectTo?: string;
    roles?: ('user' | 'admin')[];
  }
) => {
  const AuthenticatedComponent = (props: P) => {
    return (
      <RequireAuth {...options}>
        <Component {...props} />
      </RequireAuth>
    );
  };

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name})`;
  return AuthenticatedComponent;
};

// Hook for checking authentication status
export const useRequireAuth = (options?: {
  redirectTo?: string;
  roles?: ('user' | 'admin')[];
}) => {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, isLoading, checkSession } = useAuthStore();

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const currentPath = pathname;
      const signInUrl = options?.redirectTo || '/auth/signin';
      const redirectUrl = currentPath !== '/' ? `${signInUrl}?next=${encodeURIComponent(currentPath)}` : signInUrl;
      router.push(redirectUrl);
    }
  }, [isAuthenticated, isLoading, router, pathname, options?.redirectTo]);

  const hasRequiredRole = !options?.roles || (user && options.roles.includes(user.role));

  return {
    isAuthenticated,
    user,
    isLoading,
    hasRequiredRole,
  };
};