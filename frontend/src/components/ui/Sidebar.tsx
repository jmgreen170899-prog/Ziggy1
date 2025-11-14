'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/store';
import { useAuthStore } from '@/store/authStore';
import { AccountMenu } from '@/components/ui/AccountMenu';
import { BackendStatusBanner } from '@/components/ui/BackendStatusBanner';
import { WsStatusPill } from '@/components/ui/WsStatusPill';
import { useResponsiveSidebar } from '@/hooks/useResponsiveSidebar';
import { cn } from '@/utils';

interface SidebarProps {
  children: React.ReactNode;
}

export function Sidebar({ children }: SidebarProps) {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useAppStore();
  const { user, isAuthenticated } = useAuthStore();
  const { isLargeScreen } = useResponsiveSidebar();
  const toggleBtnRef = React.useRef<HTMLButtonElement | null>(null);
  const firstLinkRef = React.useRef<HTMLAnchorElement | null>(null);
  const sidebarRef = React.useRef<HTMLDivElement | null>(null);

  // Check if user is admin
  const isAdmin = isAuthenticated && user?.role === 'admin';

  // Build navigation items based on user role
  const allNavigation = [
    { name: 'Dashboard', href: '/', icon: '📊' },
    { name: 'Market', href: '/market', icon: '📈' },
    { name: 'Live Data', href: '/live', icon: '⚡' },
    { name: 'Trading', href: '/trading', icon: '💼' },
    { name: 'Predictions', href: '/predictions', icon: '🤖' },
    { name: 'Portfolio', href: '/portfolio', icon: '💰' },
    { name: 'News', href: '/news', icon: '📰' },
    { name: 'Crypto', href: '/crypto', icon: '₿' },
    { name: 'Alerts', href: '/alerts', icon: '🔔' },
    { name: 'Learning', href: '/learning', icon: '🧠' },
    { name: 'ZiggyAI Chat', href: '/chat', icon: '💬' },
    { name: 'Help & Glossary', href: '/help', icon: '❓' },
    // Admin-only items
    ...(isAdmin ? [
      { name: 'Paper Trading', href: '/paper-trading', icon: '🤖' }
    ] : [])
  ];

  React.useEffect(() => {
    // Move focus when opening/closing on mobile to improve accessibility
    if (sidebarOpen && !isLargeScreen) {
      // focus first link
      firstLinkRef.current?.focus();
    } else if (!sidebarOpen && !isLargeScreen) {
      // return focus to toggle button
      toggleBtnRef.current?.focus();
    }
  }, [sidebarOpen, isLargeScreen]);

  React.useEffect(() => {
    // Minimal focus trap for mobile sidebar when open
    if (!sidebarOpen || isLargeScreen) return;
    const container = sidebarRef.current;
    if (!container) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const focusables = container.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey) {
        if (active === first || !container.contains(active)) {
          last.focus();
          e.preventDefault();
        }
      } else {
        if (active === last) {
          first.focus();
          e.preventDefault();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen, isLargeScreen]);

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "bg-gradient-to-b from-primary-deep-blue to-slate-900 shadow-2xl transition-all duration-300 ease-in-out border-r border-primary-tech-blue/30",
          "fixed lg:static inset-y-0 left-0 z-50 lg:z-auto",
          sidebarOpen 
            ? "w-64 translate-x-0" 
            : "w-64 -translate-x-full lg:translate-x-0 lg:w-16"
        )}
        role="dialog"
        aria-modal={(!isLargeScreen && sidebarOpen) ? true : undefined}
        aria-label="Primary navigation"
        ref={sidebarRef}
      >
        <div className="flex h-full flex-col">
          {/* Enhanced Logo */}
          <div className="flex h-14 sm:h-16 items-center justify-between px-4 border-b border-primary-tech-blue/30 bg-gradient-to-r from-primary-tech-blue to-ai-purple">
            {(sidebarOpen || isLargeScreen) ? (
              <h1 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-white to-secondary-cyan bg-clip-text text-transparent">
                ZiggyAI
              </h1>
            ) : (
              <div className="text-lg sm:text-xl font-bold text-white bg-white/20 w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center">Z</div>
            )}
            <button
              onClick={toggleSidebar}
              className="text-white/80 hover:text-white transition-all duration-200 hover:bg-white/10 p-1 rounded-md lg:block"
            >
              {sidebarOpen ? '←' : '→'}
            </button>
          </div>

          {/* Enhanced Navigation */}
          <nav className="flex-1 px-2 sm:px-3 py-4 sm:py-6 space-y-1 sm:space-y-2 overflow-y-auto" role="navigation" aria-label="Primary">
            {allNavigation.map((item) => {
              const isActive = pathname === item.href;
              const showText = sidebarOpen || isLargeScreen;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => {
                    // Close sidebar on mobile after navigation
                    if (!isLargeScreen) {
                      toggleSidebar();
                    }
                  }}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={!showText ? item.name : undefined}
                  title={!showText ? item.name : undefined}
                  ref={firstLinkRef}
                  className={cn(
                    "group flex items-center px-2 sm:px-3 py-2 sm:py-3 text-sm font-medium rounded-lg sm:rounded-xl transition-all duration-200",
                    "hover:scale-105 active:scale-95",
                    isActive
                      ? "bg-gradient-to-r from-primary-tech-blue to-ai-purple text-white shadow-lg"
                      : "text-slate-300 hover:bg-secondary-aqua/10 hover:text-white"
                  )}
                >
                  <span className={cn(
                    "text-base sm:text-lg transition-transform duration-200 flex-shrink-0",
                    isActive ? "scale-110" : "group-hover:scale-110"
                  )}>
                    {item.icon}
                  </span>
                  {showText && (
                    <span className="ml-2 sm:ml-3 font-semibold truncate">{item.name}</span>
                  )}
                  {isActive && showText && (
                    <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse flex-shrink-0"></div>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        {/* Enhanced Header */}
        <header className="bg-gradient-to-r from-white to-blue-50 dark:from-gray-900 dark:to-primary-deep-blue/20 border-b border-primary-tech-blue/20 dark:border-primary-tech-blue/30 shadow-sm">
          <div className="flex items-center justify-between h-14 sm:h-16 px-4 sm:px-6">
            {/* Mobile menu button */}
            <button
              onClick={toggleSidebar}
              className="lg:hidden text-primary-deep-blue dark:text-secondary-cyan hover:text-primary-tech-blue dark:hover:text-white p-2 rounded-md"
              ref={toggleBtnRef}
              aria-controls="primary-sidebar"
              aria-expanded={sidebarOpen}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <div className="flex-1 lg:flex-none lg:ml-0 flex items-center justify-end gap-3">
              <WsStatusPill />
              <AccountMenu />
            </div>
          </div>
          {/* Backend status banner below header */}
          <BackendStatusBanner />
        </header>
        
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-gradient-to-br from-background to-blue-50/30 dark:from-background dark:to-primary-deep-blue/10">
          {children}
        </main>
      </div>
    </div>
  );
}