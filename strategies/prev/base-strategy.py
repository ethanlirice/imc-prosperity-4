from datamodel import Order, OrderDepth, TradingState
import json
from typing import Any, Dict, List, Optional, Tuple

# Primary R5 backtest: prosperity4btx ... 5 --merge-pnl = +534,757
# Days: D2 +147,320 / D3 +185,325 / D4 +202,112

LIMIT = 10

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
    "TRANSLATOR_SPACE_GRAY",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
    "UV_VISOR_YELLOW",
}


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

        for spec in SPECS:
            target = str(spec["target"])
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
            if product not in MM_PRODUCTS or product in RESIDUAL_TARGETS or product in orders:
                continue
            bid, ask = best_bid_ask(depth)
            if bid is None or ask is None or ask - bid <= 2:
                continue
            position = int(state.position.get(product, 0))
            product_orders: List[Order] = []
            buy_qty = LIMIT - position
            if buy_qty > 0:
                product_orders.append(Order(product, bid + 1, buy_qty))
            sell_qty = LIMIT + position
            if sell_qty > 0:
                product_orders.append(Order(product, ask - 1, -sell_qty))
            if product_orders:
                orders[product] = product_orders

        return orders, 0, self.save_memory(memory)
