# ZiggyAI Demo Quick Start Guide

**For Presenters: Get demo-ready in 5 minutes**

## ⚡ Quick Setup

### 1. Start Backend (30 seconds)
```bash
cd backend
DEMO_MODE=true uvicorn app.main:app --reload
```

### 2. Start Frontend (30 seconds)
```bash
cd frontend
VITE_DEMO_MODE=true npm run dev
```

### 3. Open Browser
```
http://localhost:3000
```

You should see:
- ✅ Demo indicator banner at top
- ✅ Floating blue guide button (bottom-right)
- ✅ No errors in console

## 🎯 Demo Flow (Choose One)

### Option A: Trader Journey (5-7 min)
**Best for:** Active traders, quantitative analysts

1. Click floating guide button
2. Select "📈 Trader Journey"
3. Follow steps:
   - Select ticker (AAPL, MSFT, NVDA, TSLA)
   - View live chart
   - Check Market Brain signals
   - Execute paper trade
   - Monitor portfolio

**Key talking points:**
- Real-time market data
- AI-powered signals
- Risk-free paper trading
- Performance tracking

### Option B: Analyst Journey (4-6 min)
**Best for:** Research analysts, portfolio managers

1. Click floating guide button
2. Select "🔍 Analyst Journey"
3. Follow steps:
   - Open screener
   - Choose strategy preset
   - Run market scan
   - Review results
   - Drill into details

**Key talking points:**
- 5,000+ symbols scanned
- Multiple strategies
- Instant results
- Deep analytics

### Option C: Research Journey (3-5 min)
**Best for:** Anyone wanting AI insights

1. Click floating guide button
2. Select "🤖 Research Journey"
3. Follow steps:
   - Open chat
   - Ask market question
   - Review AI response
   - Explore cognitive features
   - Validate with data

**Key talking points:**
- Natural language queries
- AI-powered analysis
- Explainable recommendations
- Data validation

## 🎬 Full Demo Script

See `DEMO_SCRIPT.md` for:
- Detailed talking points
- Timing estimates
- Q&A responses
- Troubleshooting guide

## ✅ Pre-Demo Checklist

**5 Minutes Before:**
- [ ] Backend running (`DEMO_MODE=true`)
- [ ] Frontend running (`VITE_DEMO_MODE=true`)
- [ ] Browser at http://localhost:3000
- [ ] Demo indicator visible
- [ ] Guide button visible
- [ ] No console errors
- [ ] Clear browser cache (if needed)

**Test One Journey:**
- [ ] Click through all 5 steps
- [ ] Verify data loads
- [ ] Confirm no errors
- [ ] Check progress bar works

## 🔧 Troubleshooting

**Demo indicator not showing?**
- Check `VITE_DEMO_MODE=true` is set
- Hard refresh browser (Ctrl+Shift+R)

**Guide button not visible?**
- Check demo mode is active
- Look for blue floating button (bottom-right)
- Try zooming out browser

**Data not loading?**
- Check backend is running
- Visit http://localhost:8000/demo/status
- Should return `{"demo_mode": true, ...}`

**Errors in console?**
- Clear browser cache
- Restart frontend
- Check browser console for details

## 💡 Pro Tips

**Smooth Presentation:**
- Practice one journey before live demo
- Keep DEMO_SCRIPT.md open nearby
- Have backup browser tab ready
- Know the "Go Home" recovery action

**Engagement:**
- Ask audience which journey they want
- Let them choose ticker symbol
- Pause at interesting data points
- Invite questions throughout

**Time Management:**
- 3-5 min = Research Journey
- 4-6 min = Analyst Journey
- 5-7 min = Trader Journey
- Total demo: 12-18 min for all 3

## 🚀 Advanced Options

**Custom Demo Data:**
Edit `backend/app/demo/data_generators.py` to change:
- Ticker symbols
- Price values
- Signal strengths
- News headlines

**Multiple Presenters:**
Each person can follow different journey simultaneously:
- Person 1: Trader Journey
- Person 2: Analyst Journey
- Person 3: Research Journey

**Screen Recording:**
```bash
# Start recording before demo
# Use OBS Studio or similar
# Capture at 1920x1080
# Record audio + screen
```

## 📞 Support

**Questions during demo?**
- Pause and consult DEMO_SCRIPT.md
- Use "I'll follow up on that" if uncertain
- Note question in feedback template

**Technical issues?**
- Use "Go Home" button in error boundary
- Restart browser tab if needed
- Have backup presentation slides ready

## 🎉 After Demo

**Gather Feedback:**
1. Ask which journey was most valuable
2. What features interested them most
3. Any confusion points
4. Suggestions for improvement

**Follow-up:**
- Email demo link
- Share DEMO_SCRIPT.md
- Offer to schedule deeper dive
- Connect on LinkedIn

---

**You're ready to demo! 🚀**

*For detailed script with talking points, see DEMO_SCRIPT.md*  
*For complete Phase 6 documentation, see PHASE_6_DEMO_READY_COMPLETE.md*  
*For all phases summary, see ALL_PHASES_1_TO_6_COMPLETE.md*
