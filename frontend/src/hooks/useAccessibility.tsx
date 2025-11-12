import React, { useEffect, useRef } from 'react';

// Hook for managing focus trap within modals/dialogs
export function useFocusTrap(isActive: boolean) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          e.preventDefault();
        }
      }
    };

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // You can add a callback here for handling escape
        const escapeEvent = new CustomEvent('focustrap:escape');
        container.dispatchEvent(escapeEvent);
      }
    };

    document.addEventListener('keydown', handleTabKey);
    document.addEventListener('keydown', handleEscapeKey);
    
    // Focus first element when trap activates
    firstElement?.focus();

    return () => {
      document.removeEventListener('keydown', handleTabKey);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isActive]);

  return containerRef;
}

// Hook for managing keyboard navigation in lists
export function useKeyboardNavigation<T>(
  items: T[],
  onSelect?: (index: number) => void,
  onEscape?: () => void
) {
  const listRef = useRef<HTMLDivElement>(null);
  const currentIndexRef = useRef<number>(-1);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!listRef.current) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          currentIndexRef.current = Math.min(currentIndexRef.current + 1, items.length - 1);
          focusItem(currentIndexRef.current);
          break;
          
        case 'ArrowUp':
          e.preventDefault();
          currentIndexRef.current = Math.max(currentIndexRef.current - 1, 0);
          focusItem(currentIndexRef.current);
          break;
          
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (currentIndexRef.current >= 0 && onSelect) {
            onSelect(currentIndexRef.current);
          }
          break;
          
        case 'Escape':
          e.preventDefault();
          onEscape?.();
          break;
          
        case 'Home':
          e.preventDefault();
          currentIndexRef.current = 0;
          focusItem(0);
          break;
          
        case 'End':
          e.preventDefault();
          currentIndexRef.current = items.length - 1;
          focusItem(items.length - 1);
          break;
      }
    };

    const focusItem = (index: number) => {
      const items = listRef.current?.querySelectorAll('[data-keyboard-nav-item]');
      const item = items?.[index] as HTMLElement;
      item?.focus();
    };

    const element = listRef.current;
    element?.addEventListener('keydown', handleKeyDown);

    return () => {
      element?.removeEventListener('keydown', handleKeyDown);
    };
  }, [items.length, onSelect, onEscape]);

  return { listRef, currentIndex: currentIndexRef.current };
}

// Hook for screen reader announcements
export function useScreenReader() {
  const announceRef = useRef<HTMLDivElement>(null);

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announceRef.current) return;
    
    announceRef.current.setAttribute('aria-live', priority);
    announceRef.current.textContent = message;
    
    // Clear after announcement
    setTimeout(() => {
      if (announceRef.current) {
        announceRef.current.textContent = '';
      }
    }, 1000);
  };

  const ScreenReaderAnnouncer = React.memo(() => (
    <div
      ref={announceRef}
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    />
  ));

  ScreenReaderAnnouncer.displayName = 'ScreenReaderAnnouncer';

  return { announce, ScreenReaderAnnouncer };
}

// Hook for reduced motion preferences
export function useReducedMotion() {
  const prefersReducedMotion = typeof window !== 'undefined' 
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  return prefersReducedMotion;
}