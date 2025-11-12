# ZiggyClean Intro System

A premium, accessible, and performant intro animation system for the ZiggyClean Financial Trading Platform.

## Features

- **Full-screen animated intro** with logo morphing, wordmark reveal, and tagline stagger
- **Accessibility-first** with `prefers-reduced-motion` support
- **Performance optimized** with GPU-friendly transforms and 60fps target
- **Session persistence** using localStorage with version-based keys
- **Keyboard accessible** with Esc key skip functionality
- **Focus management** with proper focus trapping and restoration
- **Custom events** for integration with other systems

## Components

### `IntroGate`

The main wrapper component that handles persistence and orchestrates the intro sequence.

```tsx
import { IntroGate } from '@/features/intro';

<IntroGate appVersion="1.0.0" theme="light">
  <YourApp />
</IntroGate>
```

**Props:**
- `appVersion` (required): Version string for localStorage key
- `children` (required): App content to show after intro
- `durationMs`: Animation duration in milliseconds (default: 2400)
- `forceShow`: Force show intro even if already seen (default: false)
- `theme`: Visual theme variant - 'dark' | 'light' (default: 'dark')
- `onDone`: Callback when intro completes

### `IntroOverlay`

The animated overlay component with all visual effects.

### `usePrefersReducedMotion`

Accessibility hook that detects user motion preferences and adjusts animations accordingly.

## Usage Examples

### Basic Integration

```tsx
// app/layout.tsx
import { IntroGate } from '@/features/intro';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <IntroGate appVersion="1.0.0">
          {children}
        </IntroGate>
      </body>
    </html>
  );
}
```

### Development/Demo Mode

```tsx
// Force show intro for demos or testing
<IntroGate 
  appVersion="1.0.0" 
  forceShow={process.env.NODE_ENV === 'development'}
  onDone={() => console.log('Intro completed!')}
>
  <App />
</IntroGate>
```

### Custom Theme

```tsx
// Light theme variant
<IntroGate appVersion="1.0.0" theme="light">
  <App />
</IntroGate>
```

## Animation Timeline

**Normal Motion (2400ms total):**
- 0-300ms: Background fade in
- 300-1200ms: Logo path drawing animation
- 900-1500ms: Wordmark slide and fade in
- 1200-2000ms: Tagline fade in
- 2000-2400ms: Complete overlay scale and fade out

**Reduced Motion (1000ms total):**
- 0-200ms: Background fade in
- 0-400ms: Logo instant appearance with fade
- 200-600ms: Wordmark fade in
- 400-800ms: Tagline fade in
- 800-1000ms: Overlay fade out

## Accessibility Features

- **Motion Respect**: Automatically detects `prefers-reduced-motion` and switches to fade-only animations
- **Focus Management**: Traps focus within overlay and restores to app after completion
- **Keyboard Navigation**: Skip with Esc key, all interactive elements keyboard accessible
- **WCAG AA Contrast**: All text meets accessibility contrast requirements
- **Screen Reader Support**: Proper ARIA labels and semantic markup

## Performance Optimizations

- **GPU Acceleration**: Uses transform properties for smooth 60fps animations
- **Visibility API**: Delays start if page not visible to avoid wasted cycles
- **Lightweight**: Minimal bundle impact with tree-shakeable components
- **Memory Efficient**: Proper cleanup of event listeners and timers

## Browser Support

- Modern browsers with CSS Grid and Flexbox support
- Graceful degradation for older browsers
- Works without JavaScript (shows app immediately)

## Customization

### Custom Logo

Replace the logo by modifying `src/features/intro/logo.svg` or passing a custom SVG:

```tsx
// The logo is currently embedded in IntroOverlay.tsx
// To use a custom logo, modify the SVG content in the component
```

### Custom Animations

Modify the animation variants in `IntroOverlay.tsx`:

```tsx
const logoVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      duration: 0.8,
      ease: "easeOut"
    }
  }
};
```

### Custom Tagline

Update the tagline text in `IntroOverlay.tsx`:

```tsx
<p className="text-lg">
  Your Custom Tagline Here
</p>
```

## Events

The intro system emits a custom event when complete:

```tsx
// Listen for completion
window.addEventListener('intro:done', () => {
  console.log('Intro animation completed');
});
```

## Storage

Persistence uses localStorage with version-based keys:
- Key format: `ziggy_intro_seen_v${appVersion}`
- Stores timestamp when intro was completed
- Automatically shows intro again when version changes

## Testing

```tsx
// Force show intro
<IntroGate appVersion="1.0.0" forceShow={true}>
  <App />
</IntroGate>

// Test different themes
<IntroGate appVersion="1.0.0" theme="dark" forceShow={true}>
  <App />
</IntroGate>

// Test callbacks
<IntroGate 
  appVersion="1.0.0" 
  forceShow={true}
  onDone={() => console.log('Complete!')}
>
  <App />
</IntroGate>
```