'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({ icon, title, description, actionText, onAction }: EmptyStateProps) {
  return (
    <div className="p-16 text-center border-2 border-dashed border-border rounded-xl bg-surface/50">
      {icon && (
        <div className="text-7xl mb-6 opacity-60 filter grayscale hover:grayscale-0 hover:opacity-100 transition-all duration-300" aria-hidden>
          {icon}
        </div>
      )}
      <div className="text-2xl font-bold text-fg mb-2">{title}</div>
      {description && (
        <div className="text-base text-fg-muted mt-2 max-w-md mx-auto leading-relaxed">{description}</div>
      )}
      {actionText && (
        <Button onClick={onAction} className="mt-6" size="lg">
          {actionText}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
