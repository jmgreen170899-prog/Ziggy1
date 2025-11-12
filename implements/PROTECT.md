# PROTECT.md - Critical Elements That Must Not Be Modified

## Summary
This document lists all public interfaces, storage keys, environment variables, routes, and critical elements that must be preserved during cleanup operations. Any modification to these items could break functionality or lose user data.

---

## 🔒 Backend API Routes (Public Contract)

### Core Routes
- **/** - Root endpoint 
- **/health** - Health check endpoint (critical for frontend discovery)
- **/__debug/routes** - Debug route listing (dev environment)
- **/__debug/env/providers** - Provider status debug endpoint
- **/__debug/env/telegram** - Telegram config debug endpoint

### Chat Routes
- **/complete** - OpenAI-compatible chat completion
- **/chat/health** - Chat service health check
- **/chat/config** - Chat configuration endpoint

### Trading Routes  
- **/trade/health** - Trading service health check
- **/trade/screener** - Market screener data
- **/trade/explain** - Trade explanation service
- **/trade/notify** - Notification endpoints
- **/trade/notify/diag** - Notification diagnostics
- **/trade/notify/probe** - Notification probe
- **/trade/notify/test** - Test notification send
- **/trade/scan/status** - Scan status
- **/trade/scan/enable** - Enable/disable scanning
- **/trade/ohlc** - OHLC price data
- **/trade/orders** - Order management
- **/trade/positions** - Position data
- **/trade/portfolio** - Portfolio overview
- **/trade/execute** - Trade execution
- **/trade/mode/{mode}** - Trading mode configuration
- **/trade/market** - Market trade endpoint

### Market Data Routes
- **/market/overview** - Market overview data
- **/market/breadth** - Market breadth indicators
- **/market/risk-lite** - Risk assessment (lightweight)
- **/market-risk-lite** - Risk assessment (alias)
- **/market/risk** - Full risk assessment
- **/market/calendar** - Market calendar events
- **/market/macro/history** - Macro economic history

### Calendar Routes  
- **/calendar** - Market calendar
- **/holidays** - Market holidays
- **/earnings** - Earnings calendar
- **/economic** - Economic events
- **/schedule** - Market schedule
- **/indicators** - Economic indicators
- **/fred/{series_id}** - FRED economic data

### Alert Routes
- **/alerts/status** - Alert service status
- **/alerts/start** - Start alert service
- **/alerts/stop** - Stop alert service
- **/alerts/ping/test** - Test alert ping
- **/alerts/create** - Create new alert
- **/alerts/sma50** - SMA50 alert setup
- **/alerts/moving-average/50** - Moving average alert
- **/alerts/list** - List active alerts
- **/alerts/production/status** - Production alert status
- **/alerts/history** - Alert history
- **/alerts/{alert_id}** - Alert management (DELETE)
- **/alerts/{alert_id}/enable** - Enable alert (PUT)
- **/alerts/{alert_id}/disable** - Disable alert (PUT)

### Signal Routes
- **/features/{ticker}** - Signal features for ticker
- **/features/bulk** - Bulk signal features
- **/regime** - Current market regime
- **/regime/history** - Market regime history
- **/signal/{ticker}** - Individual signal data
- **/signals/watchlist** - Watchlist signals
- **/signals/signal/{symbol}** - Signal by symbol
- **/trade/plan** - Trading plan generation
- **/status** - General status
- **/config** - Configuration endpoints
- **/execute/trade** - Execute trade
- **/execute/status/{request_id}** - Execution status
- **/execute/history** - Execution history
- **/execute/stats** - Execution statistics
- **/backtest/quick/{ticker}** - Quick backtest
- **/backtest/analysis/{ticker}** - Backtest analysis
- **/trading/backtest** - Trading backtest
- **/backtest** - General backtest
- **/strategy/backtest** - Strategy backtest

### News Routes
- **/news/sources** - News sources
- **/news/headlines** - News headlines
- **/news/filings** - SEC filings
- **/news/filings/recent** - Recent filings
- **/news/sentiment** - News sentiment
- **/news/headwind** - Market headwinds
- **/news/ping** - News service ping

### Crypto Routes
- **/crypto/quotes** - Cryptocurrency quotes
- **/crypto/ohlc** - Crypto OHLC data

### Learning Routes
- **/learning/status** - Learning system status
- **/learning/data/summary** - Learning data summary
- **/learning/rules/current** - Current learning rules
- **/learning/rules/history** - Learning rules history
- **/learning/run** - Run learning system
- **/learning/results/latest** - Latest learning results
- **/learning/results/history** - Learning results history
- **/learning/evaluate/current** - Current evaluation
- **/learning/gates** - Learning gates
- **/learning/calibration/status** - Calibration status
- **/learning/calibration/build** - Build calibration
- **/learning/health** - Learning system health

### Integration Routes
- **/integration/health** - Integration health
- **/decision** - Decision endpoints
- **/enhance** - Enhancement endpoints
- **/context/market** - Market context
- **/rules/active** - Active rules
- **/calibration/apply** - Apply calibration
- **/outcome/update** - Update outcome
- **/integration/status** - Integration status
- **/test/decision** - Test decision

### Explain Routes
- **/explain/events** - Explanation events
- **/explain/events/{event_id}** - Specific event
- **/explain/stats/summary** - Explanation statistics
- **/explain/status** - Explanation status  
- **/explain/stream** - Event stream
- **/explain/test/signal** - Test signal explanation
- **/explain/test/regime** - Test regime explanation

### Web Routes
- **/web/browse/search** - Web browsing search
- **/web/browse** - Web browsing interface

### Telegram Webhook
- **{api_prefix}/telegram/callback** - Telegram webhook callback

---

## 🔑 Environment Variables (Critical Configuration)

### API Keys & Secrets
- **OPENAI_API_KEY** - OpenAI API access
- **AZURE_OPENAI_API_KEY** - Azure OpenAI access
- **HUGGINGFACE_HUB_TOKEN** - HuggingFace access
- **TAVILY_API_KEY** - Tavily search API
- **FRED_API_KEY** - Federal Reserve economic data
- **NEWS_API_KEY** - News API access
- **GNEWS_API_KEY** - Google News API
- **ALPACA_KEY_ID** / **ALPACA_API_KEY** - Alpaca trading API
- **ALPACA_SECRET_KEY** / **ALPACA_API_SECRET** - Alpaca secret
- **POLYGON_API_KEY** / **POLYGON_KEY** / **POLY_API_KEY** - Polygon data
- **QDRANT_API_KEY** - Vector database access
- **TELEGRAM_BOT_TOKEN** - Telegram bot token
- **TELEGRAM_WEBHOOK_SECRET** - Telegram webhook security

### Service Configuration
- **APP_ENV** - Application environment (development/production)
- **ALLOWED_ORIGINS** - CORS allowed origins
- **DATA_PROVIDER** / **DATA_SOURCE** - Data provider selection
- **USE_OPENAI** - OpenAI vs local LLM toggle
- **LOCAL_LLM_MAX_TOKENS** - Local LLM token limit
- **EXPLAIN_ENABLED** - Explanation system toggle
- **TELEGRAM_CHAT_ID** - Telegram chat ID
- **SEC_USER_AGENT** / **USER_AGENT** - HTTP user agent strings

### Provider URLs & Base Paths
- **POLYGON_BASE_URL** / **POLYGON_BASE** - Polygon API base
- **ALPACA_DATA_BASE_URL** / **ALPACA_DATA_BASE** - Alpaca data base
- **LOCAL_LLM_BASE_URL** - Local LLM server URL

---

## 💾 Frontend Storage Keys (Data Persistence)

### Theme & UI Preferences
- **ziggy-theme** - Theme selection (light/dark/system)
- **ziggy_layout_trading_view** - TradingView layout sizes
- **ziggy_settings** - Global settings object

### Market Tab Preferences
- **ziggy_pd** - Period days setting
- **ziggy_auto** - Auto-refresh toggle
- **ziggy_risk** - Show risk toggle
- **ziggy_q** - Search query
- **ziggy_sort** - Sort preference
- **ziggy_dense** - Dense view toggle
- **ziggy_tooltips** - Show tooltips toggle
- **ziggy_since_open** - Since market open toggle
- **ziggy_watchlist** - Watchlist symbols (JSON array)
- **ziggy_wl_mode** - Watchlist mode (all/watchlist)

### API Discovery & Caching
- **ziggy_api_base** - Discovered API base URL
- **ziggy_api_prefix** - API prefix
- **ziggy_api_ts** - API discovery timestamp

### Legacy Keys (Compatibility)
- **ziggy_rr_timeframe** - Risk/return timeframe (legacy)

### Right Rail Preferences
- **ziggy_rr_** prefix - Right rail panel settings

---

## 🎨 CSS Custom Properties (Design System)

### Color Foundations
- **--bg** - Main background color
- **--panel** - Elevated panel background  
- **--surface** - Interactive surface color
- **--surface-hover** - Hover state color
- **--border** - Subtle border color
- **--border-strong** - Prominent border color

### Typography Colors
- **--fg** - Primary text color
- **--fg-muted** - Secondary text color
- **--fg-subtle** - Tertiary text color

### Brand & Accent Colors
- **--accent** - Primary accent color (cyan-blue)
- **--accent-hover** - Accent hover state
- **--accent-fg** - Accent foreground text

### Semantic Colors
- **--success** - Success state color
- **--warning** - Warning state color  
- **--danger** - Error/danger state color

### Trading-Specific Colors
- **--buy** - Bullish/long position color
- **--sell** - Bearish/short position color
- **--candle-up** - Green candlestick color
- **--candle-down** - Red candlestick color

### Chart Elements
- **--grid** - Chart grid line color

---

## ⌨️ Keyboard Shortcuts (User Workflow)

### Global Navigation
- **r** - Refresh data
- **s** - Toggle scan mode
- **/** - Focus search box
- **w** - Open watchlist
- **p** - Pin current item
- **4** - Open charts view

### List Navigation
- **j** - Move down in list
- **k** - Move up in list
- **enter** - Toggle pin/bookmark
- **b** - Bookmark current item
- **o** - Open current item

### Special Key Combinations
- **Ctrl+K** / **Cmd+K** - Command palette (if implemented)
- **Shift+[1-8]** - Tab switching (if implemented)
- **^[1-9]$** - Direct numeric navigation

---

## 🔗 Component Props & Public APIs

### Frontend Component Contracts
- **PasscodeGate** - `onPassed`, `onSuccess`, `onSuceed` callbacks
- **AppShell** - Layout and panel structure
- **TradingViewShell** - Resizable layout persistence
- **MarketTab** - Market data display component
- **TradingTab** - Trading interface component
- **InnerThoughtsTab** - Explanation interface
- **RightRail** - News and market info sidebar

### API Service Contracts
- **api()** function - Core API client
- **api.get()**, **api.post()** etc. - HTTP method helpers
- **testAPI()** - Health check function
- **ziggyAPI** class - Legacy API wrapper

---

## 🎭 DOM IDs & Data Attributes

### Critical DOM Elements
- **root** - React app mount point
- Layout panel IDs used by resizable components
- Modal backdrop and dialog IDs
- Focus trap elements for accessibility

### Password Gate Elements
- **password-face-text** - Passcode entry interface
- Elements maintaining intro/onboarding flow

---

## 📊 Analytics & Tracking IDs

### Event Tracking
- **ziggy:api-changed** - API discovery events
- **ziggy:api-retry** - API retry events  
- **ziggy:hotkey** - Keyboard shortcut events
- **ziggy:status** - Status update events

### Performance Monitoring
- Window performance markers
- API response timing events
- Error tracking and reporting

---

## 🔄 Migration & Compatibility

### Feature Flags
- Build-time feature toggles
- Environment-based feature switches
- Backward compatibility flags

### Version Migration
- Settings schema versioning
- Data format migrations
- API version compatibility

---

## ⚠️ Critical Notes

1. **No Route Changes** - Any modification to route paths will break frontend API calls
2. **No Storage Key Renames** - Will cause user preference loss
3. **No CSS Property Renames** - Will break theming system
4. **No Hotkey Conflicts** - Changing shortcuts breaks user muscle memory
5. **No API Response Schema Changes** - Frontend expects specific data shapes
6. **No Environment Key Changes** - Will break service integrations
7. **Preserve Password Flow** - Critical for security and user onboarding

---

*This protection list was generated during cleanup audit on 2025-10-18*