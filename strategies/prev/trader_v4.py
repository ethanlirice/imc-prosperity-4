"""
Round 5 trader v4 — MM + MR on a stability-filtered allow-list.

Primary R5 backtest: not yet re-verified under current default-match
prosperity4btx ... 5 --merge-pnl command.

v1 (3 layers)                                     = +79,513.
v2 (drop pairs, MM/MR all 50)                     = +152,042.
v3 (drop pairs, MM/MR only on 31 v2 winners)      = +296,162.
v4 (drop products that lost 2-of-3 historic days) = ?

Live runs on an UNSEEN day, so a product that lost on 2 of 3 calibration days
is likely to lose on the live day too. v4 keeps only the 23 products that won
at least 2 of 3 days. The cost on calibration data is +14k of dropped winners,
the gain (we hope) is robustness on the live day.
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState

# === Constants ===

LIMIT = 10  # per-product position cap (Round 5 rule)

PAIRS: List[Dict[str, str]] = []
STAT_ARB_PRODUCTS: set = set()
PAIR_SIZE = 5
WINDOW = 500
MIN_WARMUP = 200
ENTRY_Z = 1.5
EXIT_Z = 0.5

# Allow-list: products that won at least 2 of 3 historic days in v3.
ALLOWED_PRODUCTS = {
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PEBBLES_L",
    "PEBBLES_S",
    "ROBOT_IRONING",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SLEEP_POD_POLYESTER",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ASTRO_BLACK",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_ORANGE",
}

# Sticky fair for non-stat-arb MM/MR. EWMA on mid; α=0.05 ⇒ ~14-tick half-life.
# When the level-1 mid jumps, the EWMA lags, exposing MR take opportunities.
EWMA_ALPHA = 0.05
# MR take threshold in ticks above/below EWMA fair. Tight enough to fire,
# wide enough to clear typical noise (median spread is 7-17 ticks across products).
MR_THRESHOLD = 3
# MM passive edge in ticks inside the touch.
MM_EDGE = 1
# Skip MM on books where best ask - best bid <= MIN_SPREAD_FOR_MM (no edge).
MIN_SPREAD_FOR_MM = 2


# === Helpers ===


def best_bid_ask(depth: OrderDepth) -> Tuple[Optional[int], Optional[int]]:
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
    return bid, ask


def mid_price(depth: OrderDepth) -> Optional[float]:
    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return None
    return 0.5 * (bid + ask)


def fill_at(depth: OrderDepth, side: int, qty: int) -> Optional[Tuple[int, int]]:
    """Sweep up to `qty` units across the book at side (+1 = buy asks, -1 = sell bids).
    Returns (worst_price_we_cross, total_filled). Order at this price will execute
    against price-time priority across all crossed levels up to qty."""
    if qty <= 0:
        return None
    remaining = qty
    last_price: Optional[int] = None
    filled = 0
    levels = (
        sorted(depth.sell_orders.keys()) if side > 0 else sorted(depth.buy_orders.keys(), reverse=True)
    )
    for price in levels:
        avail = -depth.sell_orders[price] if side > 0 else depth.buy_orders[price]
        if avail <= 0:
            continue
        take = min(remaining, avail)
        remaining -= take
        filled += take
        last_price = price
        if remaining <= 0:
            break
    if filled == 0 or last_price is None:
        return None
    return int(last_price), int(filled)


def clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


# === Trader ===


class Trader:
    def load(self, raw: str) -> Dict[str, Any]:
        if not raw:
            return {"hist": {}, "ewma": {}, "pstate": {}}
        try:
            data = json.loads(raw)
            data.setdefault("hist", {})
            data.setdefault("ewma", {})
            data.setdefault("pstate", {})
            return data
        except Exception:
            return {"hist": {}, "ewma": {}, "pstate": {}}

    def save(self, mem: Dict[str, Any]) -> str:
        return json.dumps(mem, separators=(",", ":"))

    # --- Layer 3: stat arb on confirmed pairs ---

    def stat_arb_targets(
        self, state: TradingState, mem: Dict[str, Any]
    ) -> Dict[str, int]:
        """Return desired net position per stat-arb product, summing across pairs."""
        targets: Dict[str, int] = {p: 0 for p in STAT_ARB_PRODUCTS}
        hist = mem["hist"]
        pstate = mem["pstate"]
        for idx, pair in enumerate(PAIRS):
            key = f"p{idx}"
            depth_a = state.order_depths.get(pair["a"])
            depth_b = state.order_depths.get(pair["b"])
            if depth_a is None or depth_b is None:
                continue
            mid_a = mid_price(depth_a)
            mid_b = mid_price(depth_b)
            if mid_a is None or mid_b is None:
                continue
            spread = mid_a - mid_b

            buf = hist.setdefault(key, [])
            buf.append(spread)
            if len(buf) > WINDOW:
                # keep tail
                del buf[: len(buf) - WINDOW]

            ps = pstate.setdefault(key, {"sign": 0})
            sign = int(ps.get("sign", 0))

            if len(buf) >= MIN_WARMUP:
                mu = sum(buf) / len(buf)
                var = sum((x - mu) * (x - mu) for x in buf) / len(buf)
                sd = math.sqrt(var) if var > 0 else 0.0
                if sd > 1e-6:
                    z = (spread - mu) / sd
                    if sign == 0:
                        if z >= ENTRY_Z:
                            sign = -1  # short A, long B (mean revert spread down)
                        elif z <= -ENTRY_Z:
                            sign = +1  # long A, short B
                    else:
                        if abs(z) <= EXIT_Z:
                            sign = 0
            ps["sign"] = sign

            targets[pair["a"]] = clamp(targets[pair["a"]] + sign * PAIR_SIZE, -LIMIT, LIMIT)
            targets[pair["b"]] = clamp(targets[pair["b"]] - sign * PAIR_SIZE, -LIMIT, LIMIT)

        return targets

    def stat_arb_orders(
        self, state: TradingState, targets: Dict[str, int]
    ) -> Dict[str, List[Order]]:
        """Cross the book to move each stat-arb product toward its target position."""
        orders: Dict[str, List[Order]] = {}
        for product, target in targets.items():
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            current = int(state.position.get(product, 0))
            delta = target - current
            if delta == 0:
                continue
            side = 1 if delta > 0 else -1
            result = fill_at(depth, side, abs(delta))
            if result is None:
                continue
            price, qty = result
            orders[product] = [Order(product, price, qty if side > 0 else -qty)]
        return orders

    # --- Layers 1+2: MM and MR for non-stat-arb products ---

    def mm_mr_orders(
        self, state: TradingState, mem: Dict[str, Any]
    ) -> Dict[str, List[Order]]:
        orders: Dict[str, List[Order]] = {}
        ewma = mem["ewma"]
        for product, depth in state.order_depths.items():
            if product in STAT_ARB_PRODUCTS:
                continue
            if product not in ALLOWED_PRODUCTS:
                continue
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None:
                continue
            mid = 0.5 * (bid + ask)
            prev = ewma.get(product)
            fair = mid if prev is None else (1 - EWMA_ALPHA) * float(prev) + EWMA_ALPHA * mid
            ewma[product] = fair

            position = int(state.position.get(product, 0))
            buy_room = LIMIT - position
            sell_room = LIMIT + position
            product_orders: List[Order] = []

            # Layer 2: MR take when book is dislocated from sticky fair.
            if buy_room > 0 and ask <= fair - MR_THRESHOLD:
                avail = -depth.sell_orders.get(ask, 0)
                qty = min(buy_room, avail)
                if qty > 0:
                    product_orders.append(Order(product, ask, qty))
                    position += qty
                    buy_room = LIMIT - position
                    sell_room = LIMIT + position
            if sell_room > 0 and bid >= fair + MR_THRESHOLD:
                avail = depth.buy_orders.get(bid, 0)
                qty = min(sell_room, avail)
                if qty > 0:
                    product_orders.append(Order(product, bid, -qty))
                    position -= qty
                    buy_room = LIMIT - position
                    sell_room = LIMIT + position

            # Layer 1: MM passive quotes inside the touch with remaining capacity.
            if ask - bid > MIN_SPREAD_FOR_MM:
                if buy_room > 0:
                    product_orders.append(Order(product, bid + MM_EDGE, buy_room))
                if sell_room > 0:
                    product_orders.append(Order(product, ask - MM_EDGE, -sell_room))

            if product_orders:
                orders[product] = product_orders
        return orders

    # --- main entrypoint ---

    def run(self, state: TradingState):
        mem = self.load(state.traderData)
        targets = self.stat_arb_targets(state, mem)
        orders = self.stat_arb_orders(state, targets)
        mm_mr = self.mm_mr_orders(state, mem)
        for product, prod_orders in mm_mr.items():
            orders.setdefault(product, []).extend(prod_orders)
        return orders, 0, self.save(mem)
