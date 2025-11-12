import asyncio
import time
from typing import Any, cast

from app.services.rss_news_provider import RSSNewsProvider


class FakeResponse:
    def __init__(self, status=500, text=""):
        self.status = status
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return self._text


class FakeSession:
    def __init__(self, status=500, text=""):
        self._resp = FakeResponse(status=status, text=text)

    def get(self, url):  # aiohttp returns an awaitable context manager; our FakeResponse matches
        return self._resp


def test_rss_uses_cache_on_non200():
    provider = RSSNewsProvider()
    source = "cnbc_markets"
    url = provider.feeds[source]

    # Seed cache with one item and fresh timestamp
    cached_item = {
        "title": "Cached",
        "url": "http://example.com",
        "summary": "",
        "published_utc": time.time(),
        "source": source,
        "provider": "rss_feed",
    }
    provider._cache[source] = [cached_item]
    provider._cache_ts[source] = time.time()

    # Force non-200 response -> should fallback to cache
    provider.session = cast(Any, FakeSession(status=500, text=""))
    items = asyncio.run(provider.fetch_rss_feed(url, source))

    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]["title"] == "Cached"


def test_rss_cache_expires_then_empty_on_error():
    provider = RSSNewsProvider()
    source = "coindesk"
    url = provider.feeds[source]

    cached_item = {
        "title": "Old",
        "url": "http://example.com/old",
        "summary": "",
        "published_utc": time.time() - 3600,
        "source": source,
        "provider": "rss_feed",
    }
    provider._cache[source] = [cached_item]
    # Expire cache
    provider._cache_ts[source] = time.time() - (provider._cache_ttl + 5)

    provider.session = cast(Any, FakeSession(status=500, text=""))
    items = asyncio.run(provider.fetch_rss_feed(url, source))

    assert items == []
