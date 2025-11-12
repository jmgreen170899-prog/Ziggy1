'use client';

import React from 'react';
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'white' | 'gray';
  className?: string;
}

export function LoadingSpinner({ size = 'md', color = 'primary', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
    xl: 'w-16 h-16 border-4'
  };

  const colorClasses = {
    primary: 'border-accent border-t-transparent',
    secondary: 'border-fg-muted border-t-transparent',
    white: 'border-white border-t-transparent',
    gray: 'border-gray-400 border-t-transparent'
  };

  return (
    <div
      className={clsx(
        'border-solid rounded-full animate-spin',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
      role="status"
      aria-label="Loading"
    />
  );
}

interface LoadingStateProps {
  message?: string;
  showSpinner?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingState({ 
  message = 'Loading...', 
  showSpinner = true, 
  size = 'md',
  className 
}: LoadingStateProps) {
  return (
    <div className={clsx('flex flex-col items-center justify-center p-12 space-y-6', className)} role="status">
      {showSpinner && <LoadingSpinner size={size} />}
      <div className="text-center space-y-2">
        <p className="text-base font-semibold text-fg animate-pulse">
          {message}
        </p>
        <div className="flex justify-center gap-1">
          <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
}

export function Skeleton({ 
  className, 
  width, 
  height, 
  variant = 'rectangular' 
}: SkeletonProps) {
  const variantClasses = {
    text: 'rounded-sm',
    circular: 'rounded-full',
    rectangular: 'rounded-lg'
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={clsx(
        'skeleton',
        variantClasses[variant],
        !height && variant === 'text' && 'h-4',
        !height && variant === 'rectangular' && 'h-6',
        !width && 'w-full',
        className
      )}
      style={style}
      role="status"
      aria-label="Loading content"
    />
  );
}

interface CardSkeletonProps {
  showHeader?: boolean;
  headerHeight?: number;
  contentLines?: number;
  className?: string;
}

export function CardSkeleton({ 
  showHeader = true, 
  headerHeight = 60,
  contentLines = 3,
  className 
}: CardSkeletonProps) {
  return (
    <div className={clsx('border rounded-lg p-6 space-y-4', className)}>
      {showHeader && (
        <div className="flex items-center justify-between">
          <Skeleton width="40%" height={headerHeight} />
          <Skeleton width="20%" height={32} />
        </div>
      )}
      <div className="space-y-3">
        {Array.from({ length: contentLines }).map((_, index) => (
          <Skeleton 
            key={index}
            width={index === contentLines - 1 ? '75%' : '100%'}
            height={16}
          />
        ))}
      </div>
    </div>
  );
}

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  className?: string;
}

export function TableSkeleton({ 
  rows = 5, 
  columns = 4, 
  showHeader = true, 
  className 
}: TableSkeletonProps) {
  return (
    <div className={clsx('w-full', className)}>
      {showHeader && (
        <div className="grid gap-4 p-4 border-b" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={`header-${index}`} height={20} />
          ))}
        </div>
      )}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div 
          key={`row-${rowIndex}`}
          className="grid gap-4 p-4 border-b border-gray-100 dark:border-gray-800" 
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton 
              key={`cell-${rowIndex}-${colIndex}`} 
              height={16}
              width={colIndex === 0 ? '80%' : '60%'}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

interface DataLoadingProps {
  isLoading: boolean;
  error?: Error | string | null;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  retryAction?: () => void;
  emptyState?: React.ReactNode;
  isEmpty?: boolean;
}

export function DataLoading({
  isLoading,
  error,
  children,
  loadingComponent,
  errorComponent,
  retryAction,
  emptyState,
  isEmpty = false
}: DataLoadingProps) {
  if (isLoading) {
    return <>{loadingComponent || <LoadingState />}</>;
  }

  if (error) {
    const errorMessage = typeof error === 'string' ? error : error.message;
    
    if (errorComponent) {
      return <>{errorComponent}</>;
    }

    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <div className="text-red-500 text-2xl">⚠️</div>
        <div className="text-center">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
            Failed to load data
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {errorMessage}
          </p>
          {retryAction && (
            <button
              onClick={retryAction}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isEmpty && emptyState) {
    return <>{emptyState}</>;
  }

  return <>{children}</>;
}