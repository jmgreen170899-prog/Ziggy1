import asyncio
import json

import websockets


async def test_websocket():
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/market") as websocket:
            print("✅ Connected to market data WebSocket!")

            # Wait for initial data
            print("⏳ Waiting for market data...")
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    print(
                        f"📊 Received: {data.get('type', 'unknown')} - {str(data)[:100]}..."
                    )
                except TimeoutError:
                    print(f"⏰ Timeout {i + 1}/5")
                except Exception as e:
                    print(f"❌ Error: {e}")

            print("✅ WebSocket test completed!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
