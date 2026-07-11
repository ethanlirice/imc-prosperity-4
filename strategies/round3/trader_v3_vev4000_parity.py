"""
Round 3 trader v3 — VEV_4000 parity only.

Single-product, single-signal implementation:
- Trade only VEV_4000.
- Fair value = VELVETFRUIT_EXTRACT mid - 4000.
- Take obviously cheap asks and rich bids versus parity.
- Clear inventory at parity to free capacity.
"""

import json
import math
from datamodel import TradingState, Order

UNDERLYING = "VELVETFRUIT_EXTRACT"
OPTION = "VEV_4000"
STRIKE = 4000
LIMIT = 300


class Trader:

    def run(self, state: TradingState):
        try:
            td = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            td = {}

        result = {}
        orders = self.trade_vev_4000(state, td)
        if orders:
            result[OPTION] = orders
        return result, 0, json.dumps(td)

    def mid_from_depth(self, depth):
        has_bids = bool(depth.buy_orders)
        has_asks = bool(depth.sell_orders)
        if has_bids and has_asks:
            return (max(depth.buy_orders.keys()) + min(depth.sell_orders.keys())) / 2
        if has_bids:
            return float(max(depth.buy_orders.keys()))
        if has_asks:
            return float(min(depth.sell_orders.keys()))
        return None

    def trade_vev_4000(self, state, td):
        option_depth = state.order_depths.get(OPTION)
        underlying_depth = state.order_depths.get(UNDERLYING)
        if option_depth is None or underlying_depth is None:
            return []

        fair_mid = self.mid_from_depth(underlying_depth)
        if fair_mid is None:
            return []

        fair = fair_mid - STRIKE
        td["vev4000_last_fair"] = fair

        fair_bid = math.floor(fair)
        fair_ask = math.ceil(fair)

        position = state.position.get(OPTION, 0)
        buy_cap = LIMIT - position
        sell_cap = LIMIT + position
        orders = []

        for price in sorted(option_depth.sell_orders.keys()):
            avail = -option_depth.sell_orders[price]
            if price <= fair_bid:
                take = min(avail, buy_cap)
            elif price <= fair_ask and position < 0:
                take = min(avail, -position, buy_cap)
            else:
                break

            if take > 0:
                orders.append(Order(OPTION, price, take))
                buy_cap -= take
                position += take
                if buy_cap <= 0:
                    break

        for price in sorted(option_depth.buy_orders.keys(), reverse=True):
            avail = option_depth.buy_orders[price]
            if price >= fair_ask:
                take = min(avail, sell_cap)
            elif price >= fair_bid and position > 0:
                take = min(avail, position, sell_cap)
            else:
                break

            if take > 0:
                orders.append(Order(OPTION, price, -take))
                sell_cap -= take
                position -= take
                if sell_cap <= 0:
                    break

        return orders
