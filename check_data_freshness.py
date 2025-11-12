import time
from datetime import datetime

from backend.app.services.news import get_default_news
from backend.app.services.provider_factory import get_price_provider


print("🔍 CHECKING DATA FRESHNESS...")
print("=" * 50)

# Check news freshness
print("📰 NEWS DATA:")
try:
    news = get_default_news(limit_total=3)
    current_time = time.time()
    if news and "items" in news:
        for i, item in enumerate(news["items"][:3]):
            ts = item.get("ts")
            if ts:
                age_minutes = (current_time - ts) / 60
                title = item.get("title", "No title")[:60] + "..."
                print(f"  Item {i+1}: {age_minutes:.1f} minutes old - {title}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("📊 MARKET DATA PROVIDERS:")
try:
    provider = get_price_provider()
    print(f'  Primary provider: {provider.__class__.__name__ if provider else "None"}')

    # Test market data freshness
    import yfinance as yf

    ticker = yf.Ticker("AAPL")
    info = ticker.info
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    market_time = info.get("regularMarketTime")

    if market_time:
        market_dt = datetime.fromtimestamp(market_time)
        age_minutes = (datetime.now() - market_dt).total_seconds() / 60
        print(f"  AAPL price: ${current_price} (updated {age_minutes:.1f} minutes ago)")
    else:
        print(f"  AAPL price: ${current_price} (timestamp not available)")

except Exception as e:
    print(f"  Error: {e}")

print()
print("🆓 FREE DATA IMPROVEMENT OPTIONS:")
print("=" * 50)
print("📰 NEWS SOURCES (FREE):")
print("  ✅ Current: Polygon.io aggregated news (good coverage)")
print("  🔄 Add: Reddit Financial APIs (social sentiment)")
print("  🔄 Add: Google News RSS feeds (broader coverage)")
print("  🔄 Add: Yahoo Finance news (free, good quality)")
print("  🔄 Add: NewsAPI.org free tier (100 req/day)")

print()
print("📊 MARKET DATA (FREE):")
print("  ✅ Current: Yahoo Finance (15-20min delayed)")
print("  🔄 Upgrade: Alpha Vantage free tier (5 API calls/min)")
print("  🔄 Upgrade: IEX Cloud free tier (50k credits/month)")
print("  🔄 Add: Finnhub free tier (60 calls/min)")
print("  ⚡ Real-time: Would need paid subscriptions")

print()
print("🚀 RECOMMENDED FREE IMPROVEMENTS:")
print("  1. Add Yahoo Finance news RSS feeds")
print("  2. Implement IEX Cloud for real-time quotes (free tier)")
print("  3. Add Reddit financial subreddit sentiment")
print("  4. Use multiple news sources for better coverage")
print("  5. Cache and aggregate data to reduce API calls")
