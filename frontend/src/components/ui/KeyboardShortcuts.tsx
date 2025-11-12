'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/utils';
import { Button } from './Button';

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  // Navigation
  { keys: ['G', 'D'], description: 'Go to Dashboard', category: 'Navigation' },
  { keys: ['G', 'M'], description: 'Go to Market', category: 'Navigation' },
  { keys: ['G', 'P'], description: 'Go to Portfolio', category: 'Navigation' },
  { keys: ['G', 'T'], description: 'Go to Trading', category: 'Navigation' },
  { keys: ['G', 'N'], description: 'Go to News', category: 'Navigation' },
  { keys: ['G', 'C'], description: 'Go to Crypto', category: 'Navigation' },
  
  // Actions
  { keys: ['R'], description: 'Refresh data', category: 'Actions' },
  { keys: ['S'], description: 'Search / Focus search', category: 'Actions' },
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'Actions' },
  { keys: ['Esc'], description: 'Close dialog / Clear search', category: 'Actions' },
  
  // General
  { keys: ['['], description: 'Toggle sidebar', category: 'General' },
  { keys: ['Ctrl', 'K'], description: 'Command palette (coming soon)', category: 'General' },
];

export function KeyboardShortcuts() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Show shortcuts dialog with '?'
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const target = e.target as HTMLElement;
        // Don't trigger if user is typing in an input
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return;
        }
        e.preventDefault();
        setIsOpen(true);
      }
      // Close with Escape
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [isOpen]);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "fixed bottom-6 right-6 z-50",
          "w-12 h-12 rounded-full",
          "bg-accent text-accent-fg",
          "shadow-lg hover:shadow-xl",
          "flex items-center justify-center",
          "transition-all duration-200",
          "hover:scale-110 active:scale-95",
          "focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
        )}
        aria-label="Show keyboard shortcuts"
        title="Keyboard shortcuts (?)"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      </button>
    );
  }

  const categories = Array.from(new Set(shortcuts.map(s => s.category)));

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          setIsOpen(false);
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <div 
        className={cn(
          "bg-surface border-2 border-border rounded-2xl shadow-2xl",
          "w-full max-w-2xl max-h-[80vh] overflow-hidden",
          "animate-in fade-in-0 zoom-in-95 duration-200"
        )}
      >
        {/* Header */}
        <div className="p-6 border-b-2 border-border bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <span className="text-2xl">⌨️</span>
              </div>
              <div>
                <h2 id="shortcuts-title" className="text-2xl font-bold text-fg">
                  Keyboard Shortcuts
                </h2>
                <p className="text-sm text-fg-muted font-medium">
                  Navigate faster with keyboard shortcuts
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 rounded-lg hover:bg-white/50 dark:hover:bg-gray-800/50 transition-colors"
              aria-label="Close shortcuts dialog"
            >
              <span className="text-2xl">✕</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-200px)]">
          {categories.map(category => (
            <div key={category} className="mb-8 last:mb-0">
              <h3 className="text-lg font-bold text-fg mb-4 flex items-center gap-2">
                <span className="text-accent">■</span>
                {category}
              </h3>
              <div className="space-y-3">
                {shortcuts
                  .filter(s => s.category === category)
                  .map((shortcut, index) => (
                    <div 
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg bg-surface-hover border border-border hover:border-accent transition-colors"
                    >
                      <span className="text-fg font-medium">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <React.Fragment key={keyIndex}>
                            {keyIndex > 0 && (
                              <span className="text-fg-muted mx-1">then</span>
                            )}
                            <kbd className={cn(
                              "px-3 py-1.5 rounded-md",
                              "bg-white dark:bg-gray-800",
                              "border-2 border-border",
                              "text-fg font-mono font-bold text-sm",
                              "shadow-sm"
                            )}>
                              {key}
                            </kbd>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-6 border-t-2 border-border bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-950">
          <div className="flex items-center justify-between">
            <p className="text-sm text-fg-muted">
              Press <kbd className="px-2 py-1 rounded bg-surface border border-border font-mono text-fg font-bold">?</kbd> anytime to show this dialog
            </p>
            <Button onClick={() => setIsOpen(false)} variant="primary">
              Got it!
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default KeyboardShortcuts;
