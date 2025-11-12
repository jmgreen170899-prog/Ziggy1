from __future__ import annotations


def demo_price_series(n: int = 100):
    import math

    return [100 + 2 * math.sin(i / 5) for i in range(n)]
