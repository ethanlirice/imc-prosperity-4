"""
Round 3 trader v1 — HYDROGEL_PACK wall MM only.

Highest-confidence single-product baseline:
- Wall-based MM with raw wall_mid (no fixed anchor; HYDROGEL drifts ~9990, range 9891-10079).
- Take asks <= wall_mid - 1; take bids >= wall_mid + 1.
- Cover-take at fair when it reduces inventory.
- Make at penny-inside the wall, with L1 penny override when L1 is inside fair.

VELVETFRUIT_EXTRACT, VEV_*, vouchers: not yet implemented (one product per version).
"""

import json
from datamodel import TradingState, Order

HYDROGEL = "HYDROGEL_PACK"
HYDROGEL_LIMIT = 200


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
        return result, 0, json.dumps(td)

    def trade_hydrogel(self, state, td):
        depth = state.order_depths.get(HYDROGEL)
        if depth is None:
            return []
        has_bids = bool(depth.buy_orders)
        has_asks = bool(depth.sell_orders)
        if not (has_bids and has_asks):
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
