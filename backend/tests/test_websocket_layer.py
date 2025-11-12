import asyncio
from contextlib import suppress
from typing import Any

from app.core.websocket import ConnectionManager


class DummyWebSocket:
    def __init__(self, should_fail: bool = False):
        self.accepted = False
        self.should_fail = should_fail
        self.sent: list[dict[str, Any]] = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, data: dict[str, Any]):
        if self.should_fail:
            raise RuntimeError("send failure")
        self.sent.append(data)


def test_broadcast_prunes_failing_sockets():
    async def _run():
        cm = ConnectionManager()
        ch = "test_channel"

        ok_ws = DummyWebSocket()
        bad_ws = DummyWebSocket(should_fail=True)

        await cm.connect(ok_ws, ch)  # type: ignore[arg-type]
        await cm.connect(bad_ws, ch)  # type: ignore[arg-type]

        assert len(cm.connections.get(ch, set())) == 2

        # Enqueue a message
        await cm.broadcast_to_type({"hello": "world"}, ch)

        # Give the consumer time to process
        await asyncio.sleep(0.05)

        conns = cm.connections.get(ch, set())
        # Bad socket should have been pruned
        assert len(conns) == 1
        assert ok_ws in conns

    asyncio.run(_run())


def test_queue_overflow_drops_messages():
    async def _run():
        cm = ConnectionManager()
        ch = "overflow"

        # Ensure queue and consumer exist
        # Access internal queue and stop consumer to prevent draining
        cm._get_queue(ch)  # type: ignore[attr-defined]
        consumer = cm._consumers[ch]  # type: ignore[attr-defined]
        consumer.cancel()
        with suppress(asyncio.CancelledError):
            await consumer

        # Enqueue more than maxsize (100)
        drops_expected = 10
        for i in range(100 + drops_expected):
            await cm.broadcast_to_type({"i": i}, ch)

        # Check drop metric recorded
        metrics = cm._metrics.get(ch, {})  # type: ignore[attr-defined]
        dropped = int(metrics.get("queue_dropped", 0))
        assert dropped >= drops_expected

        # Cleanup: restart consumer so background tasks can exit gracefully
        cm._consumers[ch] = asyncio.create_task(cm._consume_channel(ch))  # type: ignore[attr-defined]
        # Let it idle briefly
        await asyncio.sleep(0.01)

    asyncio.run(_run())
