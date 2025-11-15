# ZiggyAI Demo Script

## 🎯 Demo-Ready Checklist

### Pre-Demo Setup

- [ ] Start backend with `DEMO_MODE=true`
- [ ] Start frontend with `VITE_DEMO_MODE=true`
- [ ] Verify demo indicator is showing
- [ ] Test all 3 golden journeys
- [ ] Clear browser cache/cookies

### During Demo

- [ ] Use demo guide for structured flow
- [ ] Point out key features naturally
- [ ] Handle questions gracefully
- [ ] Show error recovery if needed

### Post-Demo

- [ ] Gather feedback
- [ ] Note any issues
- [ ] Schedule follow-up if needed

---

## 🚀 Quick Start

```bash
# Backend
cd backend
DEMO_MODE=true uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
VITE_DEMO_MODE=true npm run dev
```

Visit: http://localhost:3000 (or your dev port)

---

## 📈 Golden Journey 1: Trader

**Duration:** 5-7 minutes  
**Audience:** Active traders, quantitative analysts  
**Key Value:** Real-time signals + paper trading

### Script

**1. Introduction** (30 seconds)

> "Let me show you how a trader would use ZiggyAI for daily trading decisions."

**2. Ticker Selection** (1 minute)

- Navigate to markets/trading page
- Click on AAPL (or search for it)
- **Point out**: Real-time price updates, volume, market cap

**3. Chart & Technical Analysis** (2 minutes)

- Show the chart with price action
- **Highlight**: Moving averages, RSI, MACD indicators
- **Explain**: "These update automatically as new data comes in"

**4. Market Brain Signals** (2 minutes)

- Navigate to signals panel
- **Show**: BUY/SELL signal with confidence score
- **Explain**: "Our AI analyzes multiple factors: technical indicators, market regime, sentiment"
- **Point out**: Signal strength, predicted direction, confidence level

**5. Paper Trading** (1-2 minutes)

- Open paper trading panel
- **Demo**: Place a simulated trade
- **Emphasize**: "This is paper money - safe to experiment"
- Show order confirmation and position update

**6. Portfolio View** (1 minute)

- Navigate to portfolio page
- **Show**: Current positions, P&L, performance metrics
- **Highlight**: Real-time position tracking

---

## 🔍 Golden Journey 2: Analyst/Screener

**Duration:** 4-6 minutes  
**Audience:** Research analysts, portfolio managers  
**Key Value:** Market-wide screening + opportunity discovery

### Script

**1. Introduction** (30 seconds)

> "Now let's see how an analyst uses ZiggyAI to find investment opportunities across the entire market."

**2. Screener Setup** (1 minute)

- Navigate to /screener
- **Show**: Available presets (Momentum, Mean Reversion, etc.)
- **Explain**: "We have pre-built strategies, or you can customize your own"

**3. Run Scan** (1 minute)

- Select "Momentum" preset
- Click "Run Scan"
- **Point out**: "Scanning thousands of stocks in real-time"

**4. Review Results** (2 minutes)

- **Show**: Ranked list with scores
- **Highlight**: Top opportunities (NVDA, AMD, etc.)
- **Explain**: Scoring methodology briefly

**5. Drill Down** (1-2 minutes)

- Click on NVDA
- **Show**: Detailed view with chart, metrics, signals
- **Explain**: "This gives you everything you need to make a decision"

---

## 🤖 Golden Journey 3: Research/Chat

**Duration:** 3-5 minutes  
**Audience:** Anyone wanting AI-powered insights  
**Key Value:** Natural language Q&A + explainable AI

### Script

**1. Introduction** (30 seconds)

> "ZiggyAI has an AI assistant that can answer your market questions."

**2. Ask Simple Question** (1 minute)

- Navigate to /chat
- Type: "What should I know about AAPL?"
- Press Enter
- **Show**: AI thinking, then comprehensive response

**3. Review AI Response** (1-2 minutes)

- **Highlight**: Key points in the answer
- **Point out**: Confidence score, reasoning
- **Show**: Source citations (technical analysis, sentiment, etc.)

**4. Follow-up Question** (1 minute)

- Ask: "What are the risks?"
- **Show**: Context-aware response

**5. Advanced Features** (1 minute, optional)

- **Mention**: Cognitive endpoints (explain, trace)
- **Show**: How AI breaks down its reasoning
- **Explain**: "Transparency is key - you can see why the AI recommends something"

---

## 🎭 Demo Tips

### Do's ✅

- **Start with context**: "In demo mode, we're using deterministic data"
- **Use the guide**: Click the blue button in bottom-right
- **Follow the journey**: Let the guide keep you on track
- **Show confidence**: Know the features well
- **Pause for questions**: Interactive is better
- **Show error recovery**: If something breaks, use it as a teaching moment

### Don'ts ❌

- **Don't apologize for demo mode**: Frame it as "safe to explore"
- **Don't dive too deep**: Keep it high-level unless asked
- **Don't skip the guide**: It ensures you hit all key points
- **Don't rush**: Let features sink in
- **Don't ignore errors**: Address them calmly

---

## 🔧 Troubleshooting

### Demo Indicator Not Showing

```bash
# Check environment variables
echo $VITE_DEMO_MODE  # Should be 'true'
echo $DEMO_MODE       # Backend should be 'true'
```

### Data Not Loading

1. Check backend is running (port 8000)
2. Check frontend is running (port 3000/5173)
3. Open browser console for errors
4. Verify demo endpoints work:
   ```bash
   curl http://localhost:8000/demo/status
   ```

### Blank/White Screen

1. Check browser console for errors
2. Error boundary should show friendly message
3. Try refresh or "Go Home" button

---

## 📊 Key Features to Highlight

### Technical Strengths

- Real-time WebSocket connections
- Multi-provider data failover
- Machine learning signals
- Paper trading simulation
- Market regime detection

### Business Value

- Risk-free strategy testing
- AI-powered decision support
- Market-wide opportunity discovery
- Transparent reasoning (explainable AI)
- Real-time alerts and monitoring

### User Experience

- Clean, modern interface
- Dark mode support
- Responsive design
- Error recovery
- Guided tours

---

## 🎬 Closing

### Strong Close

> "So that's ZiggyAI - whether you're an active trader, an analyst screening markets, or someone looking for AI-powered insights, we've got you covered. And remember, everything we just showed you is available in paper trading mode so you can experiment risk-free."

### Call to Action

- "Would you like to try it yourself?"
- "Do you have any specific use cases in mind?"
- "What questions can I answer?"

### Follow-up

- Provide documentation links
- Schedule follow-up demo if needed
- Get feedback on what they liked/disliked

---

## 📝 Demo Feedback Template

After each demo, fill this out:

**Date:** ********\_\_\_\_********  
**Audience:** ********\_\_\_\_********  
**Journey(s) Shown:** ☐ Trader ☐ Analyst ☐ Research

**What Went Well:**

-
-
-

**What Could Improve:**

-
-
-

**Questions Asked:**

-
-
-

**Next Steps:**

-

---

## 🔐 Security Notes

- Demo mode disables real trading
- Demo mode disables data ingestion
- Demo mode disables system modifications
- Always verify demo mode is active before demos
- Never share production credentials in demos

---

_Last Updated: 2024-12-13_  
_Version: 1.0_
