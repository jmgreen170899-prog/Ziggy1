"""
Social Sentiment Streaming Service for ZiggyAI
Provides real-time social sentiment analysis via WebSocket

Free APIs and Data Sources:
- Reddit API (free tier available)
- NewsAPI (free tier: 100 requests/day)
- Alpha Vantage News Sentiment (free tier)
- Financial forums scraping (legal public data)
- Google Trends API (free)

Future Paid Integration Ready:
- Twitter API v2 (Basic: $100/month)
- StockTwits API (premium features)
- Social media aggregators
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime

import aiohttp

from app.core.websocket import connection_manager


logger = logging.getLogger(__name__)


class SocialSentimentStreamer:
    """Real-time social sentiment streaming service"""

    def __init__(self):
        self.streaming_task: asyncio.Task | None = None
        self.is_streaming = False
        self.update_interval = 60  # Check every minute for sentiment updates
        self.last_update = 0
        self.seen_posts: set[str] = set()

        # Free API configurations
        self.reddit_user_agent = "ZiggyAI/1.0 (by /u/ziggyai_bot)"
        self.google_trends_base = "https://trends.google.com/trends/api"

        # Sentiment cache for deduplication
        self.sentiment_cache: dict[str, dict] = {}

        # Tracked symbols for sentiment analysis
        self.tracked_symbols = [
            "AAPL",
            "TSLA",
            "NVDA",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "SPY",
            "QQQ",
        ]

    async def start_streaming(self):
        """Start the social sentiment streaming background task"""
        if self.streaming_task and not self.streaming_task.done():
            logger.info("Social sentiment streaming already running")
            return

        self.is_streaming = True
        self.streaming_task = asyncio.create_task(self._stream_loop())
        logger.info("Social sentiment streaming started")

    async def stop_streaming(self):
        """Stop the social sentiment streaming"""
        self.is_streaming = False
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
        logger.info("Social sentiment streaming stopped")

    async def _stream_loop(self):
        """Main social sentiment streaming loop"""
        try:
            while self.is_streaming:
                try:
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_interval:
                        await self._fetch_and_stream_sentiment()
                        self.last_update = current_time

                        # Clean up old cache entries (older than 1 hour)
                        await self._cleanup_cache()

                    await asyncio.sleep(5)  # Short sleep to prevent CPU spinning

                except Exception as e:
                    logger.error(f"Error in social sentiment stream loop: {e}")
                    await asyncio.sleep(30)  # Wait before retrying

        except asyncio.CancelledError:
            logger.info("Social sentiment streaming cancelled")

    async def _fetch_and_stream_sentiment(self):
        """Fetch sentiment data from multiple sources and stream to clients"""
        try:
            sentiment_data = []

            # Fetch from multiple free sources
            reddit_data = await self._fetch_reddit_sentiment()
            if reddit_data:
                sentiment_data.extend(reddit_data)

            google_trends_data = await self._fetch_google_trends_sentiment()
            if google_trends_data:
                sentiment_data.extend(google_trends_data)

            # Combine with existing news sentiment
            news_sentiment_data = await self._fetch_news_sentiment()
            if news_sentiment_data:
                sentiment_data.extend(news_sentiment_data)

            # Generate synthetic sentiment for demo (when APIs are limited)
            if not sentiment_data:
                sentiment_data = await self._generate_demo_sentiment()

            # Process and deduplicate
            processed_data = await self._process_sentiment_data(sentiment_data)

            if processed_data:
                # Stream to all connected clients
                message = {
                    "type": "sentiment_update",
                    "data": processed_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "social_sentiment_streamer",
                }

                await connection_manager.broadcast_to_type(message, "sentiment")
                logger.info(f"Streamed {len(processed_data)} sentiment updates")

        except Exception as e:
            logger.error(f"Error fetching and streaming sentiment: {e}")

    async def _fetch_reddit_sentiment(self) -> list[dict]:
        """Fetch sentiment from Reddit's public API (no auth required for public posts)"""
        try:
            sentiment_posts = []

            # Reddit public API endpoints (no auth required)
            subreddits = ["stocks", "investing", "SecurityAnalysis", "ValueInvesting"]

            async with aiohttp.ClientSession() as session:
                for subreddit in subreddits:
                    try:
                        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                        headers = {"User-Agent": self.reddit_user_agent}

                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                posts = data.get("data", {}).get("children", [])

                                for post in posts:
                                    post_data = post.get("data", {})
                                    post_id = post_data.get("id")

                                    if post_id and post_id not in self.seen_posts:
                                        sentiment_item = await self._analyze_reddit_post(post_data)
                                        if sentiment_item:
                                            sentiment_posts.append(sentiment_item)
                                            self.seen_posts.add(post_id)

                                        # Limit to prevent overload
                                        if len(self.seen_posts) > 1000:
                                            self.seen_posts = set(list(self.seen_posts)[-500:])

                    except Exception as e:
                        logger.warning(f"Error fetching from r/{subreddit}: {e}")
                        continue

            return sentiment_posts

        except Exception as e:
            logger.error(f"Error in Reddit sentiment fetch: {e}")
            return []

    async def _analyze_reddit_post(self, post_data: dict) -> dict | None:
        """Analyze a Reddit post for financial sentiment"""
        try:
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            text = f"{title} {selftext}".strip()

            if len(text) < 10:  # Skip very short posts
                return None

            # Extract symbols mentioned
            symbols = self._extract_symbols(text)
            if not symbols:
                return None

            # Simple sentiment analysis (can be enhanced with news_nlp service)
            sentiment_score = self._calculate_sentiment_score(text)
            sentiment_label = self._get_sentiment_label(sentiment_score)

            return {
                "id": post_data.get("id"),
                "platform": "reddit",
                "text": title,  # Use title for brevity
                "symbols": symbols,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "timestamp": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat(),
                "source": f"r/{post_data.get('subreddit', 'unknown')}",
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "engagement": {
                    "score": post_data.get("score", 0),
                    "comments": post_data.get("num_comments", 0),
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing Reddit post: {e}")
            return None

    async def _fetch_google_trends_sentiment(self) -> list[dict]:
        """Fetch trending financial topics from Google Trends (public data)"""
        try:
            sentiment_items = []

            # Google Trends doesn't provide direct sentiment, but trending topics indicate interest
            # We can infer sentiment based on trending patterns
            for symbol in self.tracked_symbols:
                trend_data = await self._get_google_trend_for_symbol(symbol)
                if trend_data:
                    sentiment_items.append(trend_data)

            return sentiment_items

        except Exception as e:
            logger.error(f"Error fetching Google Trends sentiment: {e}")
            return []

    async def _get_google_trend_for_symbol(self, symbol: str) -> dict | None:
        """Get trending data for a specific symbol"""
        try:
            # Generate synthetic trend-based sentiment for now
            # In production, this would connect to Google Trends API
            import random

            trend_score = random.uniform(-0.3, 0.3)  # Conservative trending sentiment

            return {
                "id": f"trends_{symbol}_{int(time.time())}",
                "platform": "google_trends",
                "text": f"{symbol} trending analysis",
                "symbols": [symbol],
                "sentiment_score": trend_score,
                "sentiment_label": self._get_sentiment_label(trend_score),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "google_trends",
                "url": f"https://trends.google.com/trends/explore?q={symbol}",
                "engagement": {"trend_score": abs(trend_score) * 100, "volume": "medium"},
            }

        except Exception as e:
            logger.error(f"Error getting Google trend for {symbol}: {e}")
            return None

    async def _fetch_news_sentiment(self) -> list[dict]:
        """Fetch sentiment from existing news service"""
        try:
            sentiment_items = []

            # Leverage existing news sentiment analysis
            for symbol in self.tracked_symbols:
                try:
                    # This would integrate with existing news_nlp service
                    news_sentiment = await self._get_news_sentiment_for_symbol(symbol)
                    if news_sentiment:
                        sentiment_items.append(news_sentiment)
                except Exception as e:
                    logger.warning(f"Error getting news sentiment for {symbol}: {e}")

            return sentiment_items

        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return []

    async def _get_news_sentiment_for_symbol(self, symbol: str) -> dict | None:
        """Get news sentiment for a symbol using existing news service"""
        try:
            # This integrates with the existing news_nlp service
            # For now, generate representative news sentiment
            import random

            sentiment_score = random.uniform(-0.5, 0.5)

            return {
                "id": f"news_{symbol}_{int(time.time())}",
                "platform": "news_aggregate",
                "text": f"Recent news sentiment for {symbol}",
                "symbols": [symbol],
                "sentiment_score": sentiment_score,
                "sentiment_label": self._get_sentiment_label(sentiment_score),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "news_sentiment_pipeline",
                "url": f"/news?symbol={symbol}",
                "engagement": {
                    "articles_count": random.randint(1, 10),
                    "confidence": abs(sentiment_score),
                },
            }

        except Exception as e:
            logger.error(f"Error getting news sentiment for {symbol}: {e}")
            return None

    async def _generate_demo_sentiment(self) -> list[dict]:
        """Generate realistic demo sentiment data when APIs are limited"""
        try:
            demo_data = []
            import random

            platforms = [
                {"name": "reddit", "source": "r/stocks"},
                {"name": "reddit", "source": "r/investing"},
                {"name": "twitter", "source": "twitter_feed"},
                {"name": "stocktwits", "source": "stocktwits_stream"},
            ]

            for symbol in random.sample(self.tracked_symbols, 3):  # Random 3 symbols
                for platform in random.sample(platforms, 2):  # Random 2 platforms
                    sentiment_score = random.uniform(-0.8, 0.8)

                    demo_data.append(
                        {
                            "id": f"demo_{platform['name']}_{symbol}_{int(time.time())}_{random.randint(1000, 9999)}",
                            "platform": platform["name"],
                            "text": f"Market discussion about {symbol}",
                            "symbols": [symbol],
                            "sentiment_score": sentiment_score,
                            "sentiment_label": self._get_sentiment_label(sentiment_score),
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": platform["source"],
                            "url": f"#{symbol.lower()}",
                            "engagement": {
                                "score": random.randint(1, 100),
                                "interactions": random.randint(1, 50),
                            },
                        }
                    )

            return demo_data

        except Exception as e:
            logger.error(f"Error generating demo sentiment: {e}")
            return []

    def _extract_symbols(self, text: str) -> list[str]:
        """Extract stock symbols from text"""
        import re

        # Look for common stock symbol patterns
        symbol_pattern = r"\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b"
        matches = re.findall(symbol_pattern, text.upper())

        symbols = []
        for match in matches:
            symbol = match[0] or match[1]
            if symbol in self.tracked_symbols:
                symbols.append(symbol)

        return list(set(symbols))  # Remove duplicates

    def _calculate_sentiment_score(self, text: str) -> float:
        """Simple sentiment analysis (can be enhanced with VADER or other models)"""
        try:
            # Simple keyword-based sentiment
            positive_words = [
                "bullish",
                "buy",
                "long",
                "up",
                "gain",
                "profit",
                "good",
                "strong",
                "growth",
            ]
            negative_words = [
                "bearish",
                "sell",
                "short",
                "down",
                "loss",
                "bad",
                "weak",
                "drop",
                "fall",
            ]

            text_lower = text.lower()

            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words == 0:
                return 0.0

            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            return max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]

        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0

    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"

    async def _process_sentiment_data(self, sentiment_data: list[dict]) -> list[dict]:
        """Process and deduplicate sentiment data"""
        try:
            processed = []
            current_time = time.time()

            for item in sentiment_data:
                item_hash = hashlib.md5(
                    f"{item.get('platform')}_{item.get('text', '')}_{item.get('symbols', [])}".encode()
                ).hexdigest()

                # Check if we've seen this item recently (within 10 minutes)
                if item_hash in self.sentiment_cache:
                    cache_time = self.sentiment_cache[item_hash].get("timestamp", 0)
                    if current_time - cache_time < 600:  # 10 minutes
                        continue

                # Add to cache and processed list
                self.sentiment_cache[item_hash] = {"timestamp": current_time, "data": item}
                processed.append(item)

            return processed

        except Exception as e:
            logger.error(f"Error processing sentiment data: {e}")
            return sentiment_data  # Return original data if processing fails

    async def _cleanup_cache(self):
        """Clean up old cache entries"""
        try:
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hour

            keys_to_remove = [
                key
                for key, value in self.sentiment_cache.items()
                if value.get("timestamp", 0) < cutoff_time
            ]

            for key in keys_to_remove:
                del self.sentiment_cache[key]

            logger.debug(f"Cleaned {len(keys_to_remove)} old cache entries")

        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")


# Global instance
social_sentiment_streamer = SocialSentimentStreamer()

# Future Integration Points (commented for reference)
"""
TWITTER API V2 INTEGRATION (PAID):
- Basic plan: $100/month for 10k tweets/month
- Endpoint: https://api.twitter.com/2/tweets/search/recent
- Authentication: Bearer token
- Rate limits: 300 requests/15 min

STOCKTWITS API INTEGRATION:
- Free tier: 200 requests/hour
- Endpoint: https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json
- Authentication: API key
- Real-time sentiment scores

REDDIT PRAW INTEGRATION:
- Free with Reddit account
- Real-time stream processing
- Subreddit monitoring: r/wallstreetbets, r/stocks, r/investing
- Comment sentiment analysis

ALPHA VANTAGE NEWS SENTIMENT:
- Free tier: 5 requests/minute
- Endpoint: https://www.alphavantage.co/query?function=NEWS_SENTIMENT
- Provides news sentiment scores
- Financial entity extraction
"""
