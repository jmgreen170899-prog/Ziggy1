"""
FREE RSS News Feed Provider
- CNBC Markets RSS (free)
- CoinDesk RSS (free)

Notes:
- Uses short timeouts and a small in-memory TTL cache per feed to reduce gaps on transient errors.
- Adds a simple User-Agent header and structured logging instead of print().
"""

import asyncio
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

import aiohttp

from app.core.config.time_tuning import TIMEOUTS


logger = logging.getLogger("ziggy.rss")


class RSSNewsProvider:
    """Free RSS news feed provider with multiple sources"""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.feeds = {
            "cnbc_markets": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
            "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        }
        # Small in-memory cache per feed (last N items) to avoid gaps on transient errors
        self._cache: dict[str, list[dict[str, Any]]] = {}
        self._cache_ts: dict[str, float] = {}
        self._cache_ttl: float = 120.0  # seconds

    async def fetch_rss_feed(self, url: str, source: str) -> list[dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            if not self.session:
                timeout = aiohttp.ClientTimeout(
                    total=TIMEOUTS["rss_total"],
                    connect=TIMEOUTS["rss_connect"],
                    sock_read=TIMEOUTS["rss_sock_read"],
                )
                headers = {"User-Agent": "ZiggyNewsBot/1.0 (+https://ziggy.local)"}
                self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

            assert self.session is not None  # Type narrowing
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    items = self._parse_rss(content, source)
                    # Update cache
                    self._cache[source] = items[:30]
                    self._cache_ts[source] = time.time()
                    return items
                else:
                    logger.warning(
                        "RSS non-200", extra={"source": source, "status": response.status}
                    )
                    # Fallback to cache if fresh
                    ts = self._cache_ts.get(source, 0)
                    if time.time() - ts < self._cache_ttl:
                        return list(self._cache.get(source, []))
                    return []

        except Exception as e:
            logger.warning("RSS fetch error", extra={"source": source, "error": str(e)})
            ts = self._cache_ts.get(source, 0)
            if time.time() - ts < self._cache_ttl:
                return list(self._cache.get(source, []))
            return []

    def _parse_rss(self, content: str, source: str) -> list[dict[str, Any]]:
        """Parse RSS XML content"""
        try:
            root = ET.fromstring(content)
            items = []

            # Handle different RSS structures
            for item in root.findall(".//item"):
                try:
                    title = item.find("title")
                    link = item.find("link")
                    description = item.find("description")
                    pub_date = item.find("pubDate")

                    if title is not None and link is not None:
                        # Clean description
                        desc_text = ""
                        if description is not None and description.text:
                            desc_text = re.sub(r"<[^>]+>", "", description.text)  # Remove HTML tags
                            desc_text = desc_text.strip()[:500]  # Limit length

                        # Parse date
                        timestamp = time.time()
                        if pub_date is not None and pub_date.text:
                            try:
                                # Parse RFC 2822 format (common in RSS)
                                dt = datetime.strptime(pub_date.text, "%a, %d %b %Y %H:%M:%S %z")
                                timestamp = dt.timestamp()
                            except ValueError:
                                try:
                                    # Alternative format
                                    dt = datetime.strptime(
                                        pub_date.text, "%a, %d %b %Y %H:%M:%S GMT"
                                    )
                                    timestamp = dt.replace(tzinfo=UTC).timestamp()
                                except ValueError:
                                    pass  # Use current time as fallback

                        items.append(
                            {
                                "title": title.text.strip() if title.text else "",
                                "url": link.text.strip() if link.text else "",
                                "summary": desc_text,
                                "published_utc": timestamp,
                                "source": source,
                                "provider": "rss_feed",
                            }
                        )

                except Exception as e:
                    logger.debug("RSS item parse error", extra={"source": source, "error": str(e)})
                    continue

            return items[:20]  # Limit to 20 most recent items

        except Exception as e:
            logger.warning("RSS parsing error", extra={"source": source, "error": str(e)})
            return []

    async def get_all_news(self) -> list[dict[str, Any]]:
        """Get news from all RSS sources"""
        all_news = []

        # Fetch from all sources in parallel
        tasks = []
        for source, url in self.feeds.items():
            task = self.fetch_rss_feed(url, source)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        # Sort by timestamp (newest first)
        all_news.sort(key=lambda x: x.get("published_utc", 0), reverse=True)

        return all_news[:50]  # Return top 50 most recent

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Test function
async def test_rss_news():
    """Test RSS news provider"""
    provider = RSSNewsProvider()

    print("🗞️ Testing FREE RSS News Feeds...")

    # Test individual feeds
    for source, url in provider.feeds.items():
        print(f"\n📰 Testing {source}...")
        news = await provider.fetch_rss_feed(url, source)
        print(f"   ✅ Got {len(news)} articles")
        if news:
            latest = news[0]
            age_hours = (time.time() - latest["published_utc"]) / 3600
            print(f"   📅 Latest: {latest['title'][:80]}...")
            print(f"   ⏰ Age: {age_hours:.1f} hours ago")

    # Test combined feed
    print("\n🔄 Testing combined feed...")
    all_news = await provider.get_all_news()
    print(f"✅ Total articles: {len(all_news)}")

    if all_news:
        print("\n📊 Recent headlines:")
        for i, article in enumerate(all_news[:5]):
            age_hours = (time.time() - article["published_utc"]) / 3600
            print(f"   {i + 1}. {article['title'][:70]}... ({age_hours:.1f}h ago)")

    await provider.close()


if __name__ == "__main__":
    asyncio.run(test_rss_news())
