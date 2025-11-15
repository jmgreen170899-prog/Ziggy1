"""
Real-time news streaming service for ZiggyAI
Provides live news updates via WebSocket
"""

import asyncio
import logging
import time
from typing import Any

from app.core.config.time_tuning import BACKOFFS, TIMEOUTS
from app.core.retry import JitterBackoff
from app.core.websocket import connection_manager
from app.services.news import get_default_news
from app.services.rss_news_provider import RSSNewsProvider


logger = logging.getLogger(__name__)


class NewsStreamer:
    """Real-time news streaming service"""

    def __init__(self):
        self.streaming_task: asyncio.Task | None = None
        self.last_update: float = 0
        self.seen_news_ids: set[str] = set()
        self.update_interval = 30  # Check for news every 30 seconds
        self.is_streaming = False
        self.rss_provider = RSSNewsProvider()  # Add RSS provider
        # Backoff used only on errors; normal loop uses update_interval
        self._error_backoff = JitterBackoff(
            min_delay=BACKOFFS["news_min_delay"],
            max_delay=BACKOFFS["news_max_delay"],
            factor=BACKOFFS["news_factor"],
            jitter=BACKOFFS["news_jitter"],
        )

    async def start_streaming(self):
        """Start the news streaming background task"""
        if self.streaming_task and not self.streaming_task.done():
            logger.info("News streaming already running")
            return

        self.is_streaming = True
        # Start the streaming task but don't wait for the first update
        self.streaming_task = asyncio.create_task(self._stream_loop())
        logger.info("News streaming started (background task created)")

        # Don't await the first update - let it run in background
        # This prevents blocking the server startup

    async def stop_streaming(self):
        """Stop the news streaming"""
        self.is_streaming = False
        if self.streaming_task:
            self.streaming_task.cancel()
            from contextlib import suppress

            with suppress(asyncio.CancelledError):
                await self.streaming_task
        logger.info("News streaming stopped")

    async def _enhance_news_with_brain(
        self, news_item: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhance news item with Ziggy's brain intelligence"""
        try:
            # Import brain enhancement system
            from app.services.market_brain.simple_data_hub import (
                DataSource,
                enhance_market_data,
            )

            # Prepare news data for brain enhancement
            news_data = {"news_items": [news_item]}

            # Route through Ziggy's brain for enhancement
            enhanced = enhance_market_data(
                news_data, DataSource.NEWS, news_items=[news_item]
            )

            # Extract enhanced news data
            if isinstance(enhanced, dict):
                enhanced_item = news_item.copy()
                enhanced_item.update(
                    {
                        "brain_enhanced": True,
                        "brain_metadata": enhanced.get("brain_metadata", {}),
                        "sentiment_analysis": enhanced.get("sentiment_analysis", {}),
                        "market_relevance": enhanced.get("market_relevance", 0.5),
                        "extracted_tickers": enhanced.get("extracted_tickers", []),
                        "news_category": enhanced.get("news_category", "general"),
                        "impact_score": enhanced.get("impact_score", 0.5),
                    }
                )

                logger.debug(
                    f"Enhanced news with brain intelligence: {news_item.get('title', '')[:50]}..."
                )
                return enhanced_item
            else:
                # Fallback: add basic brain metadata
                news_item["brain_enhanced"] = True
                news_item["brain_status"] = "basic_enhancement"
                return news_item

        except Exception as e:
            logger.warning(f"Brain enhancement failed for news: {e}")
            # Fallback: return original news with brain attempt marker
            news_item["brain_enhanced"] = False
            news_item["brain_error"] = str(e)
            return news_item

    async def _stream_loop(self):
        """Main news streaming loop.

        Note: In development with auto-reload, hot reload will drop existing sockets.
        This loop is designed to be resilient and non-blocking to WS broadcasting.
        """
        try:
            while self.is_streaming:
                try:
                    # Check for new news
                    await self._check_for_news_updates()

                    # Wait before next check
                    await asyncio.sleep(self.update_interval)
                    # success resets error backoff
                    self._error_backoff.reset()

                except Exception as e:
                    logger.error(f"Error in news streaming loop: {e}")
                    # back off on errors to avoid retry storms
                    delay = self._error_backoff.next_delay(e)
                    await asyncio.sleep(delay or self.update_interval)

        except asyncio.CancelledError:
            logger.info("News streaming loop cancelled")
        except Exception as e:
            logger.error(f"News streaming loop error: {e}")

    async def _check_for_news_updates(self):
        """Check for new news and broadcast updates"""
        try:
            all_items = []

            # Get RSS news (MUCH faster and more recent!)
            try:
                # Add timeout to prevent hanging
                rss_news = await asyncio.wait_for(
                    self.rss_provider.get_all_news(), timeout=TIMEOUTS["async_slow"]
                )

                # Add RSS news (convert format and enhance with brain)
                for rss_item in rss_news:
                    # Convert RSS format to our standard format
                    converted_item = {
                        "id": f"rss_{hash(rss_item['url'])}",
                        "title": rss_item["title"],
                        "summary": rss_item["summary"],
                        "url": rss_item["url"],
                        "ts": rss_item["published_utc"],
                        "source": f"RSS/{rss_item['source']}",
                        "provider": "rss_feed",
                    }

                    # BRAIN ENHANCEMENT: Route news through Ziggy's brain
                    enhanced_item = await self._enhance_news_with_brain(converted_item)
                    all_items.append(enhanced_item)

            except TimeoutError:
                logger.warning("RSS news fetch timed out, continuing with fallback")
            except Exception as e:
                logger.warning(f"RSS news fetch failed: {e}")

            # Also get default news for fallback (with timeout)
            try:
                news_data = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: get_default_news(limit_total=20)
                    ),
                    timeout=TIMEOUTS["websocket_send"],
                )

                # Add default news items
                if news_data and "items" in news_data:
                    all_items.extend(news_data["items"])

            except TimeoutError:
                logger.warning("Default news fetch timed out")
            except Exception as e:
                logger.warning(f"Default news fetch failed: {e}")

            new_items = []
            current_time = time.time()

            # Find new items we haven't seen before
            for item in all_items:
                item_id = item.get("id", "")
                if item_id and item_id not in self.seen_news_ids:
                    # Only include recent news (within last 24 hours)
                    item_ts = item.get("ts", 0)
                    if item_ts is None or current_time - item_ts < 86400:  # 24 hours
                        new_items.append(item)
                        self.seen_news_ids.add(item_id)

            # Limit memory usage - keep only recent IDs
            if len(self.seen_news_ids) > 1000:
                # Keep only the most recent 500 IDs
                recent_items = sorted(
                    all_items, key=lambda x: x.get("ts", 0), reverse=True
                )[:500]
                self.seen_news_ids = {
                    item.get("id", "") for item in recent_items if item.get("id")
                }

            # Broadcast new items
            if new_items:
                await self._broadcast_news_updates(new_items)
                logger.info(f"Broadcasted {len(new_items)} new news items")

        except Exception as e:
            logger.error(f"Error checking for news updates: {e}")

    async def _broadcast_news_updates(self, news_items: list):
        """Broadcast news updates to connected clients"""
        try:
            for item in news_items:
                # Create news update message
                message = {
                    "type": "news_update",
                    "data": {
                        "id": item.get("id"),
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", ""),
                        "published": item.get("published"),
                        "tickers": item.get("tickers", []),
                        "image": item.get("image"),
                        "timestamp": item.get("ts", time.time()),
                    },
                    "timestamp": time.time(),
                }

                # Broadcast to all news feed connections
                await connection_manager.broadcast_to_type(message, "news_feed")

                # Small delay to avoid overwhelming clients
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error broadcasting news updates: {e}")


# Global news streamer instance
news_streamer = NewsStreamer()


async def start_news_streaming():
    """Start news streaming (call during app startup)"""
    await news_streamer.start_streaming()


async def stop_news_streaming():
    """Stop news streaming (call during app shutdown)"""
    await news_streamer.stop_streaming()
    await news_streamer.rss_provider.close()  # Clean up RSS provider
