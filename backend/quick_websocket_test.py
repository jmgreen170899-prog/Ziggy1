"""
Quick WebSocket Connection Test for News Updates Issue
"""

import asyncio
import json

import websockets


async def test_news_connection():
    """Test news WebSocket connection to diagnose the issue"""
    print("🔍 DIAGNOSING NEWS UPDATES ISSUE")
    print("=" * 40)

    try:
        print("📰 Testing news WebSocket connection...")
        async with websockets.connect("ws://localhost:8000/ws/news") as websocket:
            print("✅ Connected to news WebSocket successfully!")

            # Listen for messages for 15 seconds
            print("⏳ Listening for news updates...")

            for i in range(15):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1)
                    data = json.loads(message)

                    print(f"📨 Received message type: {data.get('type', 'unknown')}")
                    if data.get("type") == "news_update":
                        news_data = data.get("data", {})
                        title = news_data.get("title", "No title")
                        print(f"   📰 News: {title[:50]}...")
                        print("   ✅ NEWS IS WORKING!")
                        break
                except TimeoutError:
                    print(f"   ⏰ Waiting... ({i + 1}/15)")
            else:
                print("❌ No news updates received in 15 seconds")
                print("💡 This explains why frontend shows 'waiting for news updates'")

    except ConnectionRefusedError:
        print("❌ Cannot connect to ws://localhost:8000/ws/news")
        print("💡 Backend may not be running or WebSocket endpoint not working")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_market_data_connection():
    """Test market data WebSocket connection"""
    print("\n📊 Testing market data WebSocket connection...")
    try:
        async with websockets.connect("ws://localhost:8000/ws/market") as websocket:
            print("✅ Connected to market data WebSocket successfully!")

            # Listen for one message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📨 Received: {data.get('type', 'unknown')}")
                if data.get("type") == "market_data":
                    symbol = data.get("symbol", "Unknown")
                    print(f"   📈 Market data for {symbol}: Working!")
                else:
                    print(f"   📋 Message: {data}")
            except TimeoutError:
                print("   ⏰ No market data received in 5 seconds")

    except Exception as e:
        print(f"❌ Market data error: {e}")


async def main():
    await test_news_connection()
    await test_market_data_connection()

    print("\n🎯 DIAGNOSIS COMPLETE")
    print("=" * 40)
    print("If news WebSocket is not receiving data, check:")
    print("1. Backend news streaming service is running")
    print("2. RSS news provider is working")
    print("3. WebSocket endpoint /ws/news is accessible")


if __name__ == "__main__":
    asyncio.run(main())
