from datamodel import Order, OrderDepth, TradingState
import json
import os
from typing import Any, Dict, List, Optional, Tuple

# Research-only configurable copy of base-strategy-free-alpha-selected-v5.py.
# Uses environment variables to run owner/side/threshold ablations. Do not
# submit this file directly; promote a standalone variant after testing.

LIMIT = 10
FREE_ALPHA_ENTRY_EDGE = 80.0
FREE_ALPHA_EXIT_EDGE = 5.0
FREE_ALPHA_ENTRY_EDGE_BY_PRODUCT = {
    "GALAXY_SOUNDS_DARK_MATTER": 40.0,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 200.0,
    "PANEL_2X2": 200.0,
    "PEBBLES_L": 200.0,
    "SLEEP_POD_COTTON": 200.0,
    "SNACKPACK_PISTACHIO": 120.0,
    "SNACKPACK_RASPBERRY": 120.0,
    "SNACKPACK_VANILLA": 200.0,
    "UV_VISOR_MAGENTA": 40.0,
    "UV_VISOR_YELLOW": 200.0,
}

BASE_FREE_ALPHA_PRODUCTS = {
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "PANEL_2X2",
    "PEBBLES_L",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_YELLOW",
}


FREE_ALPHA_ALL = {
    "GALAXY_SOUNDS_BLACK_HOLES": (11193.8333, -68.0000, 241.3333, 36.3333, 1151.8333),
    "GALAXY_SOUNDS_DARK_MATTER": (10428.5000, -201.5000, -346.1667, -438.5000, 89.3333),
    "GALAXY_SOUNDS_PLANETARY_RINGS": (10888.3333, -155.1667, -291.6667, 25.3333, -120.0000),
    "GALAXY_SOUNDS_SOLAR_FLAMES": (10660.5000, 290.0000, 485.5000, 537.8333, 277.3333),
    "GALAXY_SOUNDS_SOLAR_WINDS": (10115.8333, -5.5000, 457.5000, 305.5000, 83.5000),
    "MICROCHIP_CIRCLE": (9140.8333, -154.1667, -31.8333, 6.8333, 127.3333),
    "MICROCHIP_OVAL": (8889.6667, -186.0000, -385.1667, -686.8333, -1488.5000),
    "MICROCHIP_RECTANGLE": (9080.6667, -268.1667, -85.0000, -334.0000, -403.5000),
    "MICROCHIP_SQUARE": (12789.5000, -77.3333, 270.1667, 1295.3333, 1205.3333),
    "MICROCHIP_TRIANGLE": (9911.5000, -84.5000, -30.3333, -405.6667, -693.3333),
    "OXYGEN_SHAKE_CHOCOLATE": (9599.6667, -51.3333, -327.3333, -100.1667, 240.6667),
    "OXYGEN_SHAKE_EVENING_BREATH": (9286.6667, 136.6667, 160.0000, 53.3333, -193.3333),
    "OXYGEN_SHAKE_GARLIC": (11250.3333, 80.8333, 134.1667, 837.6667, 1299.3333),
    "OXYGEN_SHAKE_MINT": (9939.6667, -60.8333, -251.0000, -304.6667, 52.1667),
    "OXYGEN_SHAKE_MORNING_BREATH": (10178.3333, 223.6667, 156.3333, -142.5000, -149.6667),
    "PANEL_1X2": (9092.6667, -391.0000, -339.5000, -409.1667, -99.0000),
    "PANEL_1X4": (9939.6667, -387.8333, -425.3333, -538.3333, -269.8333),
    "PANEL_2X2": (9762.1667, -231.1667, -417.1667, 114.6667, -192.0000),
    "PANEL_2X4": (10726.6667, -52.3333, 181.8333, 531.1667, 790.1667),
    "PANEL_4X4": (9977.8333, 402.5000, 233.3333, -322.3333, -291.6667),
    "PEBBLES_L": (10381.6667, -27.0000, 159.1667, -231.8333, -297.0000),
    "PEBBLES_M": (10028.6667, -336.0000, -28.8333, 421.5000, 229.8333),
    "PEBBLES_S": (9386.8333, -189.1667, -214.3333, -458.5000, -651.3333),
    "PEBBLES_XL": (11894.3333, 551.5000, 302.1667, 1300.0000, 2045.3333),
    "PEBBLES_XS": (8308.1667, 0.8333, -217.8333, -1030.6667, -1326.1667),
    "ROBOT_DISHES": (10015.6667, -126.0000, -235.1667, 41.0000, 405.5000),
    "ROBOT_IRONING": (9000.0000, 170.0000, 176.6667, -310.0000, -720.0000),
    "ROBOT_LAUNDRY": (9903.5000, -60.0000, -68.5000, 24.6667, -239.5000),
    "ROBOT_MOPPING": (10661.5000, 120.0000, -7.3333, 392.0000, 530.1667),
    "ROBOT_VACUUMING": (9550.5000, -255.3333, -440.0000, -322.8333, -570.5000),
    "SLEEP_POD_COTTON": (11105.1667, 265.3333, 277.3333, 463.3333, 471.5000),
    "SLEEP_POD_LAMB_WOOL": (10396.3333, 32.0000, 207.6667, 457.5000, 272.0000),
    "SLEEP_POD_NYLON": (9529.0000, -75.6667, 79.5000, 218.5000, 242.0000),
    "SLEEP_POD_POLYESTER": (11555.5000, -63.1667, 439.1667, 71.5000, 655.6667),
    "SLEEP_POD_SUEDE": (11074.5000, 190.5000, -64.0000, 370.0000, 603.0000),
    "SNACKPACK_CHOCOLATE": (9921.3333, -7.6667, 21.5000, 36.1667, -113.6667),
    "SNACKPACK_PISTACHIO": (9634.8333, -41.3333, -22.5000, -243.8333, -298.1667),
    "SNACKPACK_RASPBERRY": (10120.3333, 2.5000, -79.3333, 53.1667, 103.1667),
    "SNACKPACK_STRAWBERRY": (10413.8333, 89.3333, 260.1667, 178.1667, 297.0000),
    "SNACKPACK_VANILLA": (10023.0000, 23.1667, -26.1667, -74.0000, 109.3333),
    "TRANSLATOR_ASTRO_BLACK": (9774.5000, -53.0000, -237.3333, -417.5000, -352.6667),
    "TRANSLATOR_ECLIPSE_CHARCOAL": (9954.0000, 41.5000, 22.3333, -280.5000, -88.1667),
    "TRANSLATOR_GRAPHITE_MIST": (10130.3333, 327.6667, 311.0000, -148.8333, -70.0000),
    "TRANSLATOR_SPACE_GRAY": (9869.3333, -297.5000, -562.6667, -472.8333, -519.6667),
    "TRANSLATOR_VOID_BLUE": (10596.3333, 178.1667, 19.8333, 214.1667, 509.1667),
    "UV_VISOR_AMBER": (8627.3333, -410.3333, -487.1667, -629.5000, -954.5000),
    "UV_VISOR_MAGENTA": (10969.6667, -95.6667, 12.1667, -169.5000, 501.5000),
    "UV_VISOR_ORANGE": (10152.0000, 164.8333, 314.0000, 558.3333, -226.5000),
    "UV_VISOR_RED": (10624.5000, 323.1667, 487.6667, 637.8333, 574.0000),
    "UV_VISOR_YELLOW": (11211.6667, -56.0000, -301.1667, -491.1667, 16.0000),
}


def env_set(name: str) -> set:
    raw = os.environ.get(name, "")
    if not raw:
        return set()
    return set(part.strip() for part in raw.split(",") if part.strip())


def env_thresholds(name: str) -> Dict[str, float]:
    raw = os.environ.get(name, "")
    out: Dict[str, float] = {}
    if not raw:
        return out
    for part in raw.split(","):
        item = part.strip()
        if not item or ":" not in item:
            continue
        product, value = item.split(":", 1)
        try:
            out[product.strip()] = float(value)
        except Exception:
            pass
    return out


ADD_FREE_ALPHA_PRODUCTS = env_set("ADD_FREE_ALPHA_PRODUCTS")
DROP_FREE_ALPHA_PRODUCTS = env_set("DROP_FREE_ALPHA_PRODUCTS")
DROP_MM_PRODUCTS = env_set("DROP_MM_PRODUCTS")
MM_BID_OFF_PRODUCTS = env_set("MM_BID_OFF_PRODUCTS")
MM_ASK_OFF_PRODUCTS = env_set("MM_ASK_OFF_PRODUCTS")
MM_ONLY_PRODUCTS = env_set("MM_ONLY_PRODUCTS")
FREE_ALPHA_ENTRY_EDGE_BY_PRODUCT.update(env_thresholds("FREE_ALPHA_EDGE_OVERRIDES"))
FREE_ALPHA_PRODUCTS = (BASE_FREE_ALPHA_PRODUCTS | ADD_FREE_ALPHA_PRODUCTS) - DROP_FREE_ALPHA_PRODUCTS
FREE_ALPHA = FREE_ALPHA_ALL

SPECS = [
    {
        "target": "GALAXY_SOUNDS_SOLAR_FLAMES",
        "components": [
            "GALAXY_SOUNDS_DARK_MATTER",
            "GALAXY_SOUNDS_BLACK_HOLES",
            "GALAXY_SOUNDS_PLANETARY_RINGS",
            "GALAXY_SOUNDS_SOLAR_WINDS",
        ],
        "intercept": 14350.29332353689,
        "betas": [-0.06049803953960144, 0.02252832693672156, 0.02250904659478898, -0.30080885256248274],
        "sigma": 423.1705719697622,
        "entry_z": 2.0,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "MICROCHIP_RECTANGLE",
        "components": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE"],
        "intercept": 12595.888646662721,
        "betas": [0.10560729802045757, 0.25219468928333105, -0.2712089572427367, -0.3316449079702204],
        "sigma": 329.6256830600202,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "OXYGEN_SHAKE_MINT",
        "components": [
            "OXYGEN_SHAKE_MORNING_BREATH",
            "OXYGEN_SHAKE_EVENING_BREATH",
            "OXYGEN_SHAKE_CHOCOLATE",
            "OXYGEN_SHAKE_GARLIC",
        ],
        "intercept": 18937.692978063147,
        "betas": [-0.1295323083444758, -0.5603953797416523, 0.08014956879485062, -0.28291729214856054],
        "sigma": 442.06984309591326,
        "entry_z": 3.0,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "PANEL_2X2",
        "components": ["PANEL_1X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
        "intercept": 21783.253229735506,
        "betas": [-0.34317424505888905, 0.18104373486721692, -0.41149800200502956, -0.628654226694312],
        "sigma": 369.54249653714464,
        "entry_z": 2.5,
        "hold": 100,
        "exit": "fixed",
    },
    {
        "target": "PEBBLES_S",
        "components": ["PEBBLES_XS", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
        "intercept": 49997.436755970608,
        "betas": [-0.999926006686, -0.999951654763, -0.999926981924, -0.999945873064],
        "sigma": 2.798296213303394,
        "entry_z": 1.5,
        "hold": 200,
        "exit": "fixed",
    },
    {
        "target": "ROBOT_IRONING",
        "components": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY"],
        "intercept": 18545.65891347723,
        "betas": [0.12133139173436146, -0.6035255172035513, -0.4402725717106749, 0.015651900384425228],
        "sigma": 369.0771501834655,
        "entry_z": 2.5,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "SLEEP_POD_POLYESTER",
        "components": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
        "intercept": 84.64084048818248,
        "betas": [0.5185851713630322, -0.1455033575710156, 0.06990506069066837, 0.5837152771996909],
        "sigma": 327.3066485115772,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "SNACKPACK_STRAWBERRY",
        "components": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_RASPBERRY"],
        "intercept": 67692.39480337707,
        "betas": [-1.819519057618865, -1.6199756067024471, -1.0092655194895161, -1.3032960304327985],
        "sigma": 163.08409144921757,
        "entry_z": 2.0,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "TRANSLATOR_VOID_BLUE",
        "components": [
            "TRANSLATOR_SPACE_GRAY",
            "TRANSLATOR_ASTRO_BLACK",
            "TRANSLATOR_ECLIPSE_CHARCOAL",
            "TRANSLATOR_GRAPHITE_MIST",
        ],
        "intercept": 15353.237252967916,
        "betas": [-0.40582283392210716, -0.6238663498409187, 0.5065746200270247, 0.021493389661280775],
        "sigma": 329.1562069293615,
        "entry_z": 2.5,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "UV_VISOR_MAGENTA",
        "components": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED"],
        "intercept": 19824.977653006463,
        "betas": [0.031230275469664674, -0.6565830090431027, -0.06530299043059871, -0.2874209095667269],
        "sigma": 264.0833293041973,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "fixed",
    },
]

RESIDUAL_TARGETS = set(str(spec["target"]) for spec in SPECS)

PASSIVE_TARGET_OVERRIDES = {
    "PANEL_2X2",
    "PEBBLES_S",
    "ROBOT_IRONING",
    "SNACKPACK_STRAWBERRY",
}
ACTIVE_RESIDUAL_TARGETS = RESIDUAL_TARGETS - PASSIVE_TARGET_OVERRIDES

MM_PRODUCTS = {
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PANEL_2X4",
    "PEBBLES_L",
    "PEBBLES_XL",
    "ROBOT_DISHES",
    "ROBOT_LAUNDRY",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_SUEDE",
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ASTRO_BLACK",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
    "UV_VISOR_YELLOW",
}
MM_PRODUCTS.update(PASSIVE_TARGET_OVERRIDES)
MM_PRODUCTS = (MM_PRODUCTS | MM_ONLY_PRODUCTS) - FREE_ALPHA_PRODUCTS - DROP_MM_PRODUCTS


def free_alpha_fair(product: str, timestamp: int) -> Optional[float]:
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


def free_alpha_orders(state: TradingState, product: str) -> List[Order]:
    depth = state.order_depths.get(product)
    if depth is None:
        return []
    fair = free_alpha_fair(product, int(state.timestamp))
    if fair is None:
        return []
    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return []
    position = int(state.position.get(product, 0))
    target = position
    entry_edge = float(FREE_ALPHA_ENTRY_EDGE_BY_PRODUCT.get(product, FREE_ALPHA_ENTRY_EDGE))
    if ask < fair - entry_edge:
        target = LIMIT
    elif bid > fair + entry_edge:
        target = -LIMIT
    else:
        mid = 0.5 * (bid + ask)
        if abs(mid - fair) <= FREE_ALPHA_EXIT_EDGE:
            target = 0
    delta = target - position
    if delta == 0:
        return []
    side = 1 if delta > 0 else -1
    result = active_price_for_qty(depth, side, abs(delta))
    if result is None:
        return []
    price, qty = result
    return [Order(product, price, qty if side > 0 else -qty)]


def best_bid_ask(depth: OrderDepth) -> Tuple[Optional[int], Optional[int]]:
    bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
    ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
    return bid, ask


def mid_price(depth: OrderDepth) -> Optional[float]:
    bid, ask = best_bid_ask(depth)
    if bid is None or ask is None:
        return None
    return 0.5 * (bid + ask)


def active_price_for_qty(depth: OrderDepth, side: int, qty: int) -> Optional[Tuple[int, int]]:
    if qty <= 0:
        return None
    remaining = qty
    filled = 0
    last_price = None
    if side > 0:
        for price in sorted(depth.sell_orders.keys()):
            available = -int(depth.sell_orders[price])
            if available <= 0:
                continue
            take = min(remaining, available)
            remaining -= take
            filled += take
            last_price = price
            if remaining <= 0:
                break
    else:
        for price in sorted(depth.buy_orders.keys(), reverse=True):
            available = int(depth.buy_orders[price])
            if available <= 0:
                continue
            take = min(remaining, available)
            remaining -= take
            filled += take
            last_price = price
            if remaining <= 0:
                break
    if filled <= 0 or last_price is None:
        return None
    return int(last_price), int(filled)


class Trader:
    def load_memory(self, trader_data: str) -> Dict[str, Any]:
        if trader_data:
            try:
                data = json.loads(trader_data)
                if isinstance(data, dict):
                    data.setdefault("tick", 0)
                    data.setdefault("res", {})
                    return data
            except Exception:
                pass
        return {"tick": 0, "res": {}}

    def save_memory(self, memory: Dict[str, Any]) -> str:
        return json.dumps(memory, separators=(",", ":"))

    def residual(self, state: TradingState, spec: Dict[str, Any]) -> Optional[float]:
        target = str(spec["target"])
        target_depth = state.order_depths.get(target)
        if target_depth is None:
            return None
        target_mid = mid_price(target_depth)
        if target_mid is None:
            return None
        fair = float(spec["intercept"])
        components = spec["components"]
        betas = spec["betas"]
        for idx, product in enumerate(components):
            depth = state.order_depths.get(product)
            if depth is None:
                return None
            mid = mid_price(depth)
            if mid is None:
                return None
            fair += float(betas[idx]) * mid
        return target_mid - fair

    def close_order(self, state: TradingState, target: str, position: int) -> Optional[Order]:
        depth = state.order_depths.get(target)
        if depth is None or position == 0:
            return None
        side = -1 if position > 0 else 1
        result = active_price_for_qty(depth, side, abs(position))
        if result is None:
            return None
        price, qty = result
        return Order(target, price, qty if side > 0 else -qty)

    def entry_order(self, state: TradingState, target: str, direction: int) -> Optional[Order]:
        depth = state.order_depths.get(target)
        if depth is None:
            return None
        position = int(state.position.get(target, 0))
        room = LIMIT - position if direction > 0 else LIMIT + position
        qty = min(LIMIT, max(0, room))
        result = active_price_for_qty(depth, direction, qty)
        if result is None:
            return None
        price, filled_qty = result
        return Order(target, price, filled_qty if direction > 0 else -filled_qty)

    def run(self, state: TradingState):
        memory = self.load_memory(state.traderData)
        memory["tick"] = int(memory.get("tick", 0)) + 1
        tick = int(memory["tick"])
        sleeves = memory.setdefault("res", {})
        orders: Dict[str, List[Order]] = {}

        for product in FREE_ALPHA_PRODUCTS:
            product_orders = free_alpha_orders(state, product)
            if product_orders:
                orders[product] = product_orders

        for spec in SPECS:
            target = str(spec["target"])
            if target in PASSIVE_TARGET_OVERRIDES or target in FREE_ALPHA_PRODUCTS:
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

        for product, depth in state.order_depths.items():
            if product in FREE_ALPHA_PRODUCTS or product not in MM_PRODUCTS or product in ACTIVE_RESIDUAL_TARGETS or product in orders:
                continue
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None or bid >= ask:
                continue
            position = int(state.position.get(product, 0))
            product_orders: List[Order] = []
            buy_qty = LIMIT - position
            if buy_qty > 0 and product not in MM_BID_OFF_PRODUCTS:
                product_orders.append(Order(product, bid, buy_qty))
            sell_qty = LIMIT + position
            if sell_qty > 0 and product not in MM_ASK_OFF_PRODUCTS:
                product_orders.append(Order(product, ask, -sell_qty))
            if product_orders:
                orders[product] = product_orders

        return orders, 0, self.save_memory(memory)
