"""
IEX Cloud Free Tier Market Data Provider
- 50,000 free API calls per month
- Real-time quotes during market hours
- Good for up to ~1,650 calls per day
"""

import asyncio
import time
from typing import Any

import aiohttp


class IEXCloudProvider:
    """Free IEX Cloud market data provider"""

    def __init__(self, api_key: str = "pk_test_YOUR_PUBLIC_KEY"):  # Use test key for now
        self.api_key = api_key
        self.base_url = "https://cloud.iexapis.com/stable"
        self.session: aiohttp.ClientSession | None = None

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get real-time quote for a symbol"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            assert self.session is not None  # Type narrowing
            url = f"{self.base_url}/stock/{symbol}/quote"
            params = {"token": self.api_key}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Convert to our standard format
                    return {
                        "symbol": data.get("symbol"),
                        "price": data.get("latestPrice"),
                        "change": data.get("change"),
                        "change_percent": data.get("changePercent", 0) * 100,
                        "volume": data.get("latestVolume"),
                        "timestamp": time.time(),
                        "market_time": data.get("latestUpdate"),
                        "provider": "iex_cloud",
                        "high": data.get("high"),
                        "low": data.get("low"),
                        "open": data.get("open"),
                        "previous_close": data.get("previousClose"),
                        "market_cap": data.get("marketCap"),
                        "pe_ratio": data.get("peRatio"),
                        "is_us_market_open": data.get("isUSMarketOpen", False),
                    }
                else:
                    print(f"IEX Cloud error: {response.status}")
                    return None

        except Exception as e:
            print(f"IEX Cloud provider error: {e}")
            return None

    async def get_batch_quotes(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Get quotes for multiple symbols in one call"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            assert self.session is not None  # Type narrowing
            symbols_str = ",".join(symbols)
            url = f"{self.base_url}/stock/market/batch"
            params = {"symbols": symbols_str, "types": "quote", "token": self.api_key}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}

                    for symbol, symbol_data in data.items():
                        if "quote" in symbol_data:
                            quote = symbol_data["quote"]
                            result[symbol] = {
                                "symbol": quote.get("symbol"),
                                "price": quote.get("latestPrice"),
                                "change": quote.get("change"),
                                "change_percent": quote.get("changePercent", 0) * 100,
                                "volume": quote.get("latestVolume"),
                                "timestamp": time.time(),
                                "provider": "iex_cloud_batch",
                                "high": quote.get("high"),
                                "low": quote.get("low"),
                                "open": quote.get("open"),
                                "is_us_market_open": quote.get("isUSMarketOpen", False),
                            }

                    return result
                else:
                    return {}

        except Exception as e:
            print(f"IEX Cloud batch error: {e}")
            return {}

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


# Test function
async def test_iex_cloud():
    """Test IEX Cloud provider"""
    provider = IEXCloudProvider()

    print("🧪 Testing IEX Cloud Free Tier...")

    # Test single quote
    quote = await provider.get_quote("AAPL")
    if quote:
        print(
            f"✅ AAPL: ${quote['price']} ({quote['change']:+.2f}, {quote['change_percent']:+.2f}%)"
        )
        print(f"   Market Open: {quote.get('is_us_market_open', 'Unknown')}")
    else:
        print("❌ Failed to get AAPL quote")

    # Test batch quotes
    batch = await provider.get_batch_quotes(["AAPL", "MSFT", "GOOGL"])
    if batch:
        print(f"✅ Batch quotes: {len(batch)} symbols")
        for symbol, data in batch.items():
            print(f"   {symbol}: ${data['price']} ({data['change']:+.2f})")

    await provider.close()


if __name__ == "__main__":
    asyncio.run(test_iex_cloud())
