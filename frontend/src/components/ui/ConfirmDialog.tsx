'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  loading = false
}: ConfirmDialogProps) {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose, loading]);

  if (!isOpen) return null;

  const variantColors = {
    danger: {
      icon: '⚠️',
      iconBg: 'bg-red-100 dark:bg-red-900/30',
      confirmButton: 'danger' as const
    },
    warning: {
      icon: '⚡',
      iconBg: 'bg-yellow-100 dark:bg-yellow-900/30',
      confirmButton: 'primary' as const
    },
    info: {
      icon: 'ℹ️',
      iconBg: 'bg-blue-100 dark:bg-blue-900/30',
      confirmButton: 'primary' as const
    }
  };

  const config = variantColors[variant];

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div 
        className={cn(
          "bg-surface border-2 border-border rounded-2xl shadow-2xl",
          "w-full max-w-md p-6",
          "animate-in fade-in-0 zoom-in-95 duration-200"
        )}
      >
        {/* Icon */}
        <div className="flex items-center justify-center mb-6">
          <div className={cn(
            "w-16 h-16 rounded-full flex items-center justify-center text-4xl",
            config.iconBg
          )}>
            {config.icon}
          </div>
        </div>

        {/* Title */}
        <h2 
          id="dialog-title"
          className="text-2xl font-bold text-fg text-center mb-3"
        >
          {title}
        </h2>

        {/* Description */}
        <p 
          id="dialog-description"
          className="text-base text-fg-muted text-center mb-8 leading-relaxed"
        >
          {description}
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <Button
            onClick={onClose}
            variant="secondary"
            size="lg"
            className="flex-1"
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            onClick={onConfirm}
            variant={config.confirmButton}
            size="lg"
            className="flex-1"
            loading={loading}
            disabled={loading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
