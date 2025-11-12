'use client';

import React from 'react';
import { pageThemes, animations, spacing, typography } from '@/styles/themes';

interface PageLayoutProps {
  children: React.ReactNode;
  theme?: keyof typeof pageThemes;
  title: string;
  subtitle?: string;
  breadcrumbs?: string[];
  rightContent?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function PageLayout({ 
  children, 
  theme = 'dashboard', 
  title, 
  subtitle, 
  breadcrumbs,
  rightContent,
  actions,
  className = '' 
}: PageLayoutProps) {
  const currentTheme = pageThemes[theme] || pageThemes.dashboard;
  
  return (
    <div className={`min-h-screen bg-gradient-to-br ${currentTheme.secondary} dark:${currentTheme.darkMode.secondary} ${animations.pageTransition}`}>
      {/* Unified Page Header */}
      <div className={`bg-gradient-to-r ${currentTheme.primary} dark:${currentTheme.darkMode.primary} rounded-xl mx-6 mt-6 p-8 text-white shadow-2xl ${animations.fadeIn}`}>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            {breadcrumbs && breadcrumbs.length > 0 && (
              <nav className="text-sm text-white/70 mb-2">
                {breadcrumbs.map((crumb, index) => (
                  <span key={index}>
                    {index > 0 && ' / '}
                    {crumb}
                  </span>
                ))}
              </nav>
            )}
            <h1 className={`${typography.pageTitle} bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent`}>
              {title}
            </h1>
            {subtitle && (
              <p className={`${typography.subtitle} text-white/90`}>
                {subtitle}
              </p>
            )}
          </div>
          {(rightContent || actions) && (
            <div className="bg-white/10 backdrop-blur rounded-lg p-4">
              {rightContent || actions}
            </div>
          )}
        </div>
      </div>

      {/* Page Content */}
      <div className={`${spacing.pageContainer} ${className} ${animations.slideIn}`}>
        {children}
      </div>
    </div>
  );
}

// Unified Card Component with theme awareness
interface ThemedCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'glass';
  className?: string;
}

export function ThemedCard({ 
  children, 
  variant = 'default',
  className = '' 
}: ThemedCardProps) {
  const variants = {
    default: 'bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50',
    elevated: `bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 border border-gray-200/50 dark:border-gray-700/50 shadow-xl`,
    glass: 'bg-white/10 backdrop-blur-md border border-white/20'
  };

  return (
    <div 
      className={`
        rounded-xl p-6 shadow-lg 
        ${variants[variant]}
        ${animations.cardHover}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

// Unified Button Component with theme integration
interface ThemedButtonProps {
  children: React.ReactNode;
  theme?: keyof typeof pageThemes;
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export function ThemedButton({ 
  children, 
  theme = 'dashboard', 
  variant = 'primary',
  size = 'md',
  onClick,
  disabled,
  className = '' 
}: ThemedButtonProps) {
  const currentTheme = pageThemes[theme] || pageThemes.dashboard;
  
  const variants = {
    primary: `bg-gradient-to-r ${currentTheme.primary} text-white hover:shadow-xl transform hover:scale-105 transition-all duration-200`,
    secondary: 'bg-white/80 dark:bg-gray-800/80 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 hover:bg-white dark:hover:bg-gray-700',
    ghost: 'bg-transparent hover:bg-white/10 text-gray-700 dark:text-gray-300',
    outline: 'border border-gray-300 dark:border-gray-600 bg-transparent text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800',
    success: 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:shadow-xl transform hover:scale-105 transition-all duration-200',
    danger: 'bg-gradient-to-r from-red-500 to-rose-500 text-white hover:shadow-xl transform hover:scale-105 transition-all duration-200'
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        rounded-lg font-semibold
        ${variants[variant]}
        ${sizes[size]}
        ${animations.buttonPress}
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    >
      {children}
    </button>
  );
}

// Status indicator with theme awareness
interface StatusIndicatorProps {
  status: string;
  theme?: keyof typeof pageThemes;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export function StatusIndicator({ 
  status, 
  theme = 'dashboard', 
  size = 'md',
  label 
}: StatusIndicatorProps) {
  const currentTheme = pageThemes[theme] || pageThemes.dashboard;
  const statusColor = currentTheme.statusColors?.[status as keyof typeof currentTheme.statusColors] || currentTheme.primary;
  
  const sizes = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`${sizes[size]} bg-gradient-to-r ${statusColor} rounded-full ${animations.pulseGlow}`}></div>
      {label && <span className="text-sm font-medium">{label}</span>}
    </div>
  );
}