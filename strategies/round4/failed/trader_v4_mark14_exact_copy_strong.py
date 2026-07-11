from typing import Dict, List

try:
    from datamodel import Order, OrderDepth, Trade, TradingState
except ModuleNotFoundError:
    from trader_factory.core.datamodel import Order, OrderDepth, Trade, TradingState


INFORMED_TRADER = "Mark 14"
COPY_PRODUCTS = {"HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_4000"}

POSITION_LIMITS: Dict[str, int] = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300,
}


def best_bid(depth: OrderDepth):
    if not depth.buy_orders:
        return None
    return max(depth.buy_orders.keys())


def best_ask(depth: OrderDepth):
    if not depth.sell_orders:
        return None
    return min(depth.sell_orders.keys())


class Trader:
    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        for symbol in COPY_PRODUCTS:
            depth = state.order_depths.get(symbol)
            if depth is None:
                continue

            pos = int(state.position.get(symbol, 0))
            limit = POSITION_LIMITS[symbol]
            orders: List[Order] = []

            for trade in state.market_trades.get(symbol, []):
                qty = abs(int(trade.quantity))
                if qty <= 0:
                    continue

                if trade.buyer == INFORMED_TRADER:
                    ask = best_ask(depth)
                    size = min(qty, limit - pos)
                    if ask is not None and size > 0:
                        orders.append(Order(symbol, ask, size))
                        pos += size

                if trade.seller == INFORMED_TRADER:
                    bid = best_bid(depth)
                    size = min(qty, pos + limit)
                    if bid is not None and size > 0:
                        orders.append(Order(symbol, bid, -size))
                        pos -= size

            if orders:
                result[symbol] = orders

        return result, 0, ""
