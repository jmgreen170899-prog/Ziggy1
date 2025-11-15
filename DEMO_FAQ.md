# ZiggyAI Demo FAQ

**Common questions and answers for demo presenters**

## Setup Questions

### Q: How do I enable demo mode?

**A:** Set environment variables:

```bash
# Backend
DEMO_MODE=true uvicorn app.main:app

# Frontend
VITE_DEMO_MODE=true npm run dev
```

### Q: Can I run demos without a database?

**A:** Yes! Demo mode uses in-memory demo data generators. No database, Redis, or external APIs required.

### Q: How do I verify demo mode is active?

**A:** Check these indicators:

- Demo indicator banner at top of UI
- Backend: `curl http://localhost:8000/demo/status` returns `{"demo_mode": true}`
- No real API calls in network tab
- Deterministic demo data

### Q: Can I use custom tickers in demo mode?

**A:** Demo data supports AAPL, MSFT, NVDA, TSLA, GOOGL by default. Edit `backend/app/demo/data_generators.py` to add more.

## Demo Flow Questions

### Q: Which journey should I start with?

**A:** Depends on audience:

- **Traders** → Trader Journey (5-7 min)
- **Analysts** → Analyst Journey (4-6 min)
- **General** → Research Journey (3-5 min)
- **Full demo** → All three (12-18 min)

### Q: Can I skip steps in a journey?

**A:** Yes, use Previous/Next buttons in journey container. But recommended to show all steps for complete story.

### Q: What if someone asks a question I can't answer?

**A:** Professional responses:

- "Great question! Let me note that and follow up after the demo."
- "I can show you that feature in the next section."
- "That's in our roadmap. Let me connect you with the team."

### Q: Can multiple people demo simultaneously?

**A:** Yes! Demo mode is stateless. Each user can follow different journeys independently.

## Technical Questions

### Q: Is demo data real or fake?

**A:** Demo data is **realistic but synthetic**. Generated deterministically to ensure consistent demos. No real market data or live feeds.

### Q: Can I execute real trades in demo mode?

**A:** No, all trading actions are disabled when `DEMO_MODE=true`. Shows paper trading interface but doesn't execute.

### Q: Does demo mode require internet?

**A:** No! Runs entirely locally. Perfect for:

- Conference demos (unreliable WiFi)
- Air-gapped environments
- Offline presentations

### Q: How do I customize demo data?

**A:** Edit `backend/app/demo/data_generators.py`:

```python
def get_demo_market_data(ticker: str = "AAPL"):
    return {
        "ticker": ticker,
        "price": 180.50,  # Change this
        "change": 2.34,   # Change this
        # ...
    }
```

## Error & Recovery Questions

### Q: What if I get an error during demo?

**A:** Error boundary provides recovery options:

1. Click "Refresh" to restart current view
2. Click "Go Home" to return to main page
3. Check console for details (dev mode only)

### Q: What if the demo freezes or hangs?

**A:** Quick recovery steps:

1. Press Esc key (exits current journey)
2. Click browser refresh (Ctrl+R)
3. Restart journey from guide button

### Q: What if data doesn't load?

**A:** Troubleshooting:

1. Check backend is running: `curl http://localhost:8000/health`
2. Check demo status: `curl http://localhost:8000/demo/status`
3. Clear browser cache (Ctrl+Shift+Delete)
4. Hard refresh (Ctrl+Shift+R)

### Q: Can I recover from a crash mid-demo?

**A:** Yes! Options:

- Refresh browser (journey state resets)
- Start different journey
- Show static slides as backup
- Move to Q&A section early

## Presentation Questions

### Q: How long should a demo take?

**A:** Recommended timings:

- **Quick demo**: 3-5 min (one journey)
- **Standard demo**: 10-15 min (two journeys)
- **Full demo**: 20-25 min (all three journeys + Q&A)
- **Deep dive**: 30-45 min (journeys + code walkthrough)

### Q: Should I let audience drive?

**A:** Depends on format:

- **Executive demo**: You drive, smooth story
- **Technical demo**: Let them explore
- **Sales demo**: Mix of both
- **Training**: Hands-on for everyone

### Q: What if I need to pause mid-demo?

**A:** Demo pauses safely:

- Journey state preserved
- Can answer questions
- Resume from same step
- Or start fresh journey

### Q: How do I handle competitive questions?

**A:** Professional approach:

- Focus on ZiggyAI strengths
- "We'd be happy to discuss comparisons offline"
- "Here's what makes us unique..."
- Don't disparage competitors

## Integration Questions

### Q: Can I integrate this into our app?

**A:** Yes! Two approaches:

1. **Components**: Import journey components
2. **API Client**: Use typed API client
3. **Demo Mode**: Enable in your environment

See `frontend/API_CLIENT_README.md` and `frontend/MIGRATION_EXAMPLE.md`.

### Q: Is this the production system?

**A:** Demo mode is **same codebase**, but:

- Uses synthetic data
- Disables dangerous actions
- Optimized for presentation
- Can switch to production mode

### Q: Can we white-label the demo?

**A:** Yes! Customize:

- Company logo
- Color scheme
- Ticker symbols
- Demo journeys
- All in `frontend/src/config/demo.ts`

## Data Questions

### Q: Where does demo data come from?

**A:** Generated by `backend/app/demo/data_generators.py`:

- Deterministic algorithms
- Realistic patterns
- Consistent across runs
- Configurable values

### Q: Can demo data be updated?

**A:** Yes! Edit generators:

- Market data
- Portfolio positions
- Trading signals
- News articles
- Screener results
- AI responses

### Q: How realistic is the demo data?

**A:** Very realistic:

- Based on real market patterns
- Proper price movements
- Valid technical indicators
- Authentic-looking news
- Reasonable performance metrics

## Security Questions

### Q: Is demo mode secure for public demos?

**A:** Yes! Demo mode:

- Disables real trading
- Uses synthetic data only
- No actual API keys used
- No database connections
- No external calls

### Q: Can someone hack demo mode?

**A:** Very low risk:

- No real accounts
- No real money
- No sensitive data exposed
- All actions sandboxed
- Frontend validation

### Q: Should I enable auth in demos?

**A:** Recommended: **No**

- Adds friction
- Slows demo flow
- Can confuse audience
- Enable for production only

## Performance Questions

### Q: Will demo mode lag on my laptop?

**A:** No, demo mode is lightweight:

- No database queries
- No external API calls
- In-memory data only
- Fast response times (< 100ms)

### Q: Can I demo on slow internet?

**A:** Yes! Demo mode works **offline**:

- No internet required
- All data local
- Perfect for conferences
- No network dependencies

### Q: How many concurrent demos can I run?

**A:** Unlimited:

- Each demo is independent
- No shared state
- Stateless data generators
- Scales to 100+ users

## Feedback Questions

### Q: How do I gather feedback after demos?

**A:** Use feedback template:

1. Which journey was most valuable?
2. What features interested you?
3. Any confusion points?
4. Would you recommend this?
5. Next steps?

### Q: Where should I direct technical questions?

**A:** Resources:

- Email: support@ziggyai.com (example)
- Docs: See all markdown files
- Code: GitHub repo
- Slack: Internal channel

### Q: How do I improve my demos?

**A:** Best practices:

1. Record yourself demoing
2. Watch for awkward pauses
3. Practice transitions
4. Time each journey
5. Get colleague feedback
6. Iterate on script

## Customization Questions

### Q: Can I add my own journeys?

**A:** Yes! See `frontend/src/components/journeys/` for examples. Follow the pattern:

1. Create `MyJourney.tsx`
2. Define 5 steps
3. Add to `DemoGuide.tsx`
4. Test thoroughly

### Q: Can I change journey order?

**A:** Yes! Edit `frontend/src/components/demo/DemoGuide.tsx`:

```typescript
const journeys = [
  { name: 'research', ... },  // Now first
  { name: 'trader', ... },    // Now second
  { name: 'analyst', ... },   // Now third
];
```

### Q: Can I skip the demo guide?

**A:** Yes, but not recommended. To hide:

- Set `VITE_DEMO_HIDE_GUIDE_BUTTON=true`
- Or comment out `<DemoGuide />` in app

---

**Still have questions?**

- See `DEMO_SCRIPT.md` for detailed script
- See `QUICKSTART_DEMO.md` for setup guide
- See `PHASE_6_DEMO_READY_COMPLETE.md` for technical details
- See `ALL_PHASES_1_TO_6_COMPLETE.md` for complete overview

**Ready to demo! 🎉**
