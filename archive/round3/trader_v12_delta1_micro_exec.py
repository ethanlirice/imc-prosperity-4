"""
Round 3 (delta-1 only) — microstructure execution upgrades for:
- HYDROGEL_PACK
- VELVETFRUIT_EXTRACT
- VEV_4000 (deep ITM parity leg, treated as delta-1)

Focus:
- Robust wall detection: prefer L2 walls (ignore occasional one-sided L3 noise).
- Fair persistence: VELVET's L2 is missing often, so use parity-implied fair from VEV_4000 and an EMA.
- Execution: configurable make offsets + gentle inventory skew; smaller quote size for VELVET to reduce
  phantom-fill sensitivity in match-trades=all.

No options (no Black-Scholes).
"""

import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple


# Allow running this file directly via prosperity4btx from the strategies/ folder.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

from datamodel import Order, TradingState  # noqa: E402


HYDROGEL = "HYDROGEL_PACK"
UNDER = "VELVETFRUIT_EXTRACT"
VEV_4000 = "VEV_4000"
K_4000 = 4000

LIMITS = {
    HYDROGEL: 200,
    UNDER: 200,
    VEV_4000: 300,
}

# --- Execution parameters (picked to be robust; tune with backtests) ---

# Update rate for persisted fair anchors (used primarily for UNDER).
FAIR_EMA_ALPHA = 0.20

# How far inside L1 we try to quote (if still respecting fair caps).
IMPROVE_TICKS = {
    # Baseline microstructure quotes 1-tick inside L1 when still below/above fair.
    # Going more aggressive hurt --match-trades=worse on HYDROGEL in practice.
    HYDROGEL: 1,
    VEV_4000: 1,
}

# Keep quotes at least this many ticks away from fair (prevents "selling at/through fair").
MIN_FAIR_EDGE = {
    # Match the baseline wall-MM behavior: allow quoting right up to the wall mid.
    HYDROGEL: 0,
    VEV_4000: 0,
    UNDER: 2,  # tighter spread -> be more conservative in match-trades=all
}

# Inventory skew (in ticks at full position limit).
MAX_SKEW_TICKS = {
    # Keep skew minimal on wide-spread wall products; apply more strongly on the tighter UNDER book.
    HYDROGEL: 0.0,
    VEV_4000: 0.0,
    UNDER: 2.0,
}

# Per-tick quote size caps (UNDER is deliberately smaller).
MAX_MAKE_SIZE = {
    HYDROGEL: 200,
    VEV_4000: 300,
    UNDER: 60,
}

# When inventory is large, stop quoting on the inventory-worsening side.
SOFT_LIMIT_PCT = {
    # Wide-spread wall MM products tolerate full-capacity two-sided quoting well.
    HYDROGEL: 1.00,
    VEV_4000: 1.00,
    UNDER: 0.70,
}


def _safe_json_loads(s: str) -> dict:
    if not s:
        return {}
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except (json.JSONDecodeError, ValueError, TypeError):
        return {}


def _best_prices(depth) -> Optional[Tuple[int, int]]:
    if depth is None or not depth.buy_orders or not depth.sell_orders:
        return None
    return max(depth.buy_orders.keys()), min(depth.sell_orders.keys())


def _l2_wall_prices(depth) -> Optional[Tuple[int, int]]:
    """
    Prefer the second level on each side (L2) if it exists; otherwise fallback to best.
    This avoids the rare case where a one-sided L3 appears and min/max would drag the wall.
    """
    if depth is None or not depth.buy_orders or not depth.sell_orders:
        return None

    bids_desc = sorted(depth.buy_orders.keys(), reverse=True)
    asks_asc = sorted(depth.sell_orders.keys())
    wall_bid = bids_desc[1] if len(bids_desc) >= 2 else bids_desc[0]
    wall_ask = asks_asc[1] if len(asks_asc) >= 2 else asks_asc[0]
    return wall_bid, wall_ask


def _mid_from_depth(depth) -> Optional[float]:
    bp = _best_prices(depth)
    if bp is None:
        return None
    best_bid, best_ask = bp
    if best_bid >= best_ask:
        return None
    return (best_bid + best_ask) / 2.0


def _inventory_skew_ticks(position: int, limit: int, max_skew_ticks: float) -> int:
    if limit <= 0:
        return 0
    # Positive position => skew down (more aggressive selling, less aggressive buying).
    return int(round((position / limit) * max_skew_ticks))


class Trader:
    def run(self, state: TradingState):
        td = _safe_json_loads(state.traderData)

        # Shared fair anchors: UNDER fair is blended between its own wall and VEV_4000 parity.
        under_fair = self._compute_under_fair(state, td)
        vev4000_parity_fair = under_fair - K_4000 if under_fair is not None else None

        result: Dict[str, List[Order]] = {}

        hg_orders = self._trade_wall_mm(state, HYDROGEL, fair_cap=None)
        if hg_orders:
            result[HYDROGEL] = hg_orders

        vev_orders = self._trade_wall_mm(state, VEV_4000, fair_cap=vev4000_parity_fair)
        if vev_orders:
            result[VEV_4000] = vev_orders

        under_orders = self._trade_under_mm(state, under_fair)
        if under_orders:
            result[UNDER] = under_orders

        return result, 0, json.dumps(td)

    def _compute_under_fair(self, state: TradingState, td: dict) -> Optional[float]:
        ud = state.order_depths.get(UNDER)
        vd = state.order_depths.get(VEV_4000)

        implied = None
        v_wall = _l2_wall_prices(vd)
        if v_wall is not None:
            v_bid_wall, v_ask_wall = v_wall
            implied = (v_bid_wall + v_ask_wall) / 2.0 + K_4000

        under_wall = None
        if ud is not None and ud.buy_orders and ud.sell_orders and len(ud.buy_orders) >= 2 and len(ud.sell_orders) >= 2:
            u_bid_wall, u_ask_wall = _l2_wall_prices(ud)
            under_wall = (u_bid_wall + u_ask_wall) / 2.0

        raw = None
        if implied is not None and under_wall is not None:
            raw = 0.5 * (implied + under_wall)
        elif implied is not None:
            raw = implied
        elif under_wall is not None:
            raw = under_wall
        else:
            # As a last resort, fall back to mid (still better than returning None).
            mid = _mid_from_depth(ud) if ud is not None else None
            raw = mid

        if raw is None:
            return None

        prev = td.get("under_fair_ema")
        fair = raw if prev is None else (FAIR_EMA_ALPHA * raw + (1.0 - FAIR_EMA_ALPHA) * float(prev))
        td["under_fair_ema"] = fair
        return fair

    def _trade_wall_mm(self, state: TradingState, symbol: str, fair_cap: Optional[float]):
        """
        Baseline wall-based MM (from the repo's current trader.py), optionally capped to a parity fair.
        Used for: HYDROGEL_PACK and VEV_4000.
        """
        depth = state.order_depths.get(symbol)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        limit = LIMITS[symbol]
        position = state.position.get(symbol, 0)

        bid_wall = min(depth.buy_orders.keys())
        ask_wall = max(depth.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2.0

        orders: List[Order] = []
        buy_cap = limit - position
        sell_cap = limit + position

        # Take favorable liquidity relative to wall_mid (rare but keep for exact parity with baseline).
        for price in sorted(depth.sell_orders.keys()):
            avail = -depth.sell_orders[price]
            if price <= wall_mid - 1:
                take = min(avail, buy_cap)
            elif price <= wall_mid and position < 0:
                take = min(avail, -position, buy_cap)
            else:
                break
            if take > 0:
                orders.append(Order(symbol, price, take))
                buy_cap -= take
                position += take
                if buy_cap <= 0:
                    break

        for price in sorted(depth.buy_orders.keys(), reverse=True):
            avail = depth.buy_orders[price]
            if price >= wall_mid + 1:
                take = min(avail, sell_cap)
            elif price >= wall_mid and position > 0:
                take = min(avail, position, sell_cap)
            else:
                break
            if take > 0:
                orders.append(Order(symbol, price, -take))
                sell_cap -= take
                position -= take
                if sell_cap <= 0:
                    break

        bid_price = int(bid_wall) + 1
        ask_price = int(ask_wall) - 1

        best_bid = max(depth.buy_orders.keys())
        best_ask = min(depth.sell_orders.keys())

        if best_bid + 1 < wall_mid:
            bid_price = max(bid_price, best_bid + 1)
        if best_ask - 1 > wall_mid:
            ask_price = min(ask_price, best_ask - 1)

        # Optional parity cap (VEV_4000): avoid drifting rich/cheap to UNDER - 4000.
        if fair_cap is not None:
            eps = 1e-9
            bid_cap = math.floor(float(fair_cap) - eps)
            ask_cap = math.ceil(float(fair_cap) + eps)
            bid_price = min(bid_price, bid_cap)
            ask_price = max(ask_price, ask_cap)

        if buy_cap > 0:
            orders.append(Order(symbol, int(bid_price), int(buy_cap)))
        if sell_cap > 0:
            orders.append(Order(symbol, int(ask_price), -int(sell_cap)))
        return orders

    def _trade_under_mm(self, state: TradingState, under_fair: Optional[float]):
        depth = state.order_depths.get(UNDER)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        best = _best_prices(depth)
        if best is None:
            return []
        best_bid, best_ask = best
        if best_bid >= best_ask:
            return []

        mid = (best_bid + best_ask) / 2.0
        fair = under_fair if under_fair is not None else mid

        fair_bid = math.floor(fair)
        fair_ask = math.ceil(fair)

        limit = LIMITS[UNDER]
        position = state.position.get(UNDER, 0)
        buy_cap = limit - position
        sell_cap = limit + position

        min_edge = MIN_FAIR_EDGE[UNDER]
        bid_cap_px = fair_bid - min_edge
        ask_cap_px = fair_ask + min_edge

        # Default: join best (edge=2 typically implies best_bid/best_ask when spread=5).
        bid_px = min(best_bid + 1, best_ask - 1)
        ask_px = max(best_ask - 1, best_bid + 1)

        bid_px = min(bid_px, bid_cap_px)
        ask_px = max(ask_px, ask_cap_px)

        skew = _inventory_skew_ticks(position, limit, MAX_SKEW_TICKS[UNDER])
        bid_px = min(bid_px - skew, bid_cap_px)
        ask_px = max(ask_px - skew, ask_cap_px)

        if bid_px >= ask_px:
            return []

        soft = int(round(SOFT_LIMIT_PCT[UNDER] * limit))
        max_make = MAX_MAKE_SIZE[UNDER]

        want_buy = buy_cap > 0 and position < soft
        want_sell = sell_cap > 0 and position > -soft

        buy_qty = min(buy_cap, max_make) if want_buy else 0
        sell_qty = min(sell_cap, max_make) if want_sell else 0

        orders: List[Order] = []
        if buy_qty > 0:
            orders.append(Order(UNDER, int(bid_px), int(buy_qty)))
        if sell_qty > 0:
            orders.append(Order(UNDER, int(ask_px), -int(sell_qty)))
        return orders
