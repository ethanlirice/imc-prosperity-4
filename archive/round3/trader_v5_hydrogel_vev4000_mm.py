import json
from datamodel import TradingState, Order


HYDROGEL = "HYDROGEL_PACK"
HYDROGEL_LIMIT = 200

VEV_4000 = "VEV_4000"
VEV_4000_LIMIT = 300


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
