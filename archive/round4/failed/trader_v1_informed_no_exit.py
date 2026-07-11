from typing import Dict, List

try:
    from datamodel import Order, OrderDepth, Trade, TradingState
except ModuleNotFoundError:
    from trader_factory.core.datamodel import Order, OrderDepth, Trade, TradingState


INFORMED_TRADER = "Mark 14"

POSITION_LIMITS: Dict[str, int] = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300,
    "VEV_4500": 300,
    "VEV_5000": 300,
    "VEV_5100": 300,
    "VEV_5200": 300,
    "VEV_5300": 300,
    "VEV_5400": 300,
    "VEV_5500": 300,
    "VEV_6000": 300,
    "VEV_6500": 300,
}

# Products where Mark 14 cleared the Round 4 informed-trader screen with
# meaningful total edge. VEV_5200 passed the percentage threshold but had only
# 33 signals and negligible total edge, so it stays out of v1.
COPY_PRODUCTS = {
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
    "VEV_4000",
}

COPY_SIZE: Dict[str, int] = {
    "HYDROGEL_PACK": 10,
    "VELVETFRUIT_EXTRACT": 10,
    "VEV_4000": 10,
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
    def check_informed_trader(
        self,
        state: TradingState,
        symbol: str,
        orders_out: List[Order],
    ) -> bool:
        depth = state.order_depths.get(symbol)
        if depth is None:
            return False

        net_signal = 0
        for trade in state.market_trades.get(symbol, []):
            if trade.buyer == INFORMED_TRADER:
                net_signal += abs(trade.quantity)
            if trade.seller == INFORMED_TRADER:
                net_signal -= abs(trade.quantity)

        if net_signal == 0:
            return False

        limit = POSITION_LIMITS[symbol]
        pos = state.position.get(symbol, 0)
        qty = min(COPY_SIZE[symbol], limit - pos if net_signal > 0 else pos + limit)
        if qty <= 0:
            return False

        if net_signal > 0:
            ask = best_ask(depth)
            if ask is None:
                return False
            orders_out.append(Order(symbol, ask, qty))
        else:
            bid = best_bid(depth)
            if bid is None:
                return False
            orders_out.append(Order(symbol, bid, -qty))

        return True

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        for symbol in COPY_PRODUCTS:
            if symbol not in state.order_depths:
                continue
            orders: List[Order] = []
            self.check_informed_trader(state, symbol, orders)
            if orders:
                result[symbol] = orders

        conversions = 0
        trader_data = ""
        return result, conversions, trader_data
