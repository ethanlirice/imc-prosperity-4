"""
Round 3 trader v4 — VEV_5300 Black-Scholes bid-side accumulation.

Minimal one-product options implementation:
- Product: VEV_5300 only
- Fair value: Black-Scholes call price from an offline-fitted vol smile in moneyness
- Microstructure overlay: historical VEV_5300 prints are almost entirely
  seller-initiated at the bid, and this strike usually has enough spread to
  improve the bid by one tick while staying below BS fair
- Positioning: long/flat only; buy below fair, flatten when the bid catches back up
"""

import json
import math
from datamodel import TradingState, Order

UNDERLYING = "VELVETFRUIT_EXTRACT"
PRODUCT = "VEV_5300"
STRIKE = 5300
POSITION_LIMIT = 300

SMILE_A = 0.0283
SMILE_B = 0.0025
SMILE_C = 0.2395
FAIR_BIAS = 1.3112

LIVE_START_DAYS_TO_EXPIRY = 8.0
TICKS_PER_DAY = 1_000_000.0
DAYS_PER_YEAR = 365.0

OPEN_IMPROVED_BID_MARGIN = 0.35
TAKE_ASK_MARGIN = 0.75
CLOSE_BID_MARGIN = 0.1

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


def get_time_to_expiry_years(timestamp: int) -> float:
    elapsed_days = timestamp / TICKS_PER_DAY
    return (LIVE_START_DAYS_TO_EXPIRY - elapsed_days) / DAYS_PER_YEAR


class Trader:

    def run(self, state: TradingState):
        try:
            trader_data = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            trader_data = {}

        orders = self.trade_vev_5300(state)
        result = {PRODUCT: orders} if orders else {}
        return result, 0, json.dumps(trader_data)

    def trade_vev_5300(self, state: TradingState):
        underlying_depth = state.order_depths.get(UNDERLYING)
        option_depth = state.order_depths.get(PRODUCT)
        if underlying_depth is None or option_depth is None:
            return []
        if not underlying_depth.buy_orders or not underlying_depth.sell_orders:
            return []
        if not option_depth.buy_orders or not option_depth.sell_orders:
            return []

        time_to_expiry = get_time_to_expiry_years(state.timestamp)
        if time_to_expiry <= 0:
            return []

        underlying_mid = (max(underlying_depth.buy_orders) + min(underlying_depth.sell_orders)) / 2
        best_bid = max(option_depth.buy_orders)
        best_ask = min(option_depth.sell_orders)

        moneyness = math.log(STRIKE / underlying_mid) / math.sqrt(time_to_expiry)
        implied_vol = SMILE_A * moneyness * moneyness + SMILE_B * moneyness + SMILE_C
        fair_value = black_scholes_call(underlying_mid, STRIKE, time_to_expiry, implied_vol) + FAIR_BIAS

        bid_edge = fair_value - best_bid
        ask_edge = fair_value - best_ask

        position = state.position.get(PRODUCT, 0)
        buy_capacity = POSITION_LIMIT - position
        sell_capacity = POSITION_LIMIT + position
        orders = []

        # Exit inventory once the market bid has caught back up to fair.
        if position > 0 and bid_edge <= CLOSE_BID_MARGIN:
            close_qty = min(option_depth.buy_orders[best_bid], sell_capacity, position)
            if close_qty > 0:
                orders.append(Order(PRODUCT, best_bid, -close_qty))
                position -= close_qty
                buy_capacity = POSITION_LIMIT - position
                sell_capacity = POSITION_LIMIT + position

        # If the visible ask is clearly below fair, take it immediately.
        if buy_capacity > 0 and ask_edge >= TAKE_ASK_MARGIN:
            take_qty = min(-option_depth.sell_orders[best_ask], buy_capacity)
            if take_qty > 0:
                orders.append(Order(PRODUCT, best_ask, take_qty))
                position += take_qty
                buy_capacity = POSITION_LIMIT - position

        # Main signal: improve the bid by one tick when that improved price is still below fair.
        improved_bid = min(best_bid + 1, best_ask - 1)
        improved_bid_edge = fair_value - improved_bid
        if buy_capacity > 0 and improved_bid_edge >= OPEN_IMPROVED_BID_MARGIN:
            orders.append(Order(PRODUCT, improved_bid, buy_capacity))

        return orders
