import math
from typing import Dict, List, Optional

import jsonpickle
from datamodel import Order, OrderDepth, TradingState


LIMIT = 10
PENNY_SIZE = 5
FAIR_ALPHA = 0.08
FAIR_EDGE = 1.0
INVENTORY_SKEW = 0.55
TREND_GATE = 18.0

USE_V5_PRODUCTS = {
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "MICROCHIP_OVAL",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "PANEL_1X4",
    "PANEL_2X2",
    "PEBBLES_L",
    "PEBBLES_S",
    "ROBOT_IRONING",
    "UV_VISOR_AMBER",
}

FAIR_PRODUCTS = {"PEBBLES_L"}

SELECTED = [
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PANEL_2X2",
    "PANEL_2X4",
    "PEBBLES_L",
    "PEBBLES_S",
    "PEBBLES_XL",
    "ROBOT_DISHES",
    "ROBOT_IRONING",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_POLYESTER",
    "SLEEP_POD_SUEDE",
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ASTRO_BLACK",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_VOID_BLUE",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
    "UV_VISOR_YELLOW",
]

ML = {
    "OXYGEN_SHAKE_GARLIC": {
        "q": 0.60,
        "mean": [
            0.1818181818,
            0.3631363136,
            0.904490449,
            1.8104310431,
            14.0453045305,
            -0.0034726759,
            18.2591259126,
            -18.2854285429,
        ],
        "scale": [
            11.1317782543,
            15.7824207169,
            25.2089384524,
            35.8075244898,
            1.5074730353,
            0.2978849111,
            4.4281510056,
            4.381330654,
        ],
        "coef": [
            0.0065544877,
            0.0133072666,
            -0.0051592792,
            -0.0042823853,
            -0.0264587087,
            0.0199232035,
            0.1458620188,
            0.1409653857,
        ],
        "intercept": 0.0001534159,
    },
}

BASE_PRODUCTS = [
    product
    for product in SELECTED
    if product not in ML and product != "ROBOT_IRONING" and product not in FAIR_PRODUCTS
]


def best_bid_ask(depth: OrderDepth):
    if not depth.buy_orders or not depth.sell_orders:
        return None
    bid = max(depth.buy_orders)
    ask = min(depth.sell_orders)
    if bid >= ask:
        return None
    return bid, ask


def mid(depth: OrderDepth) -> Optional[float]:
    bba = best_bid_ask(depth)
    if bba is None:
        return None
    bid, ask = bba
    return (bid + ask) / 2.0


def load_data(raw: str) -> Dict:
    if not raw:
        return {}
    try:
        data = jsonpickle.decode(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def dump_data(data: Dict) -> str:
    return jsonpickle.encode(data, unpicklable=False)


class V5PebblesAndStructureTrader:
    def position(self, state: TradingState, product: str) -> int:
        return int(state.position.get(product, 0))

    def remaining_buy(self, state: TradingState, product: str) -> int:
        return max(0, LIMIT - self.position(state, product))

    def remaining_sell(self, state: TradingState, product: str) -> int:
        return max(0, LIMIT + self.position(state, product))

    def used_order_position(self, orders: List[Order]) -> int:
        return sum(order.quantity for order in orders)

    def add_buy(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        product: str,
        price: int,
        size: int,
    ) -> None:
        orders = orders_by_product[product]
        available = self.remaining_buy(state, product) - max(0, self.used_order_position(orders))
        qty = min(size, available)
        if qty > 0:
            orders.append(Order(product, int(price), int(qty)))

    def add_sell(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        product: str,
        price: int,
        size: int,
    ) -> None:
        orders = orders_by_product[product]
        available = self.remaining_sell(state, product) + min(0, self.used_order_position(orders))
        qty = min(size, available)
        if qty > 0:
            orders.append(Order(product, int(price), -int(qty)))

    def trade_penny_products(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        products: List[str],
    ) -> None:
        for product in products:
            if product not in USE_V5_PRODUCTS:
                continue
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            bba = best_bid_ask(depth)
            if bba is None:
                continue
            bid, ask = bba
            if ask - bid > 1:
                buy_px = bid + 1
                sell_px = ask - 1
            else:
                buy_px = bid
                sell_px = ask
            self.add_buy(state, orders_by_product, product, buy_px, PENNY_SIZE)
            self.add_sell(state, orders_by_product, product, sell_px, PENNY_SIZE)

    def stable_fair(self, data: Dict, product: str, current_mid: float) -> float:
        key = "fair_" + product
        previous = data.get(key)
        if previous is None:
            fair = current_mid
        else:
            fair = (1.0 - FAIR_ALPHA) * float(previous) + FAIR_ALPHA * current_mid
        data[key] = fair

        history_key = "fair_hist_" + product
        history = data.get(history_key, [])
        history.append(current_mid)
        data[history_key] = history[-31:]
        return fair

    def trade_stable_fair_products(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        data: Dict,
        products,
    ) -> None:
        for product in products:
            if product not in USE_V5_PRODUCTS:
                continue
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            bba = best_bid_ask(depth)
            current_mid = mid(depth)
            if bba is None or current_mid is None:
                continue

            bid, ask = bba
            fair = self.stable_fair(data, product, current_mid)
            history = data.get("fair_hist_" + product, [])
            trend = history[-1] - history[0] if len(history) >= 31 else 0.0
            position = self.position(state, product)
            reservation = fair - INVENTORY_SKEW * position
            buy_px = bid + 1 if ask - bid > 1 else bid
            sell_px = ask - 1 if ask - bid > 1 else ask

            if buy_px <= reservation - FAIR_EDGE and not (trend < -TREND_GATE and position >= 0):
                self.add_buy(state, orders_by_product, product, buy_px, PENNY_SIZE)
            if sell_px >= reservation + FAIR_EDGE and not (trend > TREND_GATE and position <= 0):
                self.add_sell(state, orders_by_product, product, sell_px, PENNY_SIZE)

    def features(self, mids: List[float], spread: int, obi: float, bidv: int, askv: int) -> List[float]:
        vals = []
        for lag in (1, 2, 5, 10):
            vals.append(mids[-1] - mids[-1 - lag] if len(mids) > lag else 0.0)
        vals.extend([spread, obi, bidv, askv])
        return vals

    def ml_probability(self, product: str, vals: List[float]) -> float:
        cfg = ML[product]
        z = cfg["intercept"]
        for x, mu, scale, coef in zip(vals, cfg["mean"], cfg["scale"], cfg["coef"]):
            z += ((x - mu) / scale) * coef
        return 1.0 / (1.0 + math.exp(-z))

    def trade_ml_product(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        data: Dict,
        product: str,
    ) -> None:
        if product not in USE_V5_PRODUCTS:
            return
        depth = state.order_depths.get(product)
        if depth is None:
            return
        bba = best_bid_ask(depth)
        current_mid = mid(depth)
        if bba is None or current_mid is None:
            return

        bid, ask = bba
        bidv = max(0, int(depth.buy_orders.get(bid, 0)))
        askv = max(0, -int(depth.sell_orders.get(ask, 0)))
        total = bidv + askv
        obi = (bidv - askv) / total if total > 0 else 0.0

        key = "ml_mid_" + product
        mids = data.get(key, [])
        mids.append(current_mid)
        mids = mids[-11:]
        data[key] = mids
        if len(mids) < 11:
            return

        prob_up = self.ml_probability(product, self.features(mids, ask - bid, obi, bidv, askv))
        threshold = ML[product]["q"]
        buy_px = bid + 1 if ask - bid > 1 else bid
        sell_px = ask - 1 if ask - bid > 1 else ask

        if prob_up > threshold:
            self.add_buy(state, orders_by_product, product, buy_px, LIMIT)
        elif prob_up < 1.0 - threshold:
            self.add_sell(state, orders_by_product, product, sell_px, LIMIT)

    def trade_robot_mean_reversion(
        self,
        state: TradingState,
        orders_by_product: Dict[str, List[Order]],
        data: Dict,
    ) -> None:
        product = "ROBOT_IRONING"
        if product not in USE_V5_PRODUCTS:
            return
        depth = state.order_depths.get(product)
        if depth is None:
            return
        bba = best_bid_ask(depth)
        current_mid = mid(depth)
        if bba is None or current_mid is None:
            return

        key = "last_mid_" + product
        previous = data.get(key)
        data[key] = current_mid
        if previous is None:
            return

        last_ret = current_mid - float(previous)
        if abs(last_ret) < 0.5:
            return

        bid, ask = bba
        buy_px = bid + 1 if ask - bid > 1 else bid
        sell_px = ask - 1 if ask - bid > 1 else ask
        if last_ret > 0:
            self.add_sell(state, orders_by_product, product, sell_px, LIMIT)
        elif last_ret < 0:
            self.add_buy(state, orders_by_product, product, buy_px, LIMIT)

    def run(self, state: TradingState):
        data = load_data(state.traderData)
        orders_by_product: Dict[str, List[Order]] = {product: [] for product in state.order_depths}

        self.trade_penny_products(state, orders_by_product, BASE_PRODUCTS)
        self.trade_stable_fair_products(state, orders_by_product, data, FAIR_PRODUCTS)
        for product in ML:
            self.trade_ml_product(state, orders_by_product, data, product)
        self.trade_robot_mean_reversion(state, orders_by_product, data)

        filtered = {product: orders for product, orders in orders_by_product.items() if orders}
        return filtered, 0, dump_data(data)


class Trader:
    def __init__(self) -> None:
        self.v5 = V5PebblesAndStructureTrader()

    def run(self, state: TradingState):
        return self.v5.run(state)
