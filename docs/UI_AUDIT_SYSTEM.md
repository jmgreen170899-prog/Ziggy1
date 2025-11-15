# 🎯 ZiggyAI UI Audit System

Comprehensive UI audit system with Playwright automation, Lighthouse performance testing, and intelligent report generation.

## 🚀 Quick Start

```powershell
# 1. Install dependencies
.\scripts\setup_ui_audit.ps1 -InstallDeps

# 2. Start ZiggyAI servers
cd backend && uvicorn app.main:app --reload     # Terminal 1
cd frontend && npm run dev                      # Terminal 2

# 3. Run complete audit
.\scripts\setup_ui_audit.ps1 -RunAudit
```

## 📊 What Gets Audited

### 14 ZiggyAI Routes

- Dashboard (`/`)
- Chat (`/chat`)
- Market (`/market`)
- Alerts (`/alerts`)
- Portfolio (`/portfolio`)
- Trading (`/trading`)
- Predictions (`/predictions`)
- News (`/news`)
- Paper Trading (`/paper-trading`)
- Paper Status (`/paper/status`)
- Live Data (`/live`)
- Crypto (`/crypto`)
- Learning (`/learning`)
- Account (`/account`)

### Data Quality Metrics

- **Data Cards/Rows Count**: Live content verification
- **NaN/Undefined Values**: Broken data display detection
- **Missing Fields**: Empty data element identification
- **Stale Timestamps**: Data freshness validation (>1 hour old)
- **Empty States**: Proper fallback handling

### Layout Health

- **Overflow Elements**: Horizontal scrolling issues
- **Hidden Elements**: Invisible content detection
- **Responsive Issues**: Mobile touch target validation
- **Reflow Count**: Layout stability monitoring

### Performance Analysis

- **Lighthouse Scores**: Performance, Accessibility, Best Practices, SEO
- **Core Web Vitals**: FCP, LCP, CLS, TBT measurements
- **Load Times**: DOM, Network, Data loading metrics
- **Console Errors**: JavaScript runtime error tracking

## 📸 Output Artifacts

### Screenshots

- `artifacts/ui/{tab-name}.png` - Full-page screenshots of each route
- Automated capture after data loading completes

### Raw Data

- `artifacts/ui/ui_audit.json` - Complete Playwright audit results
- `artifacts/ui/lighthouse_summary.json` - Lighthouse performance data
- `artifacts/ui/lh_{tab-name}.json` - Individual Lighthouse reports

### Generated Report

- `ui_improvements.md` - Prioritized improvement recommendations
  - **P0 (Critical)**: NaN values, layout overflow, console errors
  - **P1 (High)**: Missing fields, stale data, responsive issues
  - **P2 (Medium)**: Performance optimization, accessibility, SEO

## 🛠️ Development Tools

### UX Debug Overlay

Live development overlay for real-time monitoring:

```typescript
// Add to your layout.tsx for development
import UXDebugOverlay from '@/components/debug/UXDebugOverlay';

export default function Layout({ children }) {
  return (
    <>
      {children}
      <UXDebugOverlay />
    </>
  );
}
```

**Features:**

- **API Performance**: Real-time latency P50/P95 tracking
- **Data Freshness**: TTL and staleness indicators
- **Layout Health**: Reflow count and overflow detection
- **Error Tracking**: Console errors and network failures
- **Toggle**: `Ctrl+Shift+D` to show/hide

### Manual Audit Commands

```powershell
# Individual components
pnpm playwright test scripts/ui_audit.spec.ts    # Playwright only
.\scripts\run_lighthouse.ps1                     # Lighthouse only
python scripts/generate_ui_report.py             # Report only

# Full workflow
.\scripts\setup_ui_audit.ps1 -RunAudit          # Complete audit
```

## 📋 Report Format

### Executive Summary

```markdown
## 📊 Executive Summary

- **Total Tabs Audited:** 14
- **Healthy Tabs:** 12/14 (86%)
- **Total Issues:** 23
- **Critical Issues (P0):** 2
- **Status:** 🟡 Needs Attention
```

### Per-Tab Analysis

```markdown
## 🟡 Market (`/market`)

**Screenshot:** `artifacts/ui/market.png`

### 📊 What's Shown (Live Data)

- **Data Cards:** 8
- **Data Rows:** 24
- **Load Times:** DOM: 🟢 245ms, Data: 🟡 1.2s

### ⚠️ Issues Detected (5 total)

**P1 - Missing Data Fields** (3 found)

- div.price-display
- span.change-percent

### 🔧 Actionable Fixes

- Add loading skeletons for missing price data
- Implement graceful degradation for API failures
```

## 🎯 Best Practices

### Running Audits

1. **Clean State**: Clear browser cache and storage
2. **Stable Environment**: Ensure backend/frontend are fully loaded
3. **Consistent Data**: Use same test data for comparative audits
4. **Regular Schedule**: Run audits after major UI changes

### Interpreting Results

- **P0 Issues**: Fix immediately (break user experience)
- **P1 Issues**: Fix within 1 week (impact usability)
- **P2 Issues**: Fix within 1 month (polish and optimization)

### Performance Targets

- **Lighthouse Performance**: >90% (excellent), >70% (good)
- **Accessibility**: >95% (WCAG compliance)
- **Load Times**: <1s DOM, <3s data loading
- **Console Errors**: 0 (clean runtime)

## 🔧 Troubleshooting

### Common Issues

**Playwright Test Failures**

```bash
# Install browsers
npx playwright install

# Debug mode
npx playwright test --debug scripts/ui_audit.spec.ts
```

**Lighthouse Installation**

```bash
# Global install
npm install -g lighthouse

# Verify installation
lighthouse --version
```

**Server Connection Issues**

- Ensure backend is running on `localhost:8000`
- Ensure frontend is running on `localhost:3000`
- Check firewall/antivirus blocking connections

**Missing Screenshots**

- Verify `artifacts/ui/` directory permissions
- Check disk space availability
- Ensure Playwright has browser permissions

This audit system provides enterprise-grade UI monitoring and optimization guidance for ZiggyAI's complex financial interface.
