'use client';

import React, { createContext, useContext, useEffect } from 'react';

interface ThemeContextType {
  theme: 'light';
  setTheme: () => void;
  resolvedTheme: 'light';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const setTheme = () => {
    // Only light theme supported, no-op
  };

  // Apply light theme to document
  useEffect(() => {
    if (!mounted) return;
    
    const root = window.document.documentElement;
    
    // Remove existing theme classes and always use light
    root.classList.remove('light', 'dark');
    root.classList.add('light');
    
    // Set light theme CSS custom properties
    root.style.setProperty('--background', '#ffffff');
    root.style.setProperty('--foreground', '#171717');
    root.style.setProperty('--surface', '#f9fafb');
    root.style.setProperty('--surface-hover', '#f3f4f6');
    root.style.setProperty('--border', '#e5e7eb');
    root.style.setProperty('--border-hover', '#d1d5db');
    root.style.setProperty('--accent', '#3b82f6');
    root.style.setProperty('--accent-fg', '#ffffff');
    root.style.setProperty('--fg', '#171717');
    root.style.setProperty('--fg-muted', '#6b7280');
    root.style.setProperty('--success', '#10b981');
    root.style.setProperty('--warning', '#f59e0b');
    root.style.setProperty('--danger', '#ef4444');
  }, [mounted]);

  // Don't render until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{
        theme: 'light',
        setTheme: () => {},
        resolvedTheme: 'light',
      }}>
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{
      theme: 'light',
      setTheme,
      resolvedTheme: 'light',
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}