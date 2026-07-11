import json
import math
from datamodel import TradingState, Order


HYDROGEL = "HYDROGEL_PACK"
HYDROGEL_LIMIT = 200

UNDER = "VELVETFRUIT_EXTRACT"
UNDER_LIMIT = 200

VEV_4000 = "VEV_4000"
VEV_4000_LIMIT = 300

VEV_5300 = "VEV_5300"
VEV_5300_LIMIT = 300
VEV_5300_STRIKE = 5300

# Use the liquid strikes to infer the start-of-session days-left from the surface.
SURFACE_STRIKES = [5200, 5300, 5400, 5500]

# Offline-fitted IV smile in m = log(K/S)/sqrt(T).
SMILE_A = 0.0283
SMILE_B = 0.0025
SMILE_C = 0.2395

TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

# BS execution (long/flat only).
EMA_ALPHA = 0.02
EMA_WARMUP = 100
OPEN_IMPROVED_BID_MARGIN = 0.35
TAKE_ASK_MARGIN = 0.75
CLOSE_BID_MARGIN = 0.10

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
            trader_data = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            trader_data = {}

        result = {}

        ho = self.trade_wall_mm(state, HYDROGEL, HYDROGEL_LIMIT)
        if ho:
            result[HYDROGEL] = ho

        vo = self.trade_wall_mm(state, VEV_4000, VEV_4000_LIMIT)
        if vo:
            result[VEV_4000] = vo

        uo = self.trade_spread_mm(state, UNDER, UNDER_LIMIT)
        if uo:
            result[UNDER] = uo

        oo = self.trade_vev_5300_bs(state, trader_data)
        if oo:
            result[VEV_5300] = oo

        return result, 0, json.dumps(trader_data)

    def trade_wall_mm(self, state: TradingState, symbol: str, limit: int):
        depth = state.order_depths.get(symbol)
        if depth is None or not depth.buy_orders or not depth.sell_orders:
            return []

        position = state.position.get(symbol, 0)
        bid_wall = min(depth.buy_orders.keys())
        ask_wall = max(depth.sell_orders.keys())
        wall_mid = (bid_wall + ask_wall) / 2

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

    def trade_spread_mm(self, state: TradingState, symbol: str, limit: int):
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

        if position > 0:
            bid_px = best_bid
        if position < 0:
            ask_px = best_ask

        orders = []
        if buy_cap > 0 and bid_px < best_ask:
            orders.append(Order(symbol, int(bid_px), int(buy_cap)))
        if sell_cap > 0 and ask_px > best_bid:
            orders.append(Order(symbol, int(ask_px), -int(sell_cap)))
        return orders

    def infer_start_days(self, state: TradingState) -> float | None:
        ud = state.order_depths.get(UNDER)
        if ud is None or not ud.buy_orders or not ud.sell_orders:
            return None
        S = (max(ud.buy_orders.keys()) + min(ud.sell_orders.keys())) / 2

        # Gather surface mids at this tick.
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
                m = math.log(K / S) / math.sqrt(T)
                iv = smile_iv(m)
                theo = black_scholes_call(S, K, T, iv)
                e = mid - theo
                sse += e * e
            if best_sse is None or sse < best_sse:
                best_sse = sse
                best_start = start_days
        return best_start

    def trade_vev_5300_bs(self, state: TradingState, trader_data: dict):
        ud = state.order_depths.get(UNDER)
        vd = state.order_depths.get(VEV_5300)
        if ud is None or vd is None:
            return []
        if not ud.buy_orders or not ud.sell_orders:
            return []
        if not vd.buy_orders or not vd.sell_orders:
            return []

        start_days = trader_data.get("start_days")
        if start_days is None:
            start_days = self.infer_start_days(state)
            if start_days is None:
                return []
            trader_data["start_days"] = start_days

        elapsed_days = state.timestamp / TICKS_PER_DAY
        T_days = start_days - elapsed_days
        if T_days <= 0:
            return []
        T = T_days / DAYS_PER_YEAR

        S = (max(ud.buy_orders.keys()) + min(ud.sell_orders.keys())) / 2
        best_bid = max(vd.buy_orders.keys())
        best_ask = min(vd.sell_orders.keys())

        m = math.log(VEV_5300_STRIKE / S) / math.sqrt(T)
        iv = smile_iv(m)
        theo = black_scholes_call(S, VEV_5300_STRIKE, T, iv)

        mid = (best_bid + best_ask) / 2
        diff = mid - theo

        old_ema = trader_data.get("vev5300_ema")
        if old_ema is None:
            ema = diff
        else:
            ema = EMA_ALPHA * diff + (1.0 - EMA_ALPHA) * old_ema
        trader_data["vev5300_ema"] = ema

        warm = trader_data.get("vev5300_warm", 0) + 1
        trader_data["vev5300_warm"] = warm
        if warm < EMA_WARMUP:
            return []

        fair = theo + ema

        position = state.position.get(VEV_5300, 0)
        buy_cap = VEV_5300_LIMIT - position
        sell_cap = VEV_5300_LIMIT + position

        orders = []

        bid_edge = fair - best_bid
        ask_edge = fair - best_ask

        if position > 0 and bid_edge <= CLOSE_BID_MARGIN:
            close_qty = min(vd.buy_orders[best_bid], sell_cap, position)
            if close_qty > 0:
                orders.append(Order(VEV_5300, best_bid, -close_qty))
                position -= close_qty
                buy_cap = VEV_5300_LIMIT - position

        if buy_cap > 0 and ask_edge >= TAKE_ASK_MARGIN:
            take_qty = min(-vd.sell_orders[best_ask], buy_cap)
            if take_qty > 0:
                orders.append(Order(VEV_5300, best_ask, take_qty))
                position += take_qty
                buy_cap = VEV_5300_LIMIT - position

        improved_bid = min(best_bid + 1, best_ask - 1)
        improved_edge = fair - improved_bid
        if buy_cap > 0 and improved_edge >= OPEN_IMPROVED_BID_MARGIN and improved_bid < best_ask:
            orders.append(Order(VEV_5300, int(improved_bid), int(buy_cap)))

        return orders
