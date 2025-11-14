# ZiggyAI Design System - Quantum Blue

## Overview
This design system defines the visual identity for ZiggyAI, a modern intelligent trading AI platform. The design communicates trust, intelligence, clarity, and high-performance fintech aesthetics.

## Color Palette

### Primary Colors
- **Deep Intelligent Blue**: `#103A71` - Primary brand color, conveys trust and intelligence
- **Bright Tech Blue**: `#1B5FA7` - Secondary brand color, represents technology and innovation

### Secondary Colors
- **Soft Cyan**: `#51C8F5` - Highlights and interactive elements
- **Cool Aqua**: `#2FA2C9` - Information and data visualization

### AI Accent Color
- **Neural Purple**: `#7A4CE0` - Exclusive to AI features, signals, predictions, and intelligent capabilities
  - Use for: AI signals, prediction confidence, anomaly detection, model suggestions

### Semantic Colors

#### Success / Gains
- **Clean Green**: `#2ECC71`
- Use for: Profitable trades, positive performance, buy signals, successful operations

#### Danger / Losses
- **Market Red**: `#E74C3C`
- Use for: Losses, sell signals, errors, alerts, negative performance

#### Warning / Caution
- **Gold Yellow**: `#F4C542`
- Use for: Warnings, pending states, important notices

### Background Colors

#### Light Mode
- **Background**: `#F6F7FA` - Main page background
- **Surface**: `#ffffff` - Cards, panels, elevated surfaces

#### Dark Mode
- **Background**: `#0E121A` - Main page background
- **Surface**: `#1e293b` - Cards, panels, elevated surfaces

### Text Colors
- **Primary Text**: `#1C1E24` (light mode), `#f1f5f9` (dark mode)
- **Secondary Text**: `#5C6270` (light mode), `#94a3b8` (dark mode)

## Typography

### Font Families
- **Primary**: Inter - Clean, modern sans-serif for UI and content
- **Monospace**: JetBrains Mono, IBM Plex Mono - For numeric data, prices, P/L displays, ticker symbols

### Font Weights
- Regular: 400 - Body text
- Medium: 500 - Subtle emphasis
- Semibold: 600 - Headings, labels
- Bold: 700 - Primary headings, important metrics

### Usage Guidelines
- All numeric UI elements (charts, tickers, prices, P/L displays) **must** use monospace fonts
- Apply monospace using `font-mono` class or `var(--font-mono)` CSS variable
- Trading data, portfolio values, and market prices should always be monospace

## Spacing Scale
Use consistent spacing throughout the application:
- `4px` - Tight spacing between related items
- `8px` - Default spacing between elements
- `12px` - Small gaps
- `16px` - Medium gaps (default padding)
- `24px` - Large gaps between sections
- `32px` - Extra large gaps

## Border Radius
- **Cards**: `0.75rem` (12px) - `rounded-xl`
- **Buttons**: `0.5rem` (8px) - `rounded-lg`
- **Inputs**: `0.375rem` (6px) - `rounded-md`
- **Badges**: `9999px` - `rounded-full`

## Shadows
- **Small**: `0 1px 3px 0 rgb(0 0 0 / 0.1)` - Subtle elevation
- **Medium**: `0 4px 6px -1px rgb(0 0 0 / 0.1)` - Standard cards
- **Large**: `0 10px 15px -3px rgb(0 0 0 / 0.1)` - Prominent elements

## Trading-Specific Guidelines

### Gains/Losses Display
```tsx
// Gains - use Clean Green
<span className="text-success font-mono">+$1,234.56</span>

// Losses - use Market Red
<span className="text-danger font-mono">-$432.10</span>
```

### AI Features
Use Neural Purple (`ai-purple`) sparingly for:
- AI-generated signals
- Prediction confidence indicators
- Model suggestions
- Anomaly detection alerts
- Intelligent insights

### Neutral/Waiting States
Use primary blues and grays for neutral states:
- Pending orders
- Waiting for data
- Inactive states

## CSS Variables

### Using Theme Colors
```css
/* Primary colors */
color: var(--primary-deep-blue);
color: var(--primary-tech-blue);

/* Secondary colors */
color: var(--secondary-cyan);
color: var(--secondary-aqua);

/* AI accent */
color: var(--ai-purple);

/* Semantic colors */
color: var(--success);
color: var(--danger);
color: var(--warning);

/* Monospace font */
font-family: var(--font-mono);
```

### Using with Tailwind
```tsx
<div className="bg-primary-tech-blue text-white">
  <span className="text-ai-purple">AI Signal</span>
  <span className="text-success font-mono">+12.5%</span>
</div>
```

## Accessibility

### Contrast Ratios
All color combinations meet **WCAG AA** standards:
- Normal text: minimum 4.5:1
- Large text: minimum 3:1
- Interactive elements: minimum 3:1

### Focus States
All interactive elements have visible focus indicators:
- 2px solid outline in accent color
- 2px offset for clarity

## Icon Guidelines
- Use Lucide React icon set for consistency
- Default size: 24px (w-6 h-6)
- Stroke width: 1.5-2px
- Keep icons simple and recognizable

## Component Guidelines

### Cards
```tsx
<Card className="bg-surface border border-border shadow-lg">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    {/* content */}
  </CardContent>
</Card>
```

### Buttons
- Primary: Use for main actions
- Secondary: Use for secondary actions
- Outline: Use for tertiary actions
- Danger: Use for destructive actions

### Data Display
- Always use monospace for numbers
- Use color to indicate sentiment (green = positive, red = negative)
- Include proper currency formatting
- Show percentage changes with +/- indicators

## Dark Mode

### Principles
- Maintain color hierarchy in dark mode
- Use slightly brighter colors for accents
- Ensure text remains readable (high contrast)
- Avoid pure black (#000000), use dark blue (#0E121A)

### Testing
Test all components in both light and dark modes to ensure:
- Text is readable
- Colors don't bloom or over-glow
- Borders are visible
- Hover states are clear

## Animation Guidelines
- **Duration**: 200-300ms for most transitions
- **Easing**: cubic-bezier(0.4, 0, 0.2, 1) for natural feel
- **Hover effects**: Subtle scale (1.05) and shadow increase
- **Loading states**: Use pulse or shimmer animations

## Best Practices

1. **Use semantic colors**: Prefer `var(--success)` over hardcoded `#2ECC71`
2. **Maintain consistency**: Use the same color for the same purpose across the app
3. **Monospace for numbers**: Always use monospace font for numeric data
4. **AI = Purple**: Reserve Neural Purple exclusively for AI features
5. **Accessible contrast**: Test color combinations for accessibility
6. **Dark mode parity**: Ensure feature parity between light and dark modes

## Migration Guide

### Replacing Old Colors
```tsx
// Old
className="bg-blue-600 text-green-500"

// New
className="bg-primary-tech-blue text-success"
```

### Using CSS Variables
```tsx
// Old
style={{ color: '#2563eb' }}

// New
style={{ color: 'var(--primary-tech-blue)' }}
```

### Numeric Display
```tsx
// Old
<span className="text-xl">$1,234.56</span>

// New
<span className="text-xl font-mono">$1,234.56</span>
```

## Resources
- Color palette inspiration: Modern fintech and trading platforms
- Font: [Inter](https://rsms.me/inter/)
- Monospace: [JetBrains Mono](https://www.jetbrains.com/lp/mono/)
- Icons: [Lucide Icons](https://lucide.dev/)
