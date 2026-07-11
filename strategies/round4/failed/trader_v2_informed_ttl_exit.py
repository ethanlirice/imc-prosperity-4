import json
from typing import Dict, List

try:
    from datamodel import Order, OrderDepth, Trade, TradingState
except ModuleNotFoundError:
    from trader_factory.core.datamodel import Order, OrderDepth, Trade, TradingState


INFORMED_TRADER = "Mark 14"
EXIT_HORIZON = 200

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


def load_memory(raw: str) -> dict:
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def dump_memory(memory: dict) -> str:
    return json.dumps(memory, separators=(",", ":"))


def best_bid(depth: OrderDepth):
    if not depth.buy_orders:
        return None
    return max(depth.buy_orders.keys())


def best_ask(depth: OrderDepth):
    if not depth.sell_orders:
        return None
    return min(depth.sell_orders.keys())


def signed_submission_trade(trade: Trade) -> int:
    qty = abs(int(trade.quantity))
    if trade.buyer == "SUBMISSION":
        return qty
    if trade.seller == "SUBMISSION":
        return -qty
    return 0


class Trader:
    def record_entry_fills(self, state: TradingState, memory: dict) -> None:
        pending = memory.setdefault("pending_entries", {})
        tranches = memory.setdefault("tranches", {})
        last_seen = memory.setdefault("last_own_ts", {})

        for symbol in COPY_PRODUCTS:
            product_pending = pending.setdefault(symbol, [])
            product_tranches = tranches.setdefault(symbol, [])
            last_ts = int(last_seen.get(symbol, -1))
            max_ts = last_ts

            for trade in state.own_trades.get(symbol, []):
                ts = int(trade.timestamp)
                if ts <= last_ts:
                    continue
                max_ts = max(max_ts, ts)
                signed_qty = signed_submission_trade(trade)
                if signed_qty == 0:
                    continue

                direction = 1 if signed_qty > 0 else -1
                remaining = abs(signed_qty)
                next_pending = []

                for entry in product_pending:
                    entry_dir = int(entry["dir"])
                    entry_qty = int(entry["qty"])
                    if remaining > 0 and entry_dir == direction:
                        used = min(remaining, entry_qty)
                        product_tranches.append(
                            [ts + EXIT_HORIZON, entry_dir * used]
                        )
                        remaining -= used
                        entry_qty -= used
                    if entry_qty > 0:
                        entry["qty"] = entry_qty
                        next_pending.append(entry)

                product_pending = next_pending

            # Drop stale entry intents that never filled.
            pending[symbol] = [
                entry
                for entry in product_pending
                if int(entry["ts"]) >= int(state.timestamp) - 1000
            ]
            last_seen[symbol] = max_ts

    def send_due_exits(
        self,
        state: TradingState,
        memory: dict,
        symbol: str,
        orders_out: List[Order],
        projected_pos: int,
    ) -> int:
        depth = state.order_depths[symbol]
        tranches = memory.setdefault("tranches", {}).setdefault(symbol, [])
        due_qty = 0
        keep = []

        for exit_ts, signed_qty in tranches:
            if int(exit_ts) <= int(state.timestamp):
                due_qty += int(signed_qty)
            else:
                keep.append([int(exit_ts), int(signed_qty)])

        memory["tranches"][symbol] = keep
        if due_qty == 0:
            return projected_pos

        if due_qty > 0:
            bid = best_bid(depth)
            qty = min(due_qty, max(0, projected_pos))
            if bid is not None and qty > 0:
                orders_out.append(Order(symbol, bid, -qty))
                projected_pos -= qty
        else:
            ask = best_ask(depth)
            qty = min(-due_qty, max(0, -projected_pos))
            if ask is not None and qty > 0:
                orders_out.append(Order(symbol, ask, qty))
                projected_pos += qty

        return projected_pos

    def check_informed_trader(
        self,
        state: TradingState,
        memory: dict,
        symbol: str,
        orders_out: List[Order],
        projected_pos: int,
    ) -> int:
        depth = state.order_depths[symbol]
        net_signal = 0
        for trade in state.market_trades.get(symbol, []):
            if trade.buyer == INFORMED_TRADER:
                net_signal += abs(int(trade.quantity))
            if trade.seller == INFORMED_TRADER:
                net_signal -= abs(int(trade.quantity))

        if net_signal == 0:
            return projected_pos

        limit = POSITION_LIMITS[symbol]
        if net_signal > 0:
            ask = best_ask(depth)
            qty = min(COPY_SIZE[symbol], limit - projected_pos)
            if ask is not None and qty > 0:
                orders_out.append(Order(symbol, ask, qty))
                memory.setdefault("pending_entries", {}).setdefault(symbol, []).append(
                    {"ts": int(state.timestamp), "dir": 1, "qty": int(qty)}
                )
                projected_pos += qty
        else:
            bid = best_bid(depth)
            qty = min(COPY_SIZE[symbol], projected_pos + limit)
            if bid is not None and qty > 0:
                orders_out.append(Order(symbol, bid, -qty))
                memory.setdefault("pending_entries", {}).setdefault(symbol, []).append(
                    {"ts": int(state.timestamp), "dir": -1, "qty": int(qty)}
                )
                projected_pos -= qty

        return projected_pos

    def run(self, state: TradingState):
        memory = load_memory(state.traderData)
        self.record_entry_fills(state, memory)

        result: Dict[str, List[Order]] = {}
        for symbol in COPY_PRODUCTS:
            if symbol not in state.order_depths:
                continue

            orders: List[Order] = []
            projected_pos = int(state.position.get(symbol, 0))
            before_exit_count = len(orders)
            projected_pos = self.send_due_exits(
                state, memory, symbol, orders, projected_pos
            )

            # Do not open a new Mark 14 copy trade on the same tick we are
            # crossing out of a previous tranche.
            if len(orders) == before_exit_count:
                self.check_informed_trader(
                    state, memory, symbol, orders, projected_pos
                )

            if orders:
                result[symbol] = orders

        return result, 0, dump_memory(memory)
