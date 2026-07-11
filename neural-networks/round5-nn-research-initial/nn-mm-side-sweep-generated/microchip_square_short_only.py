from datamodel import Order, OrderDepth, TradingState
import json
from typing import Any, Dict, List, Optional, Tuple
# Generated NN-directed MM side-gate research variant: microchip_square_short_only.
LIMIT = 10
BASE_MR_SPECS = {"PEBBLES_XL": {"window": 200, "entry_z": 2.5, "hold": 500}, "PEBBLES_XS": {"window": 1000, "entry_z": 3.0, "hold": 500}, "MICROCHIP_TRIANGLE": {"window": 1000, "entry_z": 2.5, "hold": 500}, "ROBOT_LAUNDRY": {"window": 1000, "entry_z": 2.5, "hold": 500}}
MR_PRODUCTS = {"PEBBLES_XL", "PEBBLES_XS", "MICROCHIP_TRIANGLE", "ROBOT_LAUNDRY"}
FREE_ALPHA_ENTRY_EDGE = 80.0
FREE_ALPHA_EXIT_EDGE = 5.0
FREE_ALPHA_ENTRY_EDGE_BY_PRODUCT = {
    "GALAXY_SOUNDS_DARK_MATTER": 40.0,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 200.0,
    "PANEL_2X2": 200.0,
    "PEBBLES_L": 200.0,
    "ROBOT_MOPPING": 200.0,
    "ROBOT_VACUUMING": 200.0,
    "SLEEP_POD_COTTON": 200.0,
    "SLEEP_POD_POLYESTER": 200.0,
    "SNACKPACK_PISTACHIO": 120.0,
    "SNACKPACK_RASPBERRY": 120.0,
    "SNACKPACK_VANILLA": 200.0,
    "TRANSLATOR_ECLIPSE_CHARCOAL": 200.0,
    "UV_VISOR_MAGENTA": 40.0,
    "UV_VISOR_YELLOW": 200.0,
}
FREE_ALPHA_PRODUCTS = {
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "PANEL_2X2",
    "PEBBLES_L",
    "ROBOT_MOPPING",
    "ROBOT_VACUUMING",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SLEEP_POD_POLYESTER",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_YELLOW",
}
FREE_ALPHA = {
    "GALAXY_SOUNDS_DARK_MATTER": (10428.5000, -201.5000, -346.1667, -438.5000, 89.3333),
    "GALAXY_SOUNDS_SOLAR_FLAMES": (10660.5000, 290.0000, 485.5000, 537.8333, 277.3333),
    "GALAXY_SOUNDS_SOLAR_WINDS": (10115.8333, -5.5000, 457.5000, 305.5000, 83.5000),
    "PANEL_2X2": (9762.1667, -231.1667, -417.1667, 114.6667, -192.0000),
    "PEBBLES_L": (10381.6667, -27.0000, 159.1667, -231.8333, -297.0000),
    "ROBOT_MOPPING": (10661.5000, 120.0000, -7.3333, 392.0000, 530.1667),
    "ROBOT_VACUUMING": (9550.5000, -255.3333, -440.0000, -322.8333, -570.5000),
    "SLEEP_POD_COTTON": (11105.1667, 265.3333, 277.3333, 463.3333, 471.5000),
    "SLEEP_POD_LAMB_WOOL": (10396.3333, 32.0000, 207.6667, 457.5000, 272.0000),
    "SLEEP_POD_POLYESTER": (11555.5000, -63.1667, 439.1667, 71.5000, 655.6667),
    "SNACKPACK_PISTACHIO": (9634.8333, -41.3333, -22.5000, -243.8333, -298.1667),
    "SNACKPACK_RASPBERRY": (10120.3333, 2.5000, -79.3333, 53.1667, 103.1667),
    "SNACKPACK_VANILLA": (10023.0000, 23.1667, -26.1667, -74.0000, 109.3333),
    "TRANSLATOR_ECLIPSE_CHARCOAL": (9954.0000, 41.5000, 22.3333, -280.5000, -88.1667),
    "TRANSLATOR_GRAPHITE_MIST": (10130.3333, 327.6667, 311.0000, -148.8333, -70.0000),
    "UV_VISOR_MAGENTA": (10969.6667, -95.6667, 12.1667, -169.5000, 501.5000),
    "UV_VISOR_YELLOW": (11211.6667, -56.0000, -301.1667, -491.1667, 16.0000),
}
SPECS = [
    {"target": "GALAXY_SOUNDS_SOLAR_FLAMES", "components": ["GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS"], "intercept": 14350.29332353689, "betas": [-0.06049803953960144, 0.02252832693672156, 0.02250904659478898, -0.30080885256248274], "sigma": 423.1705719697622, "entry_z": 2.0, "hold": 500, "exit": "fixed"},
    {"target": "MICROCHIP_RECTANGLE", "components": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE"], "intercept": 12595.888646662721, "betas": [0.10560729802045757, 0.25219468928333105, -0.2712089572427367, -0.3316449079702204], "sigma": 329.6256830600202, "entry_z": 1.5, "hold": 500, "exit": "zero"},
    {"target": "OXYGEN_SHAKE_MINT", "components": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"], "intercept": 18937.692978063147, "betas": [-0.1295323083444758, -0.5603953797416523, 0.08014956879485062, -0.28291729214856054], "sigma": 442.06984309591326, "entry_z": 3.0, "hold": 500, "exit": "fixed"},
    {"target": "PANEL_2X2", "components": ["PANEL_1X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"], "intercept": 21783.253229735506, "betas": [-0.34317424505888905, 0.18104373486721692, -0.41149800200502956, -0.628654226694312], "sigma": 369.54249653714464, "entry_z": 2.5, "hold": 100, "exit": "fixed"},
    {"target": "PEBBLES_S", "components": ["PEBBLES_XS", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"], "intercept": 49997.436755970608, "betas": [-0.999926006686, -0.999951654763, -0.999926981924, -0.999945873064], "sigma": 2.798296213303394, "entry_z": 1.5, "hold": 200, "exit": "fixed"},
    {"target": "ROBOT_IRONING", "components": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY"], "intercept": 18545.65891347723, "betas": [0.12133139173436146, -0.6035255172035513, -0.4402725717106749, 0.015651900384425228], "sigma": 369.0771501834655, "entry_z": 2.5, "hold": 500, "exit": "fixed"},
    {"target": "SLEEP_POD_POLYESTER", "components": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"], "intercept": 84.64084048818248, "betas": [0.5185851713630322, -0.1455033575710156, 0.06990506069066837, 0.5837152771996909], "sigma": 327.3066485115772, "entry_z": 1.5, "hold": 500, "exit": "zero"},
    {"target": "SNACKPACK_STRAWBERRY", "components": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_RASPBERRY"], "intercept": 67692.39480337707, "betas": [-1.819519057618865, -1.6199756067024471, -1.0092655194895161, -1.3032960304327985], "sigma": 163.08409144921757, "entry_z": 2.0, "hold": 500, "exit": "zero"},
    {"target": "TRANSLATOR_VOID_BLUE", "components": ["TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_GRAPHITE_MIST"], "intercept": 15353.237252967916, "betas": [-0.40582283392210716, -0.6238663498409187, 0.5065746200270247, 0.021493389661280775], "sigma": 329.1562069293615, "entry_z": 2.5, "hold": 500, "exit": "fixed"},
    {"target": "UV_VISOR_MAGENTA", "components": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED"], "intercept": 19824.977653006463, "betas": [0.031230275469664674, -0.6565830090431027, -0.06530299043059871, -0.2874209095667269], "sigma": 264.0833293041973, "entry_z": 1.5, "hold": 500, "exit": "fixed"},
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
MM_PRODUCTS = MM_PRODUCTS - FREE_ALPHA_PRODUCTS - MR_PRODUCTS
MM_PRODUCTS.add("ROBOT_LAUNDRY")
MM_PRODUCTS.update({"PEBBLES_L", "SNACKPACK_CHOCOLATE", "ROBOT_DISHES"})
MM_SIZE_BY_PRODUCT = {
    "GALAXY_SOUNDS_PLANETARY_RINGS": 1,
    "UV_VISOR_ORANGE": 1,
    "OXYGEN_SHAKE_MORNING_BREATH": 1,
    "OXYGEN_SHAKE_GARLIC": 1,
    "MICROCHIP_CIRCLE": 1,
    "PANEL_2X4": 1,
    "SNACKPACK_STRAWBERRY": 2,
    "ROBOT_IRONING": 1,
    "SNACKPACK_CHOCOLATE": 1,
}
REANCHOR_PATHS = {
    "ROBOT_DISHES": {"deltas": [0.0, -3.1492, 86.3330, 90.3954, 373.3512], "edge": 80.0},
    "PEBBLES_L": {"deltas": [0.0, 0.0, 0.0, 0.0, 0.0], "edge": 80.0},
    "PEBBLES_S": {"deltas": [0.0, -174.7283, -364.3448, -492.6096, -782.8890], "edge": 80.0},
    "UV_VISOR_ORANGE": {"deltas": [0.0, 295.9357, 324.1591, 77.9767, -256.5292], "edge": 200.0},
    "SLEEP_POD_NYLON": {"deltas": [0.0, 92.0165, 198.0914, 312.9306, 294.4373], "edge": 40.0},
    "OXYGEN_SHAKE_MINT": {"deltas": [0.0, -142.7385, -233.8113, 150.5769, 149.7404], "edge": 300.0},
    "SNACKPACK_STRAWBERRY": {"deltas": [0.0, 251.9292, 166.0859, 263.2890, 230.8858], "edge": 200.0},
    "PANEL_4X4": {"deltas": [0.0, -145.1036, -495.1697, -472.6362, -243.4067], "edge": 300.0},
    "SNACKPACK_CHOCOLATE": {"deltas": [0.0, -52.7219, -60.5552, -242.0813, -138.6170], "edge": 160.0},
    "OXYGEN_SHAKE_EVENING_BREATH": {"deltas": [0.0, 188.3633, -174.7125, -316.9532, -335.9718], "edge": 300.0},
    "PANEL_1X2": {"deltas": [0.0, 144.7119, -39.1490, 229.0523, 248.6540], "edge": 300.0},
}
REANCHOR_PRODUCTS = {
    "ROBOT_DISHES",
    "PEBBLES_L",
    "OXYGEN_SHAKE_MINT",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_CHOCOLATE",
}
MM_OWNED_PRODUCTS = {"PEBBLES_L", "SNACKPACK_CHOCOLATE", "ROBOT_DISHES"}
REANCHOR_EXIT_EDGE = 5.0
NN_CROSS_SPECS = [
    {
        "source": "MICROCHIP_SQUARE",
        "target": "MICROCHIP_OVAL",
        "lookback": 50,
        "trigger": "low",
        "threshold": -180.0,
        "direction": -1,
        "hold": 1000,
    },
]
MM_BID_OFF_PRODUCTS = {
    "MICROCHIP_OVAL",
    "MICROCHIP_TRIANGLE",
    "ROBOT_IRONING",
    "TRANSLATOR_ASTRO_BLACK",
    "UV_VISOR_AMBER",
    "MICROCHIP_SQUARE",
}
MM_ASK_OFF_PRODUCTS = {
    "GALAXY_SOUNDS_BLACK_HOLES",
    "OXYGEN_SHAKE_GARLIC",
    "PANEL_2X4",
    "PEBBLES_XL",
    "SLEEP_POD_SUEDE",
    "UV_VISOR_RED",
}
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
def reanchor_bucket(timestamp: int) -> int:
    bucket = int(timestamp * 5 // 1000000)
    if bucket < 0:
        return 0
    if bucket > 4:
        return 4
    return bucket
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
                    data.setdefault("tick", 0); data.setdefault("res", {}); data.setdefault("mr", {}); data.setdefault("ra", {}); return data
            except Exception:
                pass
        return {"tick": 0, "res": {}, "mr": {}, "ra": {}}
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
    def mr_orders(self, state: TradingState, memory: Dict[str, Any], product: str, spec: Dict[str, Any], tick: int, allow_trade: bool) -> List[Order]:
        depth = state.order_depths.get(product)
        if depth is None: return []
        mid = mid_price(depth)
        if mid is None: return []
        window = int(spec["window"])
        mr_memory = memory.setdefault("mr", {}).setdefault(product, {})
        mids = mr_memory.get("mids", [])
        if not isinstance(mids, list): mids = []
        history = [float(value) for value in mids[-window:] if isinstance(value, (int, float))]
        z = None
        min_periods = max(20, window // 5)
        if len(history) >= min_periods:
            mean = sum(history) / len(history)
            sigma = (sum((value - mean) * (value - mean) for value in history) / len(history)) ** 0.5
            if sigma > 1e-9:
                z = (float(mid) - mean) / sigma
        history.append(float(mid))
        mr_memory["mids"] = history[-window:]
        if not allow_trade or z is None: return []
        position = int(state.position.get(product, 0))
        if position == 0:
            mr_memory.pop("entry_tick", None)
            mr_memory.pop("entry_z", None)
            entry_z = float(spec["entry_z"])
            direction = 1 if z <= -entry_z else -1 if z >= entry_z else 0
            if direction == 0: return []
            order = self.entry_order(state, product, direction)
            if order is None or order.quantity == 0: return []
            mr_memory["entry_tick"] = tick
            mr_memory["entry_z"] = round(float(z), 4)
            return [order]
        entry_tick = int(mr_memory.get("entry_tick", tick))
        zero_cross = (position > 0 and z >= 0.0) or (position < 0 and z <= 0.0)
        if tick - entry_tick < int(spec["hold"]) and not zero_cross: return []
        order = self.close_order(state, product, position)
        if order is None: return []
        mr_memory.pop("entry_tick", None)
        mr_memory.pop("entry_z", None)
        return [order]
    def reanchor_orders(self, state: TradingState, memory: Dict[str, Any], product: str) -> List[Order]:
        spec = REANCHOR_PATHS.get(product)
        depth = state.order_depths.get(product)
        if spec is None or depth is None:
            return []
        mid = mid_price(depth)
        if mid is None:
            return []
        bucket = reanchor_bucket(int(state.timestamp))
        ra_memory = memory.setdefault("ra", {}).setdefault(product, {})
        if bucket == 0:
            count = int(ra_memory.get("count", 0)) + 1
            anchor = float(ra_memory.get("anchor", mid))
            anchor += (float(mid) - anchor) / count
            ra_memory["anchor"] = anchor
            ra_memory["count"] = count
        anchor_value = ra_memory.get("anchor")
        if not isinstance(anchor_value, (int, float)):
            ra_memory["anchor"] = float(mid)
            ra_memory["count"] = 1
            anchor_value = float(mid)
        fair = float(anchor_value) + float(spec["deltas"][bucket])
        bid, ask = best_bid_ask(depth)
        if bid is None or ask is None:
            return []
        position = int(state.position.get(product, 0))
        target = position
        edge = float(spec["edge"])
        if ask < fair - edge:
            target = LIMIT
        elif bid > fair + edge:
            target = -LIMIT
        elif abs(float(mid) - fair) <= REANCHOR_EXIT_EDGE:
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
    def nn_cross_orders(self, state: TradingState, memory: Dict[str, Any], spec: Dict[str, Any], tick: int) -> List[Order]:
        source = str(spec["source"])
        target = str(spec["target"])
        source_depth = state.order_depths.get(source)
        if source_depth is None:
            return []
        source_mid = mid_price(source_depth)
        if source_mid is None:
            return []
        nn_memory = memory.setdefault("nn", {})
        src_mem = nn_memory.setdefault(source, {})
        mids = src_mem.get("mids", [])
        if not isinstance(mids, list):
            mids = []
        lookback = int(spec["lookback"])
        history = [float(value) for value in mids[-lookback:] if isinstance(value, (int, float))]
        src_mem["mids"] = (history + [float(source_mid)])[-lookback:]
        if len(history) < lookback:
            return []
        move = float(source_mid) - float(history[0])
        target_mem = nn_memory.setdefault(target, {})
        position = int(state.position.get(target, 0))
        entry_tick = int(target_mem.get("entry_tick", tick))
        if position != 0 and tick - entry_tick >= int(spec["hold"]):
            order = self.close_order(state, target, position)
            if order is not None:
                target_mem.clear()
                return [order]
            return []
        threshold = float(spec["threshold"])
        trigger = str(spec.get("trigger", "low"))
        hit = move <= threshold if trigger == "low" else move >= threshold
        if position != 0 or not hit:
            return []
        order = self.entry_order(state, target, int(spec["direction"]))
        if order is None or order.quantity == 0:
            return []
        target_mem["entry_tick"] = tick
        target_mem["move"] = round(move, 4)
        return [order]
    def run(self, state: TradingState):
        memory = self.load_memory(state.traderData)
        memory["tick"] = int(memory.get("tick", 0)) + 1
        tick = int(memory["tick"])
        sleeves = memory.setdefault("res", {})
        orders: Dict[str, List[Order]] = {}
        for product in REANCHOR_PRODUCTS:
            product_orders = self.reanchor_orders(state, memory, product)
            if product_orders:
                orders[product] = product_orders
        for product in FREE_ALPHA_PRODUCTS:
            if product in REANCHOR_PRODUCTS:
                continue
            product_orders = free_alpha_orders(state, product)
            if product_orders:
                orders[product] = product_orders
        for spec in SPECS:
            target = str(spec["target"])
            if target in PASSIVE_TARGET_OVERRIDES or target in FREE_ALPHA_PRODUCTS or target in REANCHOR_PRODUCTS:
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
        for spec in NN_CROSS_SPECS:
            target = str(spec["target"])
            if target in orders:
                continue
            target_orders = self.nn_cross_orders(state, memory, spec, tick)
            if target_orders:
                orders[target] = target_orders
        for product in MR_PRODUCTS:
            if product in REANCHOR_PRODUCTS:
                continue
            spec = BASE_MR_SPECS.get(product)
            if spec is None:
                continue
            allow_trade = product not in orders and product not in FREE_ALPHA_PRODUCTS and product not in ACTIVE_RESIDUAL_TARGETS
            product_orders = self.mr_orders(state, memory, product, spec, tick, allow_trade)
            if product_orders:
                orders[product] = product_orders
        for product, depth in state.order_depths.items():
            if ((product in REANCHOR_PRODUCTS or product in FREE_ALPHA_PRODUCTS) and product not in MM_OWNED_PRODUCTS) or product not in MM_PRODUCTS or product in ACTIVE_RESIDUAL_TARGETS or product in orders:
                continue
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None or bid >= ask:
                continue
            position = int(state.position.get(product, 0))
            product_orders: List[Order] = []
            max_size = int(MM_SIZE_BY_PRODUCT.get(product, LIMIT))
            can_buy = product not in MM_BID_OFF_PRODUCTS
            can_sell = product not in MM_ASK_OFF_PRODUCTS
            if product in {"PEBBLES_L", "ROBOT_DISHES"}:
                can_buy = position < 0
                can_sell = position > 0
            if product == "MICROCHIP_CIRCLE" and depth.buy_orders and depth.sell_orders:
                bid_volume = int(depth.buy_orders[max(depth.buy_orders.keys())])
                ask_volume = -int(depth.sell_orders[min(depth.sell_orders.keys())])
                total_volume = bid_volume + ask_volume
                if total_volume > 0:
                    imbalance = (bid_volume - ask_volume) / total_volume
                    if imbalance <= -0.4:
                        can_buy = False
                    if imbalance >= 0.4:
                        can_sell = False
            buy_qty = min(LIMIT - position, max_size)
            if buy_qty > 0 and can_buy:
                product_orders.append(Order(product, bid, buy_qty))
            sell_qty = min(LIMIT + position, max_size)
            if sell_qty > 0 and can_sell:
                product_orders.append(Order(product, ask, -sell_qty))
            if product_orders:
                orders[product] = product_orders
        return orders, 0, self.save_memory(memory)
