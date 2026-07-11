"""
Round 3 trader v13 — fundamentals + microstructure + Black-Scholes options MM.

Core PnL (backtest-verified on historical days 0-2):
- HYDROGEL_PACK: wall-based MM (proven, 30k+ in worse mode)
- VEV_4000: wall-based MM with parity-arb overlay vs VELVETFRUIT_EXTRACT
- VELVETFRUIT_EXTRACT: spread capture with inventory skew

Options module (VEV_5200/5300/5400/5500):
- Black-Scholes with an offline parabolic IV smile in m = log(K/S)/sqrt(T)
- Per-strike EMA absorbs persistent (mid - theo) bias
- Day-aware TTE: at session start, infer start_days from the surface (5 live / 6/7/8 historical)
- Quote inside L1 with smile-aware fair value; take obvious mispricings
"""

import json
import math
from datamodel import TradingState, Order


HYDROGEL = "HYDROGEL_PACK"
HYDROGEL_LIMIT = 200

UNDER = "VELVETFRUIT_EXTRACT"
UNDER_LIMIT = 200

VEV_4000 = "VEV_4000"
VEV_4000_LIMIT = 300
VEV_4000_STRIKE = 4000

# Active multi-strike options book.
OPTION_STRIKES = [5000, 5100, 5200, 5300, 5400, 5500]
OPTION_LIMITS = {5000: 300, 5100: 300, 5200: 300, 5300: 300, 5400: 300, 5500: 300}

# Used to infer start-of-session days-left.
SURFACE_STRIKES = [5200, 5300, 5400, 5500]

# Offline-fitted parabolic IV smile in m = log(K/S)/sqrt(T).
SMILE_A = 0.028689
SMILE_B = 0.002819
SMILE_C = 0.239411

# Offline per-strike persistent bias = E[mid - BS_theo(smile_iv)] over D0/D1/D2.
# Used to seed the per-strike EMA so the trader starts trading from tick 0 with a calibrated fair.
INIT_BIAS = {
    5000: -0.005,
    5100: -0.016,
    5200: +0.770,
    5300: +2.000,
    5400: -2.206,
    5500: +0.516,
    4500: 0.011,
    4000: 0.012,
}

TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

# Options EMA / scalp thresholds.
EMA_ALPHA = 0.05
EMA_WARMUP = 0

# Per-strike take/make thresholds (in price ticks). Fair = theo + ema_bias.
TAKE_MARGIN = 0.3
MAKE_INSIDE_MARGIN = 0.0  # post if quote is on the right side of fair at all

# VEV_4000 parity arbitrage thresholds.
PARITY_TAKE_MARGIN = 0.4
PARITY_LIMIT_FRACTION = 1.0  # use full limit on parity arb

SQRT_2 = math.sqrt(2.0)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT_2))


def black_scholes_call(spot: float, strike: int, time_to_expiry: float, volatility: float) -> float:
    if spot <= 0 or time_to_expiry <= 0 or volatility <= 0:
        return max(spot - strike, 0.0)
    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + 0.5 * volatility * volatility * time_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    return spot * norm_cdf(d1) - strike * norm_cdf(d2)


def smile_iv(m: float) -> float:
    return SMILE_A * m * m + SMILE_B * m + SMILE_C


class Trader:

    def run(self, state: TradingState):
        try:
            td = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            td = {}

        result = {}

        ho = self.trade_wall_mm(state, HYDROGEL, HYDROGEL_LIMIT, td)
        if ho:
            result[HYDROGEL] = ho

        ud = state.order_depths.get(UNDER)
        spot = None
        if ud is not None and ud.buy_orders and ud.sell_orders:
            spot = (max(ud.buy_orders.keys()) + min(ud.sell_orders.keys())) / 2

        # VEV_4000: wall MM with parity-arb take overlay (using underlying spot).
        v4o = self.trade_vev4000(state, spot, td)
        if v4o:
            result[VEV_4000] = v4o

        uo = self.trade_spread_mm(state, UNDER, UNDER_LIMIT, td)
        if uo:
            result[UNDER] = uo

        # Options book: only run when underlying mid is observable.
        if spot is not None:
            start_days = td.get("start_days")
            if start_days is None:
                start_days = self.infer_start_days(state, spot)
                if start_days is not None:
                    td["start_days"] = start_days
            if start_days is not None:
                t_years = self.compute_tte(start_days, state.timestamp)
                if t_years > 0:
                    for K in OPTION_STRIKES:
                        sym = f"VEV_{K}"
                        opo = self.trade_option_mm(state, td, sym, K, spot, t_years)
                        if opo:
                            result[sym] = opo

        return result, 0, json.dumps(td)

    def trade_wall_mm(self, state: TradingState, symbol: str, limit: int, td=None):
        depth = state.order_depths.get(symbol)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        position = state.position.get(symbol, 0)
        bid_wall = min(depth.buy_orders.keys())
        ask_wall = max(depth.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2

        # Mean-reversion shift on the FAIR used for take/make decisions.
        # Pulls the trade-fair toward the rolling mean (200-tick EMA of wall_mid),
        # exploiting VR(1000) ≈ 0.33 strong MR on HYDROGEL_PACK (and similar products).
        if td is not None:
            mr_key = f"mr_{symbol}"
            mr_alpha = 0.005  # tuned: 200-tick EMA
            old = td.get(mr_key)
            if old is None:
                ema_mid = wall_mid
            else:
                ema_mid = mr_alpha * wall_mid + (1 - mr_alpha) * float(old)
            td[mr_key] = ema_mid
            dev = wall_mid - ema_mid
            # Bias trade-fair partway toward the rolling mean. Cap to avoid overstepping.
            mr_pull = max(min(0.3 * dev, 10.0), -10.0)
            wall_mid = wall_mid - mr_pull

        orders = []
        buy_cap = limit - position
        sell_cap = limit + position

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

        if buy_cap > 0:
            orders.append(Order(symbol, bid_price, buy_cap))
        if sell_cap > 0:
            orders.append(Order(symbol, ask_price, -sell_cap))

        return orders

    def trade_spread_mm(self, state: TradingState, symbol: str, limit: int, td=None):
        depth = state.order_depths.get(symbol)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        best_bid = max(depth.buy_orders.keys())
        best_ask = min(depth.sell_orders.keys())
        if best_bid >= best_ask:
            return []

        position = state.position.get(symbol, 0)
        buy_cap = limit - position
        sell_cap = limit + position

        bid_px = min(best_bid + 1, best_ask - 1)
        ask_px = max(best_ask - 1, best_bid + 1)

        mid = (best_bid + best_ask) / 2.0

        # MR overlay on VELVETFRUIT_EXTRACT (VR(1000)=0.35, strong MR).
        # Pulls our quote toward the rolling mean side.
        mr_offset = 0.0
        if td is not None:
            mr_key = f"mr_{symbol}"
            mr_alpha = 0.005
            old = td.get(mr_key)
            if old is None:
                ema_mid = mid
            else:
                ema_mid = mr_alpha * mid + (1 - mr_alpha) * float(old)
            td[mr_key] = ema_mid
            dev = mid - ema_mid
            mr_offset = max(min(0.3 * dev, 5.0), -5.0)

        # Position skew.
        if position > 0:
            bid_px = best_bid
        if position < 0:
            ask_px = best_ask

        # Apply MR shift: above mean → push quotes down (sell more aggressively).
        if mr_offset > 0:
            ask_px = max(int(round(ask_px - mr_offset)), best_bid + 1)
        elif mr_offset < 0:
            bid_px = min(int(round(bid_px - mr_offset)), best_ask - 1)

        orders = []
        if buy_cap > 0 and bid_px < best_ask:
            orders.append(Order(symbol, int(bid_px), int(buy_cap)))
        if sell_cap > 0 and ask_px > best_bid:
            orders.append(Order(symbol, int(ask_px), -int(sell_cap)))
        return orders

    def infer_start_days(self, state: TradingState, spot):
        mids = {}
        for K in SURFACE_STRIKES:
            sym = f"VEV_{K}"
            d = state.order_depths.get(sym)
            if d is None or not d.buy_orders or not d.sell_orders:
                return None
            bid = max(d.buy_orders.keys())
            ask = min(d.sell_orders.keys())
            mids[K] = (bid + ask) / 2

        elapsed_days = state.timestamp / TICKS_PER_DAY
        candidates = [5.0, 6.0, 7.0, 8.0]
        best_sse = None
        best_start = None
        for start_days in candidates:
            T_days = start_days - elapsed_days
            if T_days <= 0:
                continue
            T = T_days / DAYS_PER_YEAR
            sse = 0.0
            for K, mid in mids.items():
                m = math.log(K / spot) / math.sqrt(T)
                iv = smile_iv(m)
                theo = black_scholes_call(spot, K, T, iv)
                e = mid - theo
                sse += e * e
            if best_sse is None or sse < best_sse:
                best_sse = sse
                best_start = start_days
        return best_start

    def compute_tte(self, start_days, timestamp):
        elapsed_days = timestamp / TICKS_PER_DAY
        T_days = start_days - elapsed_days
        if T_days <= 0:
            return 0.0
        return T_days / DAYS_PER_YEAR

    def trade_vev4000(self, state, spot, td=None):
        """VEV_4000 wall MM with parity-arb take overlay.
        Parity fair = spot - 4000. When option price strays >= PARITY_TAKE_MARGIN
        from parity, do an aggressive take at the parity-cheap side."""
        depth = state.order_depths.get(VEV_4000)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        position = state.position.get(VEV_4000, 0)
        bid_wall = min(depth.buy_orders.keys())
        ask_wall = max(depth.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2

        # MR overlay (VR(1000)=0.22 — strongest MR of any active product).
        if td is not None:
            mr_key = "mr_vev4000"
            mr_alpha = 0.005
            old = td.get(mr_key)
            if old is None:
                ema_mid = wall_mid
            else:
                ema_mid = mr_alpha * wall_mid + (1 - mr_alpha) * float(old)
            td[mr_key] = ema_mid
            dev = wall_mid - ema_mid
            mr_pull = max(min(0.3 * dev, 10.0), -10.0)
            wall_mid = wall_mid - mr_pull

        orders = []
        buy_cap = VEV_4000_LIMIT - position
        sell_cap = VEV_4000_LIMIT + position

        # Parity-arb takes (fire only when spot is observable and option dislocated).
        if spot is not None:
            parity = spot - VEV_4000_STRIKE
            for price in sorted(depth.sell_orders.keys()):
                avail = -depth.sell_orders[price]
                if price <= parity - PARITY_TAKE_MARGIN:
                    take = min(avail, buy_cap)
                    if take > 0:
                        orders.append(Order(VEV_4000, price, take))
                        buy_cap -= take
                        position += take
                else:
                    break
            for price in sorted(depth.buy_orders.keys(), reverse=True):
                avail = depth.buy_orders[price]
                if price >= parity + PARITY_TAKE_MARGIN:
                    take = min(avail, sell_cap)
                    if take > 0:
                        orders.append(Order(VEV_4000, price, -take))
                        sell_cap -= take
                        position -= take
                else:
                    break

        # Standard wall MM takes (vs wall_mid).
        for price in sorted(depth.sell_orders.keys()):
            avail = -depth.sell_orders[price]
            if price <= wall_mid - 1:
                take = min(avail, buy_cap)
            elif price <= wall_mid and position < 0:
                take = min(avail, -position, buy_cap)
            else:
                break
            if take > 0:
                orders.append(Order(VEV_4000, price, take))
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
                orders.append(Order(VEV_4000, price, -take))
                sell_cap -= take
                position -= take
                if sell_cap <= 0:
                    break

        # Make orders.
        bid_price = int(bid_wall) + 1
        ask_price = int(ask_wall) - 1

        best_bid = max(depth.buy_orders.keys())
        best_ask = min(depth.sell_orders.keys())

        if best_bid + 1 < wall_mid:
            bid_price = max(bid_price, best_bid + 1)
        if best_ask - 1 > wall_mid:
            ask_price = min(ask_price, best_ask - 1)

        if buy_cap > 0:
            orders.append(Order(VEV_4000, bid_price, buy_cap))
        if sell_cap > 0:
            orders.append(Order(VEV_4000, ask_price, -sell_cap))

        return orders

    def trade_option_mm(self, state, td, sym, K, spot, t_years):
        """Multi-strike options market making with smile-aware fair value.
        - Compute BS theo using parabolic IV smile in moneyness.
        - Maintain per-strike EMA of (mid - theo) to absorb persistent bias.
        - Fair = theo + ema. Take when L1 quote crosses fair by TAKE_MARGIN.
        - Make inside L1 when there's room and the quote stays on the right side of fair.
        """
        d = state.order_depths.get(sym)
        if d is None or not d.buy_orders or not d.sell_orders:
            return []

        best_bid = max(d.buy_orders.keys())
        best_ask = min(d.sell_orders.keys())
        if best_bid >= best_ask:
            return []

        mid = (best_bid + best_ask) / 2

        m = math.log(K / spot) / math.sqrt(t_years)
        iv = smile_iv(m)
        theo = black_scholes_call(spot, K, t_years, iv)

        diff = mid - theo
        ema_key = f"opt_ema_{K}"
        warm_key = f"opt_warm_{K}"

        old_ema = td.get(ema_key)
        if old_ema is None:
            # Seed from offline-calibrated per-strike bias so we trade from tick 0.
            seed = INIT_BIAS.get(K, diff)
            ema = EMA_ALPHA * diff + (1.0 - EMA_ALPHA) * seed
        else:
            ema = EMA_ALPHA * diff + (1.0 - EMA_ALPHA) * float(old_ema)
        td[ema_key] = ema

        warm = int(td.get(warm_key, 0)) + 1
        td[warm_key] = warm
        if warm < EMA_WARMUP:
            return []

        fair = theo + ema
        position = state.position.get(sym, 0)
        limit = OPTION_LIMITS[K]
        buy_cap = limit - position
        sell_cap = limit + position

        orders = []
        spread = best_ask - best_bid

        # TAKE: ask cheap vs fair → buy.
        if buy_cap > 0 and best_ask <= fair - TAKE_MARGIN:
            avail = -d.sell_orders[best_ask]
            qty = min(avail, buy_cap)
            if qty > 0:
                orders.append(Order(sym, best_ask, qty))
                position += qty
                buy_cap -= qty

        # TAKE: bid rich vs fair → sell.
        if sell_cap > 0 and best_bid >= fair + TAKE_MARGIN:
            avail = d.buy_orders[best_bid]
            qty = min(avail, sell_cap)
            if qty > 0:
                orders.append(Order(sym, best_bid, -qty))
                position -= qty
                sell_cap -= qty

        # Inventory-aware sizing: shrink the side that worsens inventory.
        inv_frac = position / float(limit) if limit else 0.0
        bid_size = max(int(round(buy_cap * (1.0 - max(0.0, inv_frac)))), 0)
        ask_size = max(int(round(sell_cap * (1.0 - max(0.0, -inv_frac)))), 0)

        # MAKE: post inside L1 when spread allows and our quote stays on the right side of fair.
        if spread >= 2:
            inside_bid = best_bid + 1
            inside_ask = best_ask - 1
            if bid_size > 0 and inside_bid <= fair - MAKE_INSIDE_MARGIN and inside_bid < best_ask:
                orders.append(Order(sym, inside_bid, bid_size))
            if ask_size > 0 and inside_ask >= fair + MAKE_INSIDE_MARGIN and inside_ask > best_bid:
                orders.append(Order(sym, inside_ask, -ask_size))
        else:
            # Spread = 1: queue at L1 only when our quote is still profitable vs fair.
            if bid_size > 0 and best_bid <= fair - MAKE_INSIDE_MARGIN:
                orders.append(Order(sym, best_bid, bid_size))
            if ask_size > 0 and best_ask >= fair + MAKE_INSIDE_MARGIN:
                orders.append(Order(sym, best_ask, -ask_size))

        return orders
