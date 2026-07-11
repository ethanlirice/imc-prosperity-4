"""
Test wrapper: trader.py v16 + minimal OTM BS residual sleeve for VEV_5400/VEV_5500.

This is *not* intended as a final strategy file; it's for quickly validating
parameter choices without editing trader.py.
"""

from __future__ import annotations

import json
import math

import os
import sys

# Ensure repo root (contains trader.py and datamodel.py) is importable when backtesting from this subdir.
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

import trader as base
from datamodel import Order, TradingState


UNDER = "VELVETFRUIT_EXTRACT"
OTM_STRIKES = (5400, 5500)
SURFACE_STRIKES = (5200, 5300, 5400, 5500)

TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

# Offline smile from logs/round3/GROUND_TRUTH.md
SMILE_A = 0.0283
SMILE_B = 0.0025
SMILE_C = 0.2395

BIAS_ALPHA = 0.002  # very slow; only learns long-run bias, not the MR signal
WARMUP = 200

# Maker-only: join/improve bids only when edge covers at least half-spread + buffer.
ENTRY_BUFFER = 0.25

MAX_POS = 40
MAX_QTY_PER_TICK = 8


def smile_iv(m: float) -> float:
    return SMILE_A * m * m + SMILE_B * m + SMILE_C


def best_bid_ask(depth) -> tuple[int | None, int | None]:
    bid = max(depth.buy_orders) if depth.buy_orders else None
    ask = min(depth.sell_orders) if depth.sell_orders else None
    return bid, ask


def infer_start_days(state: TradingState, spot: float) -> float | None:
    mids = {}
    for k in SURFACE_STRIKES:
        sym = f"VEV_{k}"
        d = state.order_depths.get(sym)
        if d is None or not d.buy_orders or not d.sell_orders:
            return None
        b, a = best_bid_ask(d)
        if b is None or a is None:
            return None
        mids[k] = (b + a) / 2.0

    elapsed_days = state.timestamp / TICKS_PER_DAY
    candidates = (5.0, 6.0, 7.0, 8.0)
    best = None
    best_sse = None
    for start in candidates:
        t_days = start - elapsed_days
        if t_days <= 0:
            continue
        t = t_days / DAYS_PER_YEAR
        sse = 0.0
        for k, mid in mids.items():
            m = math.log(k / spot) / math.sqrt(t)
            iv = smile_iv(m)
            theo = base.bs_call(spot, k, t, iv)
            e = mid - theo
            sse += e * e
        if best_sse is None or sse < best_sse:
            best_sse = sse
            best = start
    return best


class Trader:
    def __init__(self):
        self.base = base.Trader()

    def run(self, state: TradingState):
        result, conversions, td_str = self.base.run(state)
        try:
            td = json.loads(td_str) if td_str else {}
        except Exception:
            td = {}

        ud = state.order_depths.get(UNDER)
        if ud is None or not ud.buy_orders or not ud.sell_orders:
            return result, conversions, json.dumps(td)

        ub, ua = best_bid_ask(ud)
        if ub is None or ua is None:
            return result, conversions, json.dumps(td)

        spot = (ub + ua) / 2.0

        start_days = td.get("start_days_otm")
        if start_days is None:
            start_days = infer_start_days(state, spot)
            if start_days is None:
                return result, conversions, json.dumps(td)
            td["start_days_otm"] = start_days

        t_days = float(start_days) - state.timestamp / TICKS_PER_DAY
        if t_days <= 0:
            return result, conversions, json.dumps(td)
        t = t_days / DAYS_PER_YEAR

        # Biases keyed per strike.
        bias = td.get("otm_bias", {})
        if not isinstance(bias, dict):
            bias = {}
        cnt = int(td.get("otm_warm", 0)) + 1
        td["otm_warm"] = cnt

        for k in OTM_STRIKES:
            sym = f"VEV_{k}"
            d = state.order_depths.get(sym)
            if d is None or not d.buy_orders or not d.sell_orders:
                continue
            b, a = best_bid_ask(d)
            if b is None or a is None or b >= a:
                continue
            mid = (b + a) / 2.0
            m = math.log(k / spot) / math.sqrt(t)
            iv = smile_iv(m)
            theo = base.bs_call(spot, k, t, iv)

            raw = mid - theo
            key = str(k)
            prev = bias.get(key)
            if prev is None:
                new_bias = raw
            else:
                new_bias = float(prev) + BIAS_ALPHA * (raw - float(prev))
            bias[key] = float(new_bias)

            fair = theo + float(new_bias)
            pos = int(state.position.get(sym, 0))
            lim = min(MAX_POS, base.POS_LIMIT.get(sym, MAX_POS))
            bc = lim - pos
            sc = lim + pos
            spread = a - b
            half_spread = spread / 2.0

            if cnt < WARMUP:
                continue

            # Only place bids; OTM flow is overwhelmingly seller-initiated into the bid.
            # Improve by 1 tick when spread allows (helps `--match-trades worse`), else join.
            bid_px = b + 1 if (spread >= 2 and b + 1 < a) else b
            entry_edge = half_spread + ENTRY_BUFFER
            if bc > 0 and (fair - bid_px) >= entry_edge:
                q = min(MAX_QTY_PER_TICK, bc)
                if q > 0:
                    result.setdefault(sym, []).append(Order(sym, int(bid_px), int(q)))

        td["otm_bias"] = bias
        return result, conversions, json.dumps(td)
