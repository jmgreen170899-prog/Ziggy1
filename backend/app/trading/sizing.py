from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SizerConfig:
    fixed_notional: float = 500.0
    default_price_hint: float = 100.0  # used if no quote price is available


class FixedNotionalSizer:
    def __init__(self, cfg: SizerConfig):
        self.cfg = cfg

    def shares_for(self, price: float | None) -> int:
        p = price or self.cfg.default_price_hint
        if p <= 0:
            p = self.cfg.default_price_hint
        qty = int(self.cfg.fixed_notional // p)
        return max(qty, 1)
