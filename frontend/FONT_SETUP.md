# Font Setup Documentation

## Overview

ZiggyAI uses the Inter font family for its UI, self-hosted locally to ensure reliability, performance, and offline capability.

## Font Configuration

### Font Family

- **Primary Font**: Inter (self-hosted)
- **Weights Available**:
  - Regular (400)
  - Medium (500)
  - Semi-Bold (600)
  - Bold (700)

### Font Location

All font files are stored in:

```
frontend/public/fonts/inter/
├── Inter-Regular.woff2    (109 KB)
├── Inter-Medium.woff2     (112 KB)
├── Inter-SemiBold.woff2   (113 KB)
└── Inter-Bold.woff2       (113 KB)
```

## Implementation Details

### 1. Layout Configuration (`src/app/layout.tsx`)

Inter is loaded using Next.js's `next/font/local` with the following configuration:

```typescript
import localFont from "next/font/local";

const inter = localFont({
  src: [
    {
      path: "../../public/fonts/inter/Inter-Regular.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../../public/fonts/inter/Inter-Medium.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "../../public/fonts/inter/Inter-SemiBold.woff2",
      weight: "600",
      style: "normal",
    },
    {
      path: "../../public/fonts/inter/Inter-Bold.woff2",
      weight: "700",
      style: "normal",
    },
  ],
  variable: "--font-inter",
  display: "swap",
});
```

The font variable `--font-inter` is applied to the `<html>` element:

```tsx
<html lang="en" className={inter.variable}>
```

### 2. Tailwind Configuration (`tailwind.config.ts`)

The font is configured with comprehensive fallbacks:

```typescript
fontFamily: {
  sans: [
    'var(--font-inter)',          // Primary font (Inter)
    'system-ui',                   // System default
    '-apple-system',               // macOS/iOS
    'BlinkMacSystemFont',          // macOS
    '"Segoe UI"',                  // Windows
    'Roboto',                      // Android
    '"Helvetica Neue"',            // macOS fallback
    'Arial',                       // Universal fallback
    'sans-serif',                  // Generic fallback
    '"Apple Color Emoji"',         // Emoji support
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
  ],
}
```

### 3. Global Styles (`src/app/globals.css`)

The body element no longer specifies a hardcoded font-family, allowing the Tailwind configuration to handle font rendering:

```css
body {
  background: var(--background);
  color: var(--foreground);
  line-height: 1.5;
  transition:
    background-color var(--transition-normal),
    color var(--transition-normal);
}
```

## Why Self-Hosted Fonts?

### Advantages

1. **Reliability**: No dependency on external CDNs (e.g., Google Fonts)
2. **Performance**: Fonts load from the same origin, reducing DNS lookups and connection overhead
3. **Privacy**: No third-party requests that could track users
4. **Offline Support**: Works in environments without internet access
5. **Consistent Loading**: Guaranteed font availability in all environments

### Previous Issue

The application previously used `next/font/google` to load Inter from Google Fonts, which caused failures:

- "Failed to download `Inter` from Google Fonts"
- "There was an issue establishing a connection while requesting https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"

## Usage in Components

Components automatically inherit the Inter font through Tailwind's default `font-sans` class or by using the system's font stack.

### Examples:

```tsx
// Default usage (inherits from body/html)
<div>This text uses Inter font</div>

// Explicit font weight
<h1 className="font-bold">Bold heading (700)</h1>
<h2 className="font-semibold">Semi-bold heading (600)</h2>
<p className="font-medium">Medium text (500)</p>
<p className="font-normal">Regular text (400)</p>
```

## Fallback Strategy

The font stack ensures graceful degradation:

1. **Inter (Custom)**: Loads from local files
2. **System Fonts**: Uses native fonts if Inter fails to load
3. **Generic Sans-Serif**: Final fallback ensures text remains readable

If all custom fonts fail, the browser will use system-appropriate alternatives (system-ui, -apple-system, etc.) maintaining a professional appearance.

## Testing Font Loading

A Playwright test is included to verify font loading:

```bash
npx playwright test scripts/font-check.spec.ts
```

This test:

- Monitors all font requests
- Checks for HTTP errors (404, 500, etc.)
- Validates that all 4 Inter font weights load successfully
- Confirms no console errors related to fonts

## Maintenance

### Adding New Weights

If additional font weights are needed:

1. Download the font file (`.woff2` format preferred)
2. Place in `public/fonts/inter/`
3. Update `src/app/layout.tsx` to include the new weight
4. Test the change with the font-check test

### Updating Font Version

To update to a newer version of Inter:

1. Download the latest Inter release from https://github.com/rsms/inter/releases
2. Extract the `.woff2` files from the `web` folder
3. Replace the files in `public/fonts/inter/`
4. Test with `npm run dev` and `npm run build`
5. Run the font-check test to verify

### Changing to a Different Font

To use a different font family:

1. Add font files to `public/fonts/<font-name>/`
2. Update `src/app/layout.tsx` with the new font configuration
3. Update `tailwind.config.ts` with the new font variable
4. Update this documentation
5. Test thoroughly across all pages

## Troubleshooting

### Font Not Loading

- Check that font files exist in `public/fonts/inter/`
- Verify file permissions (should be readable)
- Check browser DevTools Network tab for 404 errors
- Run the font-check test

### Font Appears Different Than Expected

- Clear browser cache
- Check that the correct weight is being applied
- Verify `tailwind.config.ts` has the correct font stack
- Inspect computed styles in browser DevTools

### Build Errors

- Ensure font files are committed to Git
- Verify paths in `layout.tsx` are correct relative to the file location
- Check that all referenced weights exist as files

## Performance Considerations

- **Format**: WOFF2 is used for optimal compression (30-50% smaller than WOFF)
- **Loading Strategy**: `display: swap` prevents invisible text during font load
- **Subsetting**: Current fonts include the full Latin character set
- **Preloading**: Next.js automatically optimizes font loading with preload hints

## Browser Support

WOFF2 format is supported by:

- Chrome 36+
- Firefox 39+
- Safari 12+
- Edge 14+
- Opera 23+

This covers 98%+ of users. Legacy browsers will fallback to system fonts.

## Related Files

- `src/app/layout.tsx` - Font loading configuration
- `tailwind.config.ts` - Font family definition and fallbacks
- `src/app/globals.css` - Global styles (no longer includes hardcoded fonts)
- `scripts/font-check.spec.ts` - Automated font loading test
- `public/fonts/inter/` - Font asset directory

## Verification Status

✅ All font files loading successfully (HTTP 200)  
✅ No Google Fonts errors in dev mode  
✅ Production build completes without font warnings  
✅ All 4 font weights (Regular, Medium, SemiBold, Bold) load correctly  
✅ Font fallback stack configured  
✅ Automated test in place

Last verified: 2025-11-13
