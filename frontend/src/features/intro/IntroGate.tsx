'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { IntroOverlay } from './IntroOverlay';

interface IntroGateProps {
  /** Children to render after intro completes */
  children: React.ReactNode;
  /** App version for storage key and display */
  appVersion: string;
  /** Duration of intro animation in milliseconds */
  durationMs?: number;
  /** Force show intro even if already seen (for demos/testing) */
  forceShow?: boolean;
  /** Theme variant */
  theme?: 'dark' | 'light';
  /** Callback when intro completes */
  onDone?: () => void;
}

/**
 * IntroGate wraps your app and manages the intro sequence
 * Handles persistence, ensures intro shows once per version
 * 
 * Usage:
 * <IntroGate appVersion="1.0.0">
 *   <AppShell />
 * </IntroGate>
 */
export function IntroGate({
  children,
  appVersion,
  durationMs = 4500,
  forceShow = false,
  theme = 'dark',
  onDone
}: IntroGateProps) {
  const [shouldShowIntro, setShouldShowIntro] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Storage key for persistence
  const storageKey = `ziggy_intro_seen_v${appVersion}`;

  // Check if intro should be shown
  useEffect(() => {
    const checkIntroStatus = () => {
      console.log('🎬 IntroGate: Checking intro status...', { forceShow, storageKey });
      try {
        if (forceShow) {
          console.log('🎬 IntroGate: Force show enabled, showing intro');
          setShouldShowIntro(true);
          setIsLoading(false);
          return;
        }

        // Check localStorage
        const introSeen = localStorage.getItem(storageKey);
        console.log('🎬 IntroGate: localStorage check:', { introSeen });
        if (!introSeen) {
          console.log('🎬 IntroGate: First time visit, showing intro');
          setShouldShowIntro(true);
        } else {
          console.log('🎬 IntroGate: Intro already seen, skipping');
        }
      } catch (error) {
        // localStorage not available, show intro anyway
        console.log('🎬 IntroGate: localStorage error, showing intro anyway:', error);
        setShouldShowIntro(true);
      }
      
      setIsLoading(false);
    };

    // Small delay to avoid flash
    const timer = setTimeout(checkIntroStatus, 50);
    return () => clearTimeout(timer);
  }, [appVersion, forceShow, storageKey]);

  // Handle intro completion
  const handleIntroComplete = useCallback(() => {
    try {
      // Mark as seen in localStorage
      if (!forceShow) {
        localStorage.setItem(storageKey, Date.now().toString());
      }
    } catch (error) {
      // localStorage not available, continue anyway
      console.warn('Could not save intro completion status:', error);
    }

    setShouldShowIntro(false);
    onDone?.();
  }, [forceShow, storageKey, onDone]);

  // Listen for intro:done custom event
  useEffect(() => {
    const handleIntroDone = () => {
      handleIntroComplete();
    };

    window.addEventListener('intro:done', handleIntroDone);
    return () => window.removeEventListener('intro:done', handleIntroDone);
  }, [handleIntroComplete]);

  // Show loading state briefly to prevent flash
  if (isLoading) {
    return (
      <div className={`fixed inset-0 flex items-center justify-center ${
        theme === 'dark' ? 'bg-gray-900' : 'bg-white'
      }`}>
        {/* Minimal loading indicator */}
        <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${
          theme === 'dark' ? 'border-white' : 'border-gray-900'
        }`} />
      </div>
    );
  }

  return (
    <>
      {/* Intro overlay */}
      <IntroOverlay
        show={shouldShowIntro}
        durationMs={durationMs}
        appVersion={appVersion}
        theme={theme}
        onComplete={handleIntroComplete}
      />
      
      {/* Main app content */}
      {!shouldShowIntro && children}
    </>
  );
}

// Re-export components for convenience
export { IntroOverlay } from './IntroOverlay';
export { usePrefersReducedMotion } from './usePrefersReducedMotion';