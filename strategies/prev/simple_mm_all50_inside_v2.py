from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple

# Primary R5 backtest: prosperity4btx ... 5 --merge-pnl = +401,415
# Days: D2 +118,766 / D3 +105,130 / D4 +177,518
# Framework control: pure passive market making on all 50 products, one tick
# inside both sides, no fair value, no active mean reversion.

LIMIT = 10
MIN_SPREAD_FOR_INSIDE = 3


def best_bid_ask(depth: OrderDepth) -> Tuple[Optional[int], Optional[int]]:
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
    return bid, ask


class Trader:
    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}
        for product, depth in state.order_depths.items():
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None or ask - bid < MIN_SPREAD_FOR_INSIDE:
                continue
            bid_px = bid + 1
            ask_px = ask - 1
            if bid_px >= ask_px:
                continue

            position = int(state.position.get(product, 0))
            product_orders: List[Order] = []
            buy_qty = LIMIT - position
            if buy_qty > 0:
                product_orders.append(Order(product, bid_px, buy_qty))
            sell_qty = LIMIT + position
            if sell_qty > 0:
                product_orders.append(Order(product, ask_px, -sell_qty))
            if product_orders:
                orders[product] = product_orders
        return orders, 0, ""
