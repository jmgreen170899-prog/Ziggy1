"use client";

import { useState, useEffect } from "react";

/**
 * Hook to detect if the user prefers reduced motion
 * Respects system accessibility settings
 */
export function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if we're in browser environment
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = () => {
      setPrefersReducedMotion(mediaQuery.matches);
    };

    mediaQuery.addEventListener("change", handleChange);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, []);

  return prefersReducedMotion;
}

/**
 * Hook to manage focus trapping within the intro overlay
 * Returns focus management functions
 */
export function useFocusTrap() {
  const [isTrapping, setIsTrapping] = useState(false);

  useEffect(() => {
    if (!isTrapping) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Tab") {
        // For intro overlay, we don't need complex tab trapping
        // Just prevent tabbing out of the overlay
        const skipButton = document.querySelector(
          "[data-intro-skip]",
        ) as HTMLElement;
        if (skipButton) {
          event.preventDefault();
          skipButton.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isTrapping]);

  return {
    trapFocus: () => setIsTrapping(true),
    releaseFocus: () => setIsTrapping(false),
  };
}
