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

# Offline-fitted mid IV smile (R3 days 0-2, strikes 5000-5500).
SMILE_A = 0.0283
SMILE_B = 0.0025
SMILE_C = 0.2395

# Per-strike bias correction for wall_mid - BS_theo (so BS_theo + bias ~= wall_mid on average).
VEV_5300_BIAS = 1.3112

# Backtest proxy clock: day 0 starts at 8d. (Live final is 5d; keep that change isolated later.)
START_DAYS_TO_EXPIRY = 8.0
TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

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


def time_to_expiry_years(timestamp: int) -> float:
    elapsed_days = timestamp / TICKS_PER_DAY
    return (START_DAYS_TO_EXPIRY - elapsed_days) / DAYS_PER_YEAR


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

        oo = self.trade_vev_5300_bs(state)
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

    def trade_vev_5300_bs(self, state: TradingState):
        ud = state.order_depths.get(UNDER)
        vd = state.order_depths.get(VEV_5300)
        if ud is None or vd is None:
            return []
        if not ud.buy_orders or not ud.sell_orders:
            return []
        if not vd.buy_orders or not vd.sell_orders:
            return []

        T = time_to_expiry_years(state.timestamp)
        if T <= 0:
            return []

        S = (max(ud.buy_orders.keys()) + min(ud.sell_orders.keys())) / 2
        best_bid = max(vd.buy_orders.keys())
        best_ask = min(vd.sell_orders.keys())

        m = math.log(VEV_5300_STRIKE / S) / math.sqrt(T)
        iv = SMILE_A * m * m + SMILE_B * m + SMILE_C
        fair = black_scholes_call(S, VEV_5300_STRIKE, T, iv) + VEV_5300_BIAS

        position = state.position.get(VEV_5300, 0)
        buy_cap = VEV_5300_LIMIT - position
        sell_cap = VEV_5300_LIMIT + position

        orders = []

        bid_edge = fair - best_bid
        ask_edge = fair - best_ask

        # Exit long inventory when the bid catches back up to fair.
        if position > 0 and bid_edge <= CLOSE_BID_MARGIN:
            close_qty = min(vd.buy_orders[best_bid], sell_cap, position)
            if close_qty > 0:
                orders.append(Order(VEV_5300, best_bid, -close_qty))
                position -= close_qty
                buy_cap = VEV_5300_LIMIT - position

        # If the visible ask is materially below fair, lift it.
        if buy_cap > 0 and ask_edge >= TAKE_ASK_MARGIN:
            take_qty = min(-vd.sell_orders[best_ask], buy_cap)
            if take_qty > 0:
                orders.append(Order(VEV_5300, best_ask, take_qty))
                position += take_qty
                buy_cap = VEV_5300_LIMIT - position

        # Main signal: improve the bid by one tick when still below fair by margin.
        improved_bid = min(best_bid + 1, best_ask - 1)
        improved_edge = fair - improved_bid
        if buy_cap > 0 and improved_edge >= OPEN_IMPROVED_BID_MARGIN and improved_bid < best_ask:
            orders.append(Order(VEV_5300, int(improved_bid), int(buy_cap)))

        return orders
