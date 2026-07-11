from datamodel import Order, OrderDepth, TradingState
import importlib.util
import os
from typing import Dict, List, Optional, Tuple

# Primary R5 backtest at default ENTRY_EDGE=20, LIMIT=10: +478,380
# Sweep best broad setting ENTRY_EDGE=200, LIMIT=10: +742,005 but day 4 only +23,686.
# Research-only experiment: load the supplied "free alpha" table and treat each
# tuple as a five-bucket fair path [base, base+d1, ..., base+d4].

LIMIT = int(os.environ.get("FREE_ALPHA_LIMIT", "10"))
ENTRY_EDGE = float(os.environ.get("FREE_ALPHA_ENTRY_EDGE", "20.0"))
EXIT_EDGE = float(os.environ.get("FREE_ALPHA_EXIT_EDGE", "5.0"))


def load_free_alpha():
    here = os.path.dirname(__file__)
    path = os.path.abspath(os.path.join(here, "..", "..", "analysis", "round5-free-alpha", "20_free_alpha_probe.py"))
    spec = importlib.util.spec_from_file_location("free_alpha_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.FREE_ALPHA


FREE_ALPHA = load_free_alpha()


def best_bid_ask(depth: OrderDepth) -> Tuple[Optional[int], Optional[int]]:
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
    return bid, ask


def fair_path(product: str, timestamp: int) -> Optional[float]:
    vals = FREE_ALPHA.get(product)
    if vals is None:
        return None
    base = float(vals[0])
    path = [base, base + float(vals[1]), base + float(vals[2]), base + float(vals[3]), base + float(vals[4])]
    bucket = int(timestamp * 5 // 1000000)
    if bucket < 0:
        bucket = 0
    if bucket > 4:
        bucket = 4
    return path[bucket]


def take_to_target(product: str, depth: OrderDepth, position: int, target: int) -> List[Order]:
    delta = target - position
    if delta == 0:
        return []
    if delta > 0:
        ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
        if ask is None:
            return []
        qty = min(delta, -int(depth.sell_orders.get(ask, 0)))
        if qty <= 0:
            return []
        return [Order(product, ask, qty)]
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    if bid is None:
        return []
    qty = min(-delta, int(depth.buy_orders.get(bid, 0)))
    if qty <= 0:
        return []
    return [Order(product, bid, -qty)]


class Trader:
    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}
        for product, depth in state.order_depths.items():
            fair = fair_path(product, int(state.timestamp))
            if fair is None:
                continue
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None:
                continue
            position = int(state.position.get(product, 0))
            target = position
            if ask < fair - ENTRY_EDGE:
                target = LIMIT
            elif bid > fair + ENTRY_EDGE:
                target = -LIMIT
            else:
                mid = 0.5 * (bid + ask)
                if abs(mid - fair) <= EXIT_EDGE:
                    target = 0
            product_orders = take_to_target(product, depth, position, target)
            if product_orders:
                orders[product] = product_orders
        return orders, 0, ""
