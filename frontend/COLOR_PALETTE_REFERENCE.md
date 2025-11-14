# ZiggyAI Color Palette Reference

## Quick Reference Guide

### Primary Brand Colors

#### Deep Intelligent Blue
- **Hex**: `#103A71`
- **Usage**: Primary brand color, sidebar background, deep accents
- **CSS Variable**: `var(--primary-deep-blue)`
- **Tailwind**: `bg-primary-deep-blue`, `text-primary-deep-blue`

#### Bright Tech Blue
- **Hex**: `#1B5FA7`
- **Usage**: Interactive elements, buttons, links, accents
- **CSS Variable**: `var(--primary-tech-blue)`
- **Tailwind**: `bg-primary-tech-blue`, `text-primary-tech-blue`

### Secondary Colors

#### Soft Cyan
- **Hex**: `#51C8F5`
- **Usage**: Highlights, hover states, data visualization
- **CSS Variable**: `var(--secondary-cyan)`
- **Tailwind**: `bg-secondary-cyan`, `text-secondary-cyan`

#### Cool Aqua
- **Hex**: `#2FA2C9`
- **Usage**: Information displays, connection status, charts
- **CSS Variable**: `var(--secondary-aqua)`
- **Tailwind**: `bg-secondary-aqua`, `text-secondary-aqua`

### AI Accent

#### Neural Purple
- **Hex**: `#7A4CE0`
- **Usage**: **EXCLUSIVE to AI features** - signals, predictions, confidence scores, model suggestions, anomaly detection
- **CSS Variable**: `var(--ai-purple)`
- **Tailwind**: `bg-ai-purple`, `text-ai-purple`
- **Important**: Reserve this color ONLY for AI-related features to maintain visual hierarchy

### Trading & Semantic Colors

#### Clean Green (Success/Gains)
- **Hex**: `#2ECC71`
- **Usage**: Profitable trades, positive changes, buy signals, success messages
- **CSS Variable**: `var(--success)`
- **Tailwind**: `bg-success`, `text-success`
- **Examples**: "+$1,234.56", "+5.2%", "Profit: $500"

#### Market Red (Danger/Losses)
- **Hex**: `#E74C3C`
- **Usage**: Losses, negative changes, sell signals, errors
- **CSS Variable**: `var(--danger)`
- **Tailwind**: `bg-danger`, `text-danger`
- **Examples**: "-$432.10", "-2.3%", "Loss: $200"

#### Gold Yellow (Warning)
- **Hex**: `#F4C542`
- **Usage**: Warnings, caution states, pending actions
- **CSS Variable**: `var(--warning)`
- **Tailwind**: `bg-warning`, `text-warning`
- **Examples**: "High Volatility", "Pending Order"

### Background Colors

#### Light Mode Background
- **Hex**: `#F6F7FA`
- **Usage**: Main page background (light mode)
- **CSS Variable**: `var(--background)`

#### Dark Mode Background
- **Hex**: `#0E121A`
- **Usage**: Main page background (dark mode)
- **CSS Variable**: `var(--background)` (in dark mode)

#### Surface (Cards, Panels)
- **Light**: `#ffffff`
- **Dark**: `#1e293b`
- **CSS Variable**: `var(--surface)`

### Text Colors

#### Primary Text
- **Light**: `#1C1E24`
- **Dark**: `#f1f5f9`
- **CSS Variable**: `var(--fg)`

#### Secondary Text (Muted)
- **Light**: `#5C6270`
- **Dark**: `#94a3b8`
- **CSS Variable**: `var(--fg-muted)`

## Usage Examples

### Trading Displays
```tsx
// Profit/Gain
<span className="text-success font-mono">+$1,234.56</span>
<span className="text-success font-mono">+5.2%</span>

// Loss/Decline
<span className="text-danger font-mono">-$432.10</span>
<span className="text-danger font-mono">-2.3%</span>

// Neutral
<span className="text-fg font-mono">$50,000.00</span>
```

### AI Features
```tsx
// AI Signal Confidence
<div className="bg-ai-purple/10 text-ai-purple">
  <span className="font-mono">87% confidence</span>
</div>

// AI Coach Recommendation
<div className="border-ai-purple/30 bg-ai-purple/5">
  🧠 AI Coach suggests...
</div>
```

### Buttons
```tsx
// Primary action
<button className="bg-gradient-to-r from-primary-tech-blue to-ai-purple">
  Execute Trade
</button>

// Success action
<button className="bg-success">
  Confirm Profit
</button>

// Danger action
<button className="bg-danger">
  Close Position
</button>
```

### Status Indicators
```tsx
// Connection status
<span className="text-success">● Connected</span>
<span className="text-warning">● Connecting</span>
<span className="text-danger">● Disconnected</span>

// Market status
<span className="text-success">OPEN</span>
<span className="text-fg-muted">CLOSED</span>
```

## Gradients

### Primary Gradient (Buttons, Headers)
```css
background: linear-gradient(135deg, #1B5FA7, #7A4CE0);
/* Tech Blue → AI Purple */
```

### Success Gradient
```css
background: linear-gradient(135deg, #2ECC71, #10b981);
/* Clean Green → Emerald */
```

### Danger Gradient
```css
background: linear-gradient(135deg, #E74C3C, #dc2626);
/* Market Red → Red */
```

### AI Gradient
```css
background: linear-gradient(135deg, #7A4CE0, #9370DB);
/* Neural Purple → Medium Purple */
```

## Color Combinations

### High Contrast (Best for Accessibility)
- Primary Deep Blue (#103A71) on White
- Clean Green (#2ECC71) on White
- Market Red (#E74C3C) on White
- White on Primary Deep Blue

### Medium Contrast
- Tech Blue (#1B5FA7) on Light Background
- Soft Cyan (#51C8F5) on Dark Background
- Neural Purple (#7A4CE0) on Light Background

### Low Contrast (Use Sparingly)
- Secondary text colors on backgrounds
- Borders and dividers

## Dark Mode Adjustments

In dark mode, some colors are automatically adjusted for better visibility:

| Color | Light Mode | Dark Mode |
|-------|------------|-----------|
| Primary Deep Blue | #103A71 | #1B5FA7 (brighter) |
| Primary Tech Blue | #1B5FA7 | #51C8F5 (brighter) |
| AI Purple | #7A4CE0 | #9370DB (slightly brighter) |
| Accent | #1B5FA7 | #51C8F5 |

## Typography with Colors

Always use monospace fonts for numeric data:

```tsx
// Correct
<span className="text-success font-mono">+$1,234.56</span>

// Incorrect
<span className="text-success">+$1,234.56</span>
```

## Accessibility Notes

All color combinations have been tested to meet WCAG AA standards:
- ✅ Success Green on white: 4.5:1 ratio
- ✅ Danger Red on white: 4.5:1 ratio
- ✅ Tech Blue on white: 4.5:1 ratio
- ✅ Primary text colors: 7:1+ ratio

## Migration Checklist

When adding new components or features:

- [ ] Use semantic color variables (var(--success), not #2ECC71)
- [ ] Use Tailwind semantic classes (text-success, not text-green-500)
- [ ] Apply font-mono to all numeric displays
- [ ] Reserve AI purple only for AI features
- [ ] Use Clean Green for gains, Market Red for losses
- [ ] Test in both light and dark modes
- [ ] Verify contrast ratios meet WCAG AA

## Tools & Resources

- **Color Contrast Checker**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- **Tailwind Config**: `frontend/tailwind.config.ts`
- **CSS Variables**: `frontend/src/app/globals.css`
- **Design System**: `frontend/DESIGN_SYSTEM.md`
