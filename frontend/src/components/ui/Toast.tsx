'use client';

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/utils';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextValue {
  showToast: (toast: Omit<Toast, 'id'>) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

interface ToastProviderProps {
  children: React.ReactNode;
  maxToasts?: number;
}

export function ToastProvider({ children, maxToasts = 5 }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    const timeout = toastRefs.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      toastRefs.current.delete(id);
    }
  }, []);

  const showToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const duration = toast.duration || 5000;
    
    setToasts(prev => {
      const newToasts = [...prev, { ...toast, id }];
      return newToasts.slice(-maxToasts);
    });

    const timeout = setTimeout(() => removeToast(id), duration);
    toastRefs.current.set(id, timeout);
  }, [maxToasts, removeToast]);

  const success = useCallback((title: string, message?: string) => {
    showToast({ type: 'success', title, message });
  }, [showToast]);

  const error = useCallback((title: string, message?: string) => {
    showToast({ type: 'error', title, message, duration: 7000 });
  }, [showToast]);

  const warning = useCallback((title: string, message?: string) => {
    showToast({ type: 'warning', title, message, duration: 6000 });
  }, [showToast]);

  const info = useCallback((title: string, message?: string) => {
    showToast({ type: 'info', title, message });
  }, [showToast]);

  useEffect(() => {
    return () => {
      toastRefs.current.forEach(timeout => clearTimeout(timeout));
    };
  }, []);

  const value: ToastContextValue = {
    showToast,
    success,
    error,
    warning,
    info
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div 
      className="fixed top-4 right-4 z-[200] flex flex-col gap-3 max-w-md pointer-events-none"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isLeaving, setIsLeaving] = useState(false);

  const config = {
    success: {
      icon: '✓',
      iconBg: 'bg-success/10 dark:bg-success/20 text-success dark:text-success',
      border: 'border-success/30 dark:border-success/50',
      bg: 'bg-success/5 dark:bg-success/10'
    },
    error: {
      icon: '✕',
      iconBg: 'bg-danger/10 dark:bg-danger/20 text-danger dark:text-danger',
      border: 'border-danger/30 dark:border-danger/50',
      bg: 'bg-danger/5 dark:bg-danger/10'
    },
    warning: {
      icon: '⚠',
      iconBg: 'bg-warning/10 dark:bg-warning/20 text-warning dark:text-warning',
      border: 'border-warning/30 dark:border-warning/50',
      bg: 'bg-warning/5 dark:bg-warning/10'
    },
    info: {
      icon: 'i',
      iconBg: 'bg-primary-tech-blue/10 dark:bg-secondary-cyan/20 text-primary-tech-blue dark:text-secondary-cyan',
      border: 'border-primary-tech-blue/30 dark:border-secondary-cyan/50',
      bg: 'bg-primary-tech-blue/5 dark:bg-secondary-cyan/10'
    }
  };

  const style = config[toast.type];

  const handleRemove = () => {
    setIsLeaving(true);
    setTimeout(() => onRemove(toast.id), 200);
  };

  return (
    <div
      className={cn(
        "pointer-events-auto",
        "flex items-start gap-3 p-4 rounded-xl shadow-lg border-2",
        "backdrop-blur-sm",
        "transition-all duration-200",
        isLeaving ? "opacity-0 translate-x-full" : "opacity-100 translate-x-0 animate-in slide-in-from-right",
        style.bg,
        style.border
      )}
      role="alert"
      aria-live="polite"
    >
      {/* Icon */}
      <div className={cn(
        "flex items-center justify-center w-8 h-8 rounded-full font-bold text-lg flex-shrink-0",
        style.iconBg
      )}>
        {style.icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="font-bold text-fg text-sm mb-1">
          {toast.title}
        </h4>
        {toast.message && (
          <p className="text-sm text-fg-muted leading-relaxed">
            {toast.message}
          </p>
        )}
      </div>

      {/* Close Button */}
      <button
        onClick={handleRemove}
        className="flex-shrink-0 w-6 h-6 rounded-full hover:bg-black/10 dark:hover:bg-white/10 flex items-center justify-center transition-colors"
        aria-label="Close notification"
      >
        <svg className="w-4 h-4 text-fg-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export default ToastProvider;
