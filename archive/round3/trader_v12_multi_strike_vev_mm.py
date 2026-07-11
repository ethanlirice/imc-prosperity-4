"""
Round 3 minimal multi-strike options market maker.

Products:
- Underlying: VELVETFRUIT_EXTRACT
- Options: VEV_5200 / VEV_5300 / VEV_5400 / VEV_5500 (European calls)

Model/quoting patterns adapted from common R3 winners:
- Offline quadratic IV smile in m = log(K/S)/sqrt(T)
- Black–Scholes theoretical per strike
- Per-strike EMA bias for persistent (mid - theo) drift
- Quote around (theo + ema_bias) with inventory + global-delta skew
- Taker thresholds for obvious mispricings
"""

import json
import math
import os
import sys

# Ensure repo root (contains datamodel.py) is importable when backtesting from this subdir.
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

from datamodel import Order, TradingState


UNDER = "VELVETFRUIT_EXTRACT"
OPTIONS = {5200: "VEV_5200", 5300: "VEV_5300", 5400: "VEV_5400", 5500: "VEV_5500"}

# Internal risk limits (game limits are higher, but the underlying is wide so we keep these modest).
UNDER_LIMIT = 200
OPTION_LIMIT = 75

# Timestamp units: 100 per tick, 1_000_000 per day in Prosperity backtests.
TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

# IV smile in m = log(K/S)/sqrt(T).
# Coeffs are in-family with (and close to) common offline fits used for VEV in Round 3.
SMILE_A = 0.0283
SMILE_B = 0.0025
SMILE_C = 0.2395

# EMA on (mid - theo) to absorb slowly-varying bias; lower alpha = stronger mean-reversion signal.
BIAS_EMA_ALPHA = 0.02

# Quoting / taking params (ticks).
MAKE_HALF_SPREAD = 0.55
TAKE_MARGIN = 0.75

# Inventory and delta control.
INV_SKEW_TICKS = 0.02          # per-contract inventory skew (per strike)
GLOBAL_DELTA_SKEW_TICKS = 0.01  # skew all option quotes by net delta (in underlying shares)
GLOBAL_DELTA_SOFT_LIMIT = 140   # stop quoting bids/asks that worsen delta beyond this

# Only hedge with the underlying when it's tight enough to not donate the spread.
HEDGE_SPREAD_MAX = 1
HEDGE_TRIGGER_DELTA = 120
HEDGE_RATIO = 0.5
HEDGE_MAX_STEP = 40

SQRT_2 = math.sqrt(2.0)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT_2))


def smile_iv(m: float) -> float:
    return SMILE_A * m * m + SMILE_B * m + SMILE_C


def bs_call_and_delta(spot: float, strike: int, time_to_expiry: float, volatility: float) -> tuple[float, float]:
    if spot <= 0.0 or strike <= 0 or time_to_expiry <= 0.0 or volatility <= 0.0:
        intrinsic = max(spot - strike, 0.0)
        return intrinsic, 1.0 if spot > strike else 0.0
    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + 0.5 * volatility * volatility * time_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    call = spot * norm_cdf(d1) - strike * norm_cdf(d2)
    delta = norm_cdf(d1)
    return call, delta


def best_bid_ask(depth):
    bid = max(depth.buy_orders) if depth.buy_orders else None
    ask = min(depth.sell_orders) if depth.sell_orders else None
    return bid, ask


def infer_start_days(state, spot):
    # Infer the start-of-sim days-to-expiry from the observed surface mids.
    mids: dict[int, float] = {}
    for k, sym in OPTIONS.items():
        d = state.order_depths.get(sym)
        if d is None or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = best_bid_ask(d)
        if bid is None or ask is None:
            return None
        mids[k] = (bid + ask) / 2.0

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
            theo, _ = bs_call_and_delta(spot, k, t, iv)
            e = mid - theo
            sse += e * e
        if best_sse is None or sse < best_sse:
            best_sse = sse
            best = start
    return best


class Trader:
    def run(self, state: TradingState):
        try:
            td = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            td = {}

        result: dict[str, list[Order]] = {}

        ud = state.order_depths.get(UNDER)
        if ud is None or not ud.buy_orders or not ud.sell_orders:
            return result, 0, json.dumps(td)

        under_bid, under_ask = best_bid_ask(ud)
        if under_bid is None or under_ask is None:
            return result, 0, json.dumps(td)

        spot = (under_bid + under_ask) / 2.0

        start_days = td.get("start_days")
        if start_days is None:
            start_days = infer_start_days(state, spot) or 8.0
            td["start_days"] = start_days

        elapsed_days = state.timestamp / TICKS_PER_DAY
        t_days = float(start_days) - elapsed_days
        if t_days <= 0:
            return result, 0, json.dumps(td)
        t = t_days / DAYS_PER_YEAR

        bias: dict[str, float] = td.get("bias", {})
        if not isinstance(bias, dict):
            bias = {}

        # Pass 1: compute rolling fair per strike, deltas, and current net delta.
        per_opt = {}
        net_delta = 0.0
        for k, sym in OPTIONS.items():
            d = state.order_depths.get(sym)
            if d is None or not d.buy_orders or not d.sell_orders:
                continue
            bid, ask = best_bid_ask(d)
            if bid is None or ask is None or bid >= ask:
                continue
            mid = (bid + ask) / 2.0

            m = math.log(k / spot) / math.sqrt(t)
            iv = smile_iv(m)
            theo, delta = bs_call_and_delta(spot, k, t, iv)

            diff = mid - theo
            key = str(k)
            prev = bias.get(key)
            if prev is None:
                new_bias = diff
            else:
                new_bias = BIAS_EMA_ALPHA * diff + (1.0 - BIAS_EMA_ALPHA) * float(prev)
            bias[key] = float(new_bias)

            fair = theo + new_bias
            pos = int(state.position.get(sym, 0))
            net_delta += delta * pos

            per_opt[sym] = {
                "k": k,
                "depth": d,
                "bid": bid,
                "ask": ask,
                "theo": theo,
                "fair": fair,
                "delta": delta,
                "pos": pos,
            }

        td["bias"] = bias

        # Global skew used to keep the book roughly delta-balanced without constantly trading the wide underlying.
        global_skew = GLOBAL_DELTA_SKEW_TICKS * net_delta
        global_skew = max(min(global_skew, 3.0), -3.0)

        # Pass 2: generate option orders; track net delta assuming taker orders fill.
        net_delta_after_taker = 0.0
        for sym, ctx in per_opt.items():
            k = int(ctx["k"])
            d = ctx["depth"]
            bid = int(ctx["bid"])
            ask = int(ctx["ask"])
            fair = float(ctx["fair"])
            delta = float(ctx["delta"])
            pos = int(ctx["pos"])

            orders: list[Order] = []
            buy_cap = OPTION_LIMIT - pos
            sell_cap = OPTION_LIMIT + pos

            # If we're already very long/short delta, stop quoting in the direction that worsens it.
            allow_buy = net_delta < GLOBAL_DELTA_SOFT_LIMIT
            allow_sell = net_delta > -GLOBAL_DELTA_SOFT_LIMIT

            # TAKER: hit obvious mispricings against L1.
            if allow_buy and buy_cap > 0 and ask <= fair - TAKE_MARGIN:
                qty = min(-d.sell_orders[ask], buy_cap, 25)
                if qty > 0:
                    orders.append(Order(sym, ask, int(qty)))
                    pos += int(qty)
                    buy_cap -= int(qty)

            if allow_sell and sell_cap > 0 and bid >= fair + TAKE_MARGIN:
                qty = min(d.buy_orders[bid], sell_cap, 25)
                if qty > 0:
                    orders.append(Order(sym, bid, -int(qty)))
                    pos -= int(qty)
                    sell_cap -= int(qty)

            # MAKER: quote around skewed fair.
            center = fair - global_skew - INV_SKEW_TICKS * pos
            raw_bid = center - MAKE_HALF_SPREAD
            raw_ask = center + MAKE_HALF_SPREAD

            bid_px = int(math.floor(raw_bid))
            ask_px = int(math.ceil(raw_ask))

            intrinsic = max(0.0, spot - k)
            ask_px = max(ask_px, int(math.ceil(intrinsic)))

            # Clamp into the current spread (join or improve by a tick).
            bid_px = min(max(bid_px, bid), ask - 1)
            ask_px = max(min(ask_px, ask), bid + 1)
            if bid_px >= ask_px:
                bid_px = bid
                ask_px = ask

            inv = pos / float(OPTION_LIMIT) if OPTION_LIMIT else 0.0
            base = 20
            bid_qty = int(round(base * (1.0 - inv)))
            ask_qty = int(round(base * (1.0 + inv)))
            bid_qty = max(0, min(bid_qty, 2 * base, buy_cap))
            ask_qty = max(0, min(ask_qty, 2 * base, sell_cap))

            if not allow_buy:
                bid_qty = 0
            if not allow_sell:
                ask_qty = 0

            if bid_qty > 0 and bid_px < ask:
                orders.append(Order(sym, int(bid_px), int(bid_qty)))
            if ask_qty > 0 and ask_px > bid:
                orders.append(Order(sym, int(ask_px), -int(ask_qty)))

            if orders:
                result[sym] = orders

            net_delta_after_taker += delta * pos

        # Optional cheap hedge in the underlying when spread tight.
        under_spread = under_ask - under_bid
        if under_spread <= HEDGE_SPREAD_MAX and abs(net_delta_after_taker) >= HEDGE_TRIGGER_DELTA:
            target_under = int(max(min(-round(net_delta_after_taker * HEDGE_RATIO), UNDER_LIMIT), -UNDER_LIMIT))
            cur_under = int(state.position.get(UNDER, 0))
            diff = target_under - cur_under
            diff = int(max(min(diff, HEDGE_MAX_STEP), -HEDGE_MAX_STEP))
            if diff > 0:
                qty = min(diff, UNDER_LIMIT - cur_under)
                if qty > 0:
                    result.setdefault(UNDER, []).append(Order(UNDER, int(under_ask), int(qty)))
            elif diff < 0:
                qty = min(-diff, UNDER_LIMIT + cur_under)
                if qty > 0:
                    result.setdefault(UNDER, []).append(Order(UNDER, int(under_bid), -int(qty)))

        return result, 0, json.dumps(td)
