from __future__ import annotations

from dataclasses import dataclass

from .oms import OMS


@dataclass
class RiskConfig:
    max_notional_per_trade: float = 1000.0
    max_gross_exposure: float = 5000.0
    max_daily_loss: float = 200.0
    max_positions: int = 5


class RiskManager:
    def __init__(self, cfg: RiskConfig, oms: OMS):
        self.cfg, self.oms = cfg, oms

    def check(self, symbol: str, intended_notional: float) -> bool:
        if intended_notional > self.cfg.max_notional_per_trade:
            raise ValueError("Notional exceeds per-trade cap")
        if self.oms.gross_exposure() + abs(intended_notional) > self.cfg.max_gross_exposure:
            raise ValueError("Exposure cap hit")
        # if self.oms.realized_pnl_today() < -self.cfg.max_daily_loss:
        #     raise ValueError("Daily loss limit breached")
        if self.oms.position_count() >= self.cfg.max_positions:
            raise ValueError("Positions limit reached")
        return True
