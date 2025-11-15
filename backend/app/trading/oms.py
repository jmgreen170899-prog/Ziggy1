from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from .models import Fill, Order, Position


class OMS:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init(self):
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    ts TEXT NOT NULL
                )
            """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    ts TEXT NOT NULL
                )
            """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    qty INTEGER NOT NULL,
                    avg_price REAL NOT NULL
                )
            """
            )

    def record_order(self, o: Order) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO orders(client_id, symbol, side, qty, type, ts) VALUES (?, ?, ?, ?, ?, ?)",
                (o.client_order_id, o.symbol, o.side, o.qty, o.order_type, o.ts),
            )
            return cur.lastrowid

    def record_fill(self, f: Fill) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO fills(order_id, symbol, side, qty, avg_price, ts) VALUES (?, ?, ?, ?, ?, ?)",
                (f.order_id, f.symbol, f.side, f.qty, f.avg_price, f.ts),
            )
            self._apply_fill_to_positions(c, f)
            return cur.lastrowid

    def _apply_fill_to_positions(self, c: sqlite3.Connection, f: Fill) -> None:
        row = c.execute(
            "SELECT qty, avg_price FROM positions WHERE symbol = ?", (f.symbol,)
        ).fetchone()
        sign = 1 if f.side == "BUY" else -1
        fill_qty = sign * f.qty
        if row is None:
            c.execute(
                "INSERT OR REPLACE INTO positions(symbol, qty, avg_price) VALUES (?, ?, ?)",
                (f.symbol, fill_qty, f.avg_price),
            )
            return
        qty, avg_price = row
        new_qty = qty + fill_qty
        if (qty >= 0 and fill_qty > 0) or (qty <= 0 and fill_qty < 0):
            total_shares = abs(qty) + abs(fill_qty)
            new_avg = (abs(qty) * avg_price + abs(fill_qty) * f.avg_price) / max(
                total_shares, 1
            )
        else:
            new_avg = avg_price if new_qty != 0 else 0.0
        if new_qty == 0:
            c.execute("DELETE FROM positions WHERE symbol = ?", (f.symbol,))
        else:
            c.execute(
                "UPDATE positions SET qty = ?, avg_price = ? WHERE symbol = ?",
                (new_qty, new_avg, f.symbol),
            )

    def positions(self) -> Iterable[Position]:
        with self._conn() as c:
            for sym, qty, avg in c.execute(
                "SELECT symbol, qty, avg_price FROM positions"
            ):
                yield Position(sym, qty, avg)

    def position_count(self) -> int:
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) FROM positions WHERE qty <> 0").fetchone()
            return int(row[0]) if row else 0

    def gross_exposure(self, last_prices: dict[str, float] | None = None) -> float:
        exp = 0.0
        with self._conn() as c:
            for sym, qty, avg in c.execute(
                "SELECT symbol, qty, avg_price FROM positions"
            ):
                px = (last_prices or {}).get(sym, avg)
                exp += abs(qty * px)
        return float(exp)

    def realized_pnl_today(self) -> float:
        # Placeholder: implement lot-level realization if needed.
        return 0.0
