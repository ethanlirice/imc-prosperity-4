"""
Round 3 trader v2 — HYDROGEL_PACK wall MM + VEV_5500 IV scalping.

VEV_5500 IV scalping rationale (verified on data/ROUND3 days 0-2):
- Offline-fit parabolic vol smile in moneyness m_t = log(K/S)/sqrt(T):
    iv = 0.029290 * m_t^2 + 0.002971 * m_t + 0.239378
- BS theoretical from this smile gives a "fair" price; mid - theo deviation
  has AC(1) ~= -0.32 on returns and VR(1000) = 0.007 (extreme mean reversion).
- We track an EMA of (wall_mid - BS_theo) per voucher to absorb the
  per-strike persistent bias (5500 mean +0.52). The signal is
  (best_bid or best_ask) vs (theo + ema_diff +/- thr).
- Scalp by taking against best_bid/best_ask whenever the L1 quote is
  better than the rolling fair by THR_OPEN; close at THR_CLOSE.

Position scaling: scalp size = limit (300) — we want max exposure when the
signal fires, since VEV_5500 spread is 1 tick and per-trade edge is ~0.5-1.
"""

import json
import math
from datamodel import TradingState, Order

HYDROGEL = "HYDROGEL_PACK"
HYDROGEL_LIMIT = 200
UNDERLYING = "VELVETFRUIT_EXTRACT"

VEV_5500 = "VEV_5500"
VEV_5500_STRIKE = 5500
VEV_5500_LIMIT = 300

# Parabolic vol smile fitted on R3 days 0-2, NTM strikes 5000-5500, 100-tick samples.
SMILE_A = 0.029290
SMILE_B = 0.002971
SMILE_C = 0.239378

# TTE clock: backtester data starts at TTE = 8 days for day 0 at timestamp 0.
# Backtester monotonically increments timestamp across days (1M ticks per day).
# tte (years) = (8 - timestamp/1e6) / 365
TTE_DAYS_AT_START = 8.0
TTE_DAYS_PER_YEAR = 365.0
TICKS_PER_DAY = 1_000_000

# IV scalping params
IV_EMA_ALPHA = 0.02   # ~100-tick EMA window
IV_EMA_WARMUP = 100   # ticks before signals enable
THR_OPEN_5500 = 0.5   # take when |best_X - rolling_fair| > THR_OPEN
THR_CLOSE_5500 = 0.0  # close when crossed; close at zero deviation

_SQRT_2 = math.sqrt(2.0)


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / _SQRT_2))


def _bs_call(S, K, T, sigma):
    if sigma <= 0 or T <= 0 or S <= 0:
        return max(0.0, S - K)
    sqrt_t = math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    return S * _norm_cdf(d1) - K * _norm_cdf(d2)


def _tte_years(timestamp):
    elapsed_days = timestamp / TICKS_PER_DAY
    return (TTE_DAYS_AT_START - elapsed_days) / TTE_DAYS_PER_YEAR


class Trader:

    def run(self, state: TradingState):
        try:
            td = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            td = {}
        result = {}

        ho = self.trade_hydrogel(state, td)
        if ho:
            result[HYDROGEL] = ho

        vo = self.trade_vev_5500(state, td)
        if vo:
            result[VEV_5500] = vo

        return result, 0, json.dumps(td)

    def trade_hydrogel(self, state, td):
        depth = state.order_depths.get(HYDROGEL)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        position = state.position.get(HYDROGEL, 0)
        bid_wall = min(depth.buy_orders.keys())
        ask_wall = max(depth.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2

        orders = []
        buy_cap = HYDROGEL_LIMIT - position
        sell_cap = HYDROGEL_LIMIT + position

        for p in sorted(depth.sell_orders.keys()):
            avail = -depth.sell_orders[p]
            if p <= wall_mid - 1:
                take = min(avail, buy_cap)
            elif p <= wall_mid and position < 0:
                take = min(avail, -position, buy_cap)
            else:
                break
            if take > 0:
                orders.append(Order(HYDROGEL, p, take))
                buy_cap -= take
                position += take
                if buy_cap <= 0:
                    break

        for p in sorted(depth.buy_orders.keys(), reverse=True):
            avail = depth.buy_orders[p]
            if p >= wall_mid + 1:
                take = min(avail, sell_cap)
            elif p >= wall_mid and position > 0:
                take = min(avail, position, sell_cap)
            else:
                break
            if take > 0:
                orders.append(Order(HYDROGEL, p, -take))
                sell_cap -= take
                position -= take
                if sell_cap <= 0:
                    break

        bid_price = int(bid_wall) + 1
        ask_price = int(ask_wall) - 1

        bp = max(depth.buy_orders.keys())
        bv = depth.buy_orders[bp]
        over = bp + 1
        if bv > 1 and over < wall_mid:
            bid_price = max(bid_price, over)
        elif bp < wall_mid:
            bid_price = max(bid_price, bp)

        sp = min(depth.sell_orders.keys())
        sv = -depth.sell_orders[sp]
        under = sp - 1
        if sv > 1 and under > wall_mid:
            ask_price = min(ask_price, under)
        elif sp > wall_mid:
            ask_price = min(ask_price, sp)

        if buy_cap > 0:
            orders.append(Order(HYDROGEL, bid_price, buy_cap))
        if sell_cap > 0:
            orders.append(Order(HYDROGEL, ask_price, -sell_cap))
        return orders

    def trade_vev_5500(self, state, td):
        ud = state.order_depths.get(UNDERLYING)
        vd = state.order_depths.get(VEV_5500)
        if ud is None or vd is None:
            return []
        if not ud.buy_orders or not ud.sell_orders:
            return []
        if not vd.buy_orders or not vd.sell_orders:
            return []

        T = _tte_years(state.timestamp)
        if T <= 1e-6:
            return []

        S = (max(ud.buy_orders.keys()) + min(ud.sell_orders.keys())) / 2

        bid_wall = min(vd.buy_orders.keys())
        ask_wall = max(vd.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2
        best_bid = max(vd.buy_orders.keys())
        best_ask = min(vd.sell_orders.keys())

        m_t = math.log(VEV_5500_STRIKE / S) / math.sqrt(T)
        smile_iv = SMILE_A * m_t * m_t + SMILE_B * m_t + SMILE_C
        theo = _bs_call(S, VEV_5500_STRIKE, T, smile_iv)
        diff = wall_mid - theo

        old_ema = td.get("ev55_ema_diff")
        if old_ema is None:
            new_ema = diff
            td["ev55_ema_diff"] = new_ema
            warm = td.get("ev55_warm", 0) + 1
            td["ev55_warm"] = warm
            return []

        new_ema = IV_EMA_ALPHA * diff + (1.0 - IV_EMA_ALPHA) * old_ema
        td["ev55_ema_diff"] = new_ema
        warm = td.get("ev55_warm", 0) + 1
        td["ev55_warm"] = warm
        if warm < IV_EMA_WARMUP:
            return []

        rolling_fair = theo + new_ema
        position = state.position.get(VEV_5500, 0)
        buy_cap = VEV_5500_LIMIT - position
        sell_cap = VEV_5500_LIMIT + position

        orders = []

        # OPEN: take when L1 quote is past rolling fair by THR_OPEN
        if best_bid > rolling_fair + THR_OPEN_5500 and sell_cap > 0:
            avail = vd.buy_orders[best_bid]
            qty = min(avail, sell_cap)
            if qty > 0:
                orders.append(Order(VEV_5500, best_bid, -qty))
                sell_cap -= qty
                position -= qty

        if best_ask < rolling_fair - THR_OPEN_5500 and buy_cap > 0:
            avail = -vd.sell_orders[best_ask]
            qty = min(avail, buy_cap)
            if qty > 0:
                orders.append(Order(VEV_5500, best_ask, qty))
                buy_cap -= qty
                position += qty

        # CLOSE: unwind when crossed back to within THR_CLOSE
        if position > 0 and best_bid >= rolling_fair + THR_CLOSE_5500:
            avail = vd.buy_orders[best_bid]
            qty = min(avail, position)
            if qty > 0:
                orders.append(Order(VEV_5500, best_bid, -qty))

        elif position < 0 and best_ask <= rolling_fair - THR_CLOSE_5500:
            avail = -vd.sell_orders[best_ask]
            qty = min(avail, -position)
            if qty > 0:
                orders.append(Order(VEV_5500, best_ask, qty))

        return orders
