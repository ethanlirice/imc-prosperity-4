from datamodel import Order, TradingState
import importlib.util
import os
from typing import Dict, List

BASE_PATH = os.path.join(os.path.dirname(__file__), "base-strategy-free-alpha-side-gated-mr-mm-reanchor-v11.py")
if not os.path.exists(BASE_PATH):
    BASE_PATH = os.path.join(os.getcwd(), "strategies", "round5", "base-strategy-free-alpha-side-gated-mr-mm-reanchor-v11.py")
SPEC = importlib.util.spec_from_file_location("round5_v11_base", BASE_PATH)
base = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(base)

LIMIT = base.LIMIT


def env_set(name: str):
    raw = os.environ.get(name, "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def env_int_map(name: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    raw = os.environ.get(name, "")
    for part in raw.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        try:
            result[key.strip()] = int(value.strip())
        except Exception:
            pass
    return result


def env_float_map(name: str) -> Dict[str, float]:
    result: Dict[str, float] = {}
    raw = os.environ.get(name, "")
    for part in raw.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        try:
            result[key.strip()] = float(value.strip())
        except Exception:
            pass
    return result


def top_volume(depth, side: int) -> int:
    if side > 0:
        if not depth.buy_orders:
            return 0
        return int(depth.buy_orders[max(depth.buy_orders.keys())])
    if not depth.sell_orders:
        return 0
    return -int(depth.sell_orders[min(depth.sell_orders.keys())])


BASE_MM_PRODUCTS = set(base.MM_PRODUCTS)
BASE_MM_PRODUCTS = BASE_MM_PRODUCTS - set(base.REANCHOR_PRODUCTS) - set(base.FREE_ALPHA_PRODUCTS) - set(base.ACTIVE_RESIDUAL_TARGETS)
BASE_MM_PRODUCTS.add("ROBOT_LAUNDRY")
MM_PRODUCTS = (set(BASE_MM_PRODUCTS) | env_set("ADD_MM_PRODUCTS")) - env_set("DROP_MM_PRODUCTS")
MM_WITH_OWNED_PRODUCTS = env_set("MM_WITH_OWNED_PRODUCTS")
MM_BID_OFF_PRODUCTS = (set(base.MM_BID_OFF_PRODUCTS) | env_set("MM_BID_OFF_PRODUCTS")) - env_set("MM_BID_ON_PRODUCTS")
MM_ASK_OFF_PRODUCTS = (set(base.MM_ASK_OFF_PRODUCTS) | env_set("MM_ASK_OFF_PRODUCTS")) - env_set("MM_ASK_ON_PRODUCTS")
MM_SIZE = int(os.environ.get("MM_SIZE", str(LIMIT)))
MM_SIZE_BY_PRODUCT = dict(base.MM_SIZE_BY_PRODUCT)
MM_SIZE_BY_PRODUCT.update(env_int_map("MM_SIZE_BY_PRODUCT"))
MM_FLAT_ONLY_PRODUCTS = env_set("MM_FLAT_ONLY_PRODUCTS")
MM_REDUCE_ONLY_PRODUCTS = env_set("MM_REDUCE_ONLY_PRODUCTS")
MM_INVENTORY_REDUCE_THRESHOLD = int(os.environ.get("MM_INVENTORY_REDUCE_THRESHOLD", "999"))
MM_OFFSET = int(os.environ.get("MM_OFFSET", "0"))
MM_OFFSET_BY_PRODUCT = env_int_map("MM_OFFSET_BY_PRODUCT")
MM_IMB_THRESHOLD = float(os.environ.get("MM_IMB_THRESHOLD", "0"))
MM_IMB_THRESHOLD_BY_PRODUCT = env_float_map("MM_IMB_THRESHOLD_BY_PRODUCT")
MM_IMB_FILTER_PRODUCTS = env_set("MM_IMB_FILTER_PRODUCTS")
MM_MIN_SPREAD = int(os.environ.get("MM_MIN_SPREAD", "1"))
MM_MIN_SPREAD_BY_PRODUCT = env_int_map("MM_MIN_SPREAD_BY_PRODUCT")


class Trader(base.Trader):
    def run(self, state: TradingState):
        memory = self.load_memory(state.traderData)
        memory["tick"] = int(memory.get("tick", 0)) + 1
        tick = int(memory["tick"])
        sleeves = memory.setdefault("res", {})
        orders: Dict[str, List[Order]] = {}
        for product in base.REANCHOR_PRODUCTS:
            product_orders = self.reanchor_orders(state, memory, product)
            if product_orders:
                orders[product] = product_orders
        for product in base.FREE_ALPHA_PRODUCTS:
            if product in base.REANCHOR_PRODUCTS:
                continue
            product_orders = base.free_alpha_orders(state, product)
            if product_orders:
                orders[product] = product_orders
        for spec in base.SPECS:
            target = str(spec["target"])
            if target in base.PASSIVE_TARGET_OVERRIDES or target in base.FREE_ALPHA_PRODUCTS or target in base.REANCHOR_PRODUCTS:
                continue
            sleeve = sleeves.setdefault(target, {})
            position = int(state.position.get(target, 0))
            if position == 0:
                sleeve.clear()
            resid = self.residual(state, spec)
            if resid is None:
                continue
            target_orders: List[Order] = []
            entry_tick = int(sleeve.get("entry_tick", tick))
            should_exit = False
            if position != 0:
                timed_out = tick - entry_tick >= int(spec["hold"])
                zero_cross = False
                if spec["exit"] == "zero":
                    zero_cross = (position > 0 and resid >= 0.0) or (position < 0 and resid <= 0.0)
                if timed_out or zero_cross:
                    should_exit = True
            if should_exit:
                order = self.close_order(state, target, position)
                if order is not None:
                    target_orders.append(order)
                    sleeve.clear()
            elif position == 0:
                z = resid / float(spec["sigma"])
                direction = 0
                if z <= -float(spec["entry_z"]):
                    direction = 1
                elif z >= float(spec["entry_z"]):
                    direction = -1
                if direction != 0:
                    order = self.entry_order(state, target, direction)
                    if order is not None and order.quantity != 0:
                        target_orders.append(order)
                        sleeve["dir"] = direction
                        sleeve["entry_tick"] = tick
                        sleeve["entry_resid"] = round(float(resid), 4)
            if target_orders:
                orders[target] = target_orders
        for product in base.MR_PRODUCTS:
            if product in base.REANCHOR_PRODUCTS:
                continue
            spec = base.BASE_MR_SPECS.get(product)
            if spec is None:
                continue
            allow_trade = product not in orders and product not in base.FREE_ALPHA_PRODUCTS and product not in base.ACTIVE_RESIDUAL_TARGETS
            product_orders = self.mr_orders(state, memory, product, spec, tick, allow_trade)
            if product_orders:
                orders[product] = product_orders
        for product, depth in state.order_depths.items():
            if product not in MM_PRODUCTS:
                continue
            if product in orders:
                continue
            if product in base.ACTIVE_RESIDUAL_TARGETS:
                continue
            if product in base.REANCHOR_PRODUCTS and product not in MM_WITH_OWNED_PRODUCTS:
                continue
            if product in base.FREE_ALPHA_PRODUCTS and product not in MM_WITH_OWNED_PRODUCTS:
                continue
            bid, ask = base.best_bid_ask(depth)
            if bid is None or ask is None or bid >= ask:
                continue
            min_spread = int(MM_MIN_SPREAD_BY_PRODUCT.get(product, MM_MIN_SPREAD))
            if ask - bid < min_spread:
                continue
            position = int(state.position.get(product, 0))
            max_size = int(MM_SIZE_BY_PRODUCT.get(product, MM_SIZE))
            if max_size <= 0:
                continue
            can_buy = product not in MM_BID_OFF_PRODUCTS
            can_sell = product not in MM_ASK_OFF_PRODUCTS
            if product in MM_FLAT_ONLY_PRODUCTS and position != 0:
                can_buy = False
                can_sell = False
            if product in MM_REDUCE_ONLY_PRODUCTS or abs(position) >= MM_INVENTORY_REDUCE_THRESHOLD:
                can_buy = position < 0
                can_sell = position > 0
            threshold = float(MM_IMB_THRESHOLD_BY_PRODUCT.get(product, MM_IMB_THRESHOLD))
            if threshold > 0 and (not MM_IMB_FILTER_PRODUCTS or product in MM_IMB_FILTER_PRODUCTS):
                bid_volume = top_volume(depth, 1)
                ask_volume = top_volume(depth, -1)
                total_volume = bid_volume + ask_volume
                if total_volume > 0:
                    imbalance = (bid_volume - ask_volume) / total_volume
                    if imbalance <= -threshold:
                        can_buy = False
                    if imbalance >= threshold:
                        can_sell = False
            offset = int(MM_OFFSET_BY_PRODUCT.get(product, MM_OFFSET))
            buy_price = int(bid - offset)
            sell_price = int(ask + offset)
            if buy_price >= ask:
                can_buy = False
            if sell_price <= bid:
                can_sell = False
            product_orders: List[Order] = []
            buy_qty = min(LIMIT - position, max_size)
            if buy_qty > 0 and can_buy:
                product_orders.append(Order(product, buy_price, buy_qty))
            sell_qty = min(LIMIT + position, max_size)
            if sell_qty > 0 and can_sell:
                product_orders.append(Order(product, sell_price, -sell_qty))
            if product_orders:
                orders[product] = product_orders
        return orders, 0, self.save_memory(memory)
