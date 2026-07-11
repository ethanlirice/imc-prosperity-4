from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple

# Primary R5 backtest: prosperity4btx ... 5 --merge-pnl = +476,800
# Days: D2 +141,311 / D3 +134,250 / D4 +201,238
# Framework control: pure passive market making on all 50 products at best
# displayed bid/ask, no fair value, no active mean reversion.

LIMIT = 10


def best_bid_ask(depth: OrderDepth) -> Tuple[Optional[int], Optional[int]]:
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
    return bid, ask


class Trader:
    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}
        for product, depth in state.order_depths.items():
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None or bid >= ask:
                continue

            position = int(state.position.get(product, 0))
            product_orders: List[Order] = []
            buy_qty = LIMIT - position
            if buy_qty > 0:
                product_orders.append(Order(product, bid, buy_qty))
            sell_qty = LIMIT + position
            if sell_qty > 0:
                product_orders.append(Order(product, ask, -sell_qty))
            if product_orders:
                orders[product] = product_orders
        return orders, 0, ""
