'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePrefersReducedMotion, useFocusTrap } from './usePrefersReducedMotion';

interface IntroOverlayProps {
  /** Duration of the intro animation in milliseconds */
  durationMs?: number;
  /** App version for branding */
  appVersion?: string;
  /** Theme variant */
  theme?: 'dark' | 'light';
  /** Callback when intro completes */
  onComplete?: () => void;
  /** Whether to show the overlay */
  show: boolean;
}

/**
 * Full-screen animated intro overlay
 * Features logo animation, wordmark reveal, and background effects
 * Fully accessible with reduced motion support
 */
export function IntroOverlay({
  durationMs = 4500,
  appVersion = '1.0.0',
  theme = 'dark',
  onComplete,
  show
}: IntroOverlayProps) {
  console.log('🎭 IntroOverlay: Render called', { show, durationMs, theme });
  
  const prefersReducedMotion = usePrefersReducedMotion();
  const { trapFocus, releaseFocus } = useFocusTrap();
  
  const [isVisible, setIsVisible] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<'enter' | 'play' | 'complete' | 'exit'>('enter');

  // Extended timeline for dramatic effect
  const timeline = useMemo(() => prefersReducedMotion ? {
    backgroundFade: { start: 0, end: 300 },
    logoReveal: { start: 0, end: 600 },
    wordmarkReveal: { start: 300, end: 900 },
    taglineReveal: { start: 600, end: 1200 },
    exit: { start: 1200, end: 1500 }
  } : {
    backgroundFade: { start: 0, end: 500 },
    logoReveal: { start: 500, end: 2000 },
    wordmarkReveal: { start: 1600, end: 2800 },
    taglineReveal: { start: 2400, end: 3600 },
    holdMoment: { start: 3600, end: 4000 },
    exit: { start: 4000, end: durationMs }
  }, [prefersReducedMotion, durationMs]);

  // Handle skip functionality
  const handleSkip = () => {
    setCurrentPhase('complete');
    setTimeout(() => setCurrentPhase('exit'), 50);
  };

  // Keyboard event handling
  useEffect(() => {
    if (!show) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        handleSkip();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [show]);

  // Animation sequence
  useEffect(() => {
    console.log('🎭 IntroOverlay: Effect triggered', { show, currentPhase });
    if (!show) return;

    setIsVisible(true);
    setCurrentPhase('enter');
    trapFocus();

    const sequence = async () => {
      // Wait for visibility
      if (document.visibilityState !== 'visible') {
        await new Promise(resolve => {
          const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
              document.removeEventListener('visibilitychange', handleVisibilityChange);
              resolve(void 0);
            }
          };
          document.addEventListener('visibilitychange', handleVisibilityChange);
        });
      }

      setCurrentPhase('play');

      // Auto-complete after duration
      setTimeout(() => {
        setCurrentPhase(current => current !== 'exit' ? 'complete' : current);
        setTimeout(() => setCurrentPhase('exit'), 100);
      }, timeline.exit.start);
    };

    sequence();
  }, [show, timeline.exit.start, trapFocus, currentPhase]);

  // Handle exit phase
  useEffect(() => {
    if (currentPhase === 'exit') {
      setTimeout(() => {
        setIsVisible(false);
        releaseFocus();
        onComplete?.();
        
        // Emit custom event
        window.dispatchEvent(new CustomEvent('intro:done'));
      }, timeline.exit.end - timeline.exit.start);
    }
  }, [currentPhase, onComplete, releaseFocus, timeline]);

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        duration: prefersReducedMotion ? 0.2 : 0.3
      }
    },
    exit: { 
      opacity: 0,
      scale: prefersReducedMotion ? 1 : 1.05,
      transition: { 
        duration: prefersReducedMotion ? 0.2 : 0.4
      }
    }
  };

  const logoVariants = {
    hidden: { opacity: 0, scale: 0.6 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { 
        duration: prefersReducedMotion ? 0.6 : 1.5,
        delay: prefersReducedMotion ? 0 : 0.5
      }
    }
  };

  const wordmarkVariants = {
    hidden: { opacity: 0, y: 40 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: prefersReducedMotion ? 0.6 : 1.2,
        delay: prefersReducedMotion ? 0.3 : 1.6
      }
    }
  };

  const taglineVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1,
      y: 0,
      transition: { 
        duration: prefersReducedMotion ? 0.6 : 1.2,
        delay: prefersReducedMotion ? 0.6 : 2.4
      }
    }
  };

  const skipButtonVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        duration: 0.3,
        delay: 0.5
      }
    }
  };

  // Background particles and effects (disabled for reduced motion)
  const backgroundParticles = !prefersReducedMotion && (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Floating particles */}
      {Array.from({ length: 16 }).map((_, i) => (
        <motion.div
          key={i}
          className={`absolute w-1 h-1 rounded-full ${
            theme === 'dark' ? 'bg-white/30' : 'bg-gray-600/30'
          }`}
          style={{
            left: `${5 + (i * 6) % 90}%`,
            top: `${10 + (i * 11) % 80}%`,
          }}
          animate={{
            y: [-15, 15, -15],
            x: [-5, 5, -5],
            opacity: [0.1, 0.8, 0.1],
            scale: [0.5, 1.2, 0.5],
          }}
          transition={{
            duration: 4 + (i * 0.3),
            repeat: Infinity,
            ease: 'easeInOut',
            delay: i * 0.2,
          }}
        />
      ))}
      
      {/* Subtle gradient overlay */}
      <motion.div
        className={`absolute inset-0 ${
          theme === 'dark' 
            ? 'bg-gradient-to-br from-blue-900/10 via-transparent to-purple-900/10'
            : 'bg-gradient-to-br from-blue-100/30 via-transparent to-indigo-100/30'
        }`}
        animate={{
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );

  if (!isVisible) return null;

  return (
    <AnimatePresence mode="wait">
      {show && (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={currentPhase === 'exit' ? 'exit' : 'visible'}
          className={`fixed inset-0 z-50 flex items-center justify-center ${
            theme === 'dark' 
              ? 'bg-gray-900 text-white' 
              : 'bg-white text-gray-900'
          }`}
          role="dialog"
          aria-modal="true"
          aria-label="Application intro"
        >
          {backgroundParticles}

          {/* Skip button */}
          <motion.button
            variants={skipButtonVariants}
            initial="hidden"
            animate="visible"
            onClick={handleSkip}
            data-intro-skip
            className={`absolute top-6 right-6 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              theme === 'dark'
                ? 'text-white/70 hover:text-white hover:bg-white/10 focus:bg-white/10'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:bg-gray-100'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
            aria-label="Skip intro animation"
          >
            Skip
          </motion.button>

          {/* Main content */}
          <motion.div 
            className="flex flex-col items-center space-y-8 text-center"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ 
              duration: prefersReducedMotion ? 0.5 : 1.0,
              delay: prefersReducedMotion ? 0 : 0.3,
              ease: "easeOut" 
            }}
          >
            {/* Logo */}
            <motion.div
              variants={logoVariants}
              initial="hidden"
              animate="visible"
              className="relative"
            >
              <div className={`w-32 h-32 md:w-40 md:h-40 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                <svg viewBox="0 0 120 120" className="w-full h-full">
                  <defs>
                    <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="currentColor" stopOpacity="1" />
                      <stop offset="100%" stopColor="currentColor" stopOpacity="0.6" />
                    </linearGradient>
                  </defs>
                  
                  {/* Animated circle */}
                  <motion.circle 
                    cx="60" 
                    cy="60" 
                    r="50" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ 
                      duration: prefersReducedMotion ? 0.6 : 2.0, 
                      delay: prefersReducedMotion ? 0 : 0.8,
                      ease: 'easeInOut' 
                    }}
                  />
                  
                  {/* Animated zigzag */}
                  <motion.path 
                    d="M25 35 L45 35 L35 50 L55 50 L45 65 L65 65 L55 80 L75 80 L85 65 L95 65" 
                    fill="none" 
                    stroke="url(#logoGradient)" 
                    strokeWidth="4" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ 
                      duration: prefersReducedMotion ? 0.6 : 1.5, 
                      delay: prefersReducedMotion ? 0.2 : 1.2,
                      ease: 'easeOut' 
                    }}
                  />
                  
                  {/* Animated dots */}
                  {[
                    { cx: 30, cy: 25 },
                    { cx: 70, cy: 30 },
                    { cx: 40, cy: 90 },
                    { cx: 80, cy: 85 },
                    { cx: 90, cy: 45 }
                  ].map((dot, i) => (
                    <motion.circle 
                      key={i}
                      cx={dot.cx} 
                      cy={dot.cy} 
                      r="2" 
                      fill="currentColor"
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ 
                        duration: prefersReducedMotion ? 0.4 : 0.6, 
                        delay: prefersReducedMotion ? 0.4 + (i * 0.1) : 1.8 + (i * 0.15),
                        ease: 'easeOut' 
                      }}
                    />
                  ))}
                </svg>
              </div>
            </motion.div>

            {/* Wordmark */}
            <motion.div
              variants={wordmarkVariants}
              initial="hidden"
              animate="visible"
            >
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
                ZiggyClean
              </h1>
            </motion.div>

            {/* Tagline */}
            <motion.div
              variants={taglineVariants}
              initial="hidden"
              animate="visible"
            >
              <p className={`text-xl md:text-2xl ${
                theme === 'dark' ? 'text-white/70' : 'text-gray-600'
              }`}>
                AI-Powered Financial Trading Platform
              </p>
              <p className={`text-base md:text-lg mt-3 ${
                theme === 'dark' ? 'text-white/50' : 'text-gray-500'
              }`}>
                Version {appVersion}
              </p>
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}