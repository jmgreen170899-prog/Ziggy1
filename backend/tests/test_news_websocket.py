import asyncio
import json

import websockets


async def test_news_websocket():
    try:
        print("🔌 Connecting to News WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/news") as websocket:
            print("✅ Connected to news WebSocket!")

            # Wait for news data
            print("⏳ Waiting for news updates...")
            for i in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📰 Received: {data.get('type', 'unknown')}")
                    if data.get("type") == "news_update" and "data" in data:
                        news_data = data["data"]
                        print(f"   Title: {news_data.get('title', 'No title')[:100]}")
                        print(f"   Source: {news_data.get('source', 'Unknown')}")
                except TimeoutError:
                    print(f"⏰ News timeout {i + 1}/10")
                except Exception as e:
                    print(f"❌ Error: {e}")

            print("✅ News WebSocket test completed!")

    except Exception as e:
        print(f"❌ News connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_news_websocket())
