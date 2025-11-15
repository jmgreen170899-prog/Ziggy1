# ZiggyContext — Working Snapshot

_Last updated: 2025-10-10 19:58_

This file brings us **back to exactly this working point**: UI stages OK, passcode gate OK, market tab plan in place, backend API + Telegram webhook + scheduler wiring known.

---

## 0) Project layout (assumed paths)

```
C:\ZiggyClean
 ├─ backend
 │   ├─ .env
 │   ├─ app
 │   │   ├─ main.py                 # FastAPI (CORS, routers, scheduler start)
 │   │   ├─ api
 │   │   │   ├─ routes.py           # (optional) general API
 │   │   │   └─ routes_trading.py   # screener + telegram notify + scan enable
 │   │   ├─ services
 │   │   │   └─ screener.py         # demo screener (replace with real logic)
 │   │   └─ tasks
 │   │       ├─ scheduler.py        # APScheduler, background scans
 │   │       └─ telegram.py         # tg_send()
 └─ frontend
     ├─ .env
     └─ src
        ├─ App.jsx                  # stage machine
        ├─ features
        │  ├─ gate/PasscodeGate.jsx # accepts onPassed/onSuccess/onSuceed
        │  ├─ face/ZiggyFace.jsx    # pixel face, eye tracking, timed onDone
        │  ├─ intro/ZiggyIntro.jsx  # type-to-end, caret blinks twice
        │  ├─ chat/ChatUI.jsx       # header with Market button
        │  └─ market/MarketScreen.jsx (planned/added)  # scan + toggle background
        └─ index.css                # typing caret CSS (Intro)
```

---

## 1) Frontend — stage flow and guarantees

- **Stages:** `gate → face → intro → chat (→ market)`
- **Props:** Gate calls **onPassed**, **onSuccess**, **onSuceed** (all supported) to advance.
- **Passcodes:** `52446688` (primary) + `00000000` (master override). _No paste_ enforced.
- **Gate UI:** 8 boxes, keypad, wrong-code shake, optional vibration.
- **Face:** high-contrast neon pixels on black; pupils follow cursor; auto-advance after ~3.5s.
- **Intro:** `"I'm Ziggy"` types once; caret blinks twice at end; then `onDone` → chat.
- **Chat:** header includes a **Market** button (opens the Market screen/stage when wired).

**Known pitfalls we already fixed**

- Duplicate imports (e.g., `useEffect` declared twice).
- Typos on prop names (e.g., `onSuceed`); we tolerate all three names.
- White screen → use ErrorBoundary, fix import casing, guard DOM refs before use.

---

## 2) Backend — FastAPI core

- `app.main`:
  - Loads `.env` via `dotenv.load_dotenv()`.
  - CORS allows `http://localhost:5173`.
  - Includes routers: `api_router` (optional) and **`routes_trading`**.
  - **Startup** calls `start_scheduler()` (APScheduler) so background scans run.
  - Health endpoints: `/` → `{"status":"ok"}`, `/health` → `{"ok": true}`.
- **Telegram webhook**: `POST /telegram/callback` (respects optional `API_ROOT` prefix).
  - Verifies header `X-Telegram-Bot-Api-Secret-Token` **if** `TELEGRAM_WEBHOOK_SECRET` is set.
  - Handles inline buttons `exec:<id>` / `cancel:<id>` and simple text `/exec <id>`/`/cancel <id>`.
  - Uses real trading functions if present; safe stubs otherwise.

---

## 3) Trading endpoints (for UI + Telegram)

**`GET /trade/screener?market=nyse`** → returns list of signals and **also Telegram-notifies** if any.  
**`POST /trade/notify`** body `{"text": "..."}` → push a manual message to Telegram.  
**`GET /trade/scan/status`** → `{"enabled": true/false}` (background alerts)  
**`POST /trade/scan/enable?enabled=true|false`** → toggle scheduler state.

_Background scans_

- APScheduler interval minutes: `ZIGGY_SCAN_INTERVAL_MIN` (default **5**).
- Enabled by `ZIGGY_SCAN_ENABLED=true` (and persisted via Redis if configured).

_Screener_

- `app/services/screener.py` is a **demo** (even-minute BUYs for a few tickers). Replace with Alpaca/Polygon/IBKR/yfinance logic.

---

## 4) Environment variables (back & front)

### backend/.env

```
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...             # your bot
TELEGRAM_CHAT_ID=123456789                   # your chat/user id
TELEGRAM_WEBHOOK_SECRET=fb38c4c1a7e44c1ea094f4b571db0b9b

# Background screener
ZIGGY_SCAN_ENABLED=true
ZIGGY_SCAN_INTERVAL_MIN=5

# Optional Redis for the scan toggle state
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional API root prefix (e.g., /api) shown in logs above
API_ROOT=
```

### frontend/.env

```
VITE_API_URL=http://localhost:8000
```

---

## 5) Start commands (Windows)

**Backend**

```powershell
cd "C:\ZiggyClean\backend"
# optional venv
# python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```powershell
cd "C:\ZiggyClean\frontend"
npm run dev -- --host
```

**One-click launcher (PowerShell)**

```powershell
# Save as C:\ZiggyClean\ziggy-dev.ps1 and run with ExecutionPolicy Bypass
$backend  = "C:\ZiggyClean\backend"
$frontend = "C:\ZiggyClean\frontend"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$backend'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$frontend'; npm run dev -- --host"
Write-Host "Frontend : http://localhost:5173"; Write-Host "Backend  : http://localhost:8000 (health: /health)"
```

---

## 6) Market tab (UI contract)

- `ChatUI` places a **Market** button that calls `onOpenMarket()`.
- `App.jsx` adds stage `"market"`.
- `MarketScreen.jsx` uses:
  - `GET {VITE_API_URL}/trade/screener?market=nyse` → renders signals
  - `GET {VITE_API_URL}/trade/scan/status` → switch state
  - `POST {VITE_API_URL}/trade/scan/enable?enabled=true|false` → toggle

---

## 7) Quick diagnostics

- **If gate doesn’t advance**: confirm prop name; we call all of `onPassed/onSuccess/onSuceed`.
- **If face doesn’t show**: check stage logs and ensure CSS or inline sizes render; guard `getBoundingClientRect()`.
- **If blank white screen**: check console for red; wrap in `ErrorBoundary`; confirm imports & file casing.
- **If Telegram silent**: verify `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in backend `.env`; restart API.
- **If webhook 401**: ensure `X-Telegram-Bot-Api-Secret-Token` matches `TELEGRAM_WEBHOOK_SECRET`.

---

## 8) Immediate next steps

- Replace **demo screener** with your real data source.
- Add confirm buttons in Telegram that hit `/telegram/callback` with `exec:<id>` / `cancel:<id>`.
- Persist events (`mem_event`) and trade audit trail in Postgres; embed snippets in Qdrant.
- Add Playwright smoke test for `gate→face→intro→chat` and a quick API test for `/trade/screener`.

---

## 9) Minimal test payloads

**Manual Telegram notify**

```
POST {VITE_API_URL}/trade/notify
{ "text": "Test alert from Ziggy" }
```

**Simulate callback (curl)**

```
curl -X POST http://localhost:8000/telegram/callback   -H "Content-Type: application/json"   -H "X-Telegram-Bot-Api-Secret-Token: fb38c4c1a7e44c1ea094f4b571db0b9b"   -d '{"callback_query":{"data":"exec:ABC123"}}'
```
