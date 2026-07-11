"""
Round 1 trader v14 — OSMIUM execution fix: one-sided book handling.

Diagnostic finding: v10 returns [] on ~800 ticks/day (~8%) because it
requires both depth.buy_orders AND depth.sell_orders non-empty before
doing anything. Those one-sided ticks lose:
  - take opportunities on whichever side IS visible
  - make-quote placements on BOTH sides (the hidden side included) —
    on live this is where competitors catch exclusive taker flow

Fix:
  - Persist last-known wall_mid / bid_wall / ask_wall in traderData.
  - On one-sided ticks, use stored values for the missing side and run
    the normal take/make logic on whichever side is visible.
  - If no value has been stored yet (initial one-sided tick), bootstrap
    from the visible side using a 22-tick default spread (mean observed
    wall_spread across all 3 training days).

Also: on two-sided ticks the behavior is unchanged from v10, so the
uptrend/reverse backtest should match v10 exactly on those ticks. Extra
PnL comes only from previously-skipped ticks.

PEPPER: unchanged from v10.
"""

import json
from datamodel import TradingState, Order

OSMIUM = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"

POS_LIMIT = 80

PEPPER_STOP_LOSS = 300
OSMIUM_DEFAULT_HALFSPREAD = 11  # mean wall_spread ~22 → half 11


class Trader:

    def run(self, state: TradingState):
        try:
            td = json.loads(state.traderData) if state.traderData else {}
        except (json.JSONDecodeError, ValueError):
            td = {}
        result = {}
        oo = self.trade_osmium(state, td)
        if oo:
            result[OSMIUM] = oo
        po = self.trade_pepper(state, td)
        if po:
            result[PEPPER] = po
        return result, 0, json.dumps(td)

    def trade_osmium(self, state, td):
        depth = state.order_depths.get(OSMIUM)
        if depth is None:
            return []
        has_bids = bool(depth.buy_orders)
        has_asks = bool(depth.sell_orders)
        if not has_bids and not has_asks:
            return []

        position = state.position.get(OSMIUM, 0)
        orders = []

        if has_bids and has_asks:
            bid_wall = min(depth.buy_orders.keys())
            ask_wall = max(depth.sell_orders.keys())
            wall_mid = (bid_wall + ask_wall) / 2
            td["osm_wall_mid"] = wall_mid
            td["osm_bid_wall"] = bid_wall
            td["osm_ask_wall"] = ask_wall
        else:
            wall_mid = td.get("osm_wall_mid", 10000.0)
            stored_bid_wall = td.get("osm_bid_wall", wall_mid - OSMIUM_DEFAULT_HALFSPREAD)
            stored_ask_wall = td.get("osm_ask_wall", wall_mid + OSMIUM_DEFAULT_HALFSPREAD)
            bid_wall = min(depth.buy_orders.keys()) if has_bids else stored_bid_wall
            ask_wall = max(depth.sell_orders.keys()) if has_asks else stored_ask_wall

        buy_cap = POS_LIMIT - position
        sell_cap = POS_LIMIT + position

        if has_asks:
            for p in sorted(depth.sell_orders.keys()):
                avail = -depth.sell_orders[p]
                if p <= wall_mid - 1:
                    take = min(avail, buy_cap)
                elif p <= wall_mid and position < 0:
                    take = min(avail, -position, buy_cap)
                else:
                    break
                if take > 0:
                    orders.append(Order(OSMIUM, p, take))
                    buy_cap -= take
                    position += take
                    if buy_cap <= 0:
                        break

        if has_bids:
            for p in sorted(depth.buy_orders.keys(), reverse=True):
                avail = depth.buy_orders[p]
                if p >= wall_mid + 1:
                    take = min(avail, sell_cap)
                elif p >= wall_mid and position > 0:
                    take = min(avail, position, sell_cap)
                else:
                    break
                if take > 0:
                    orders.append(Order(OSMIUM, p, -take))
                    sell_cap -= take
                    position -= take
                    if sell_cap <= 0:
                        break

        bid_price = int(bid_wall) + 1
        ask_price = int(ask_wall) - 1

        if has_bids:
            for bp in sorted(depth.buy_orders.keys(), reverse=True):
                bv = depth.buy_orders[bp]
                over = bp + 1
                if bv > 1 and over < wall_mid:
                    bid_price = max(bid_price, over)
                elif bp < wall_mid:
                    bid_price = max(bid_price, bp)
                break

        if has_asks:
            for sp in sorted(depth.sell_orders.keys()):
                sv = -depth.sell_orders[sp]
                under = sp - 1
                if sv > 1 and under > wall_mid:
                    ask_price = min(ask_price, under)
                elif sp > wall_mid:
                    ask_price = min(ask_price, sp)
                break

        if buy_cap > 0:
            orders.append(Order(OSMIUM, bid_price, buy_cap))
        if sell_cap > 0:
            orders.append(Order(OSMIUM, ask_price, -sell_cap))
        return orders

    def trade_pepper(self, state, trader_data):
        depth = state.order_depths.get(PEPPER)
        position = state.position.get(PEPPER, 0)
        s = trader_data.setdefault("pepper", {})

        prev = s.get("prev_ts", -1)
        if prev >= 0 and state.timestamp < prev:
            s["peak_mid"] = None
            s["stopped_out"] = False
        s["prev_ts"] = state.timestamp

        if depth is None or (not depth.buy_orders and not depth.sell_orders):
            return []

        best_bid = max(depth.buy_orders.keys()) if depth.buy_orders else None
        best_ask = min(depth.sell_orders.keys()) if depth.sell_orders else None
        if best_bid is not None and best_ask is not None:
            mid = (best_bid + best_ask) / 2
        elif best_bid is not None:
            mid = float(best_bid)
        else:
            mid = float(best_ask)

        peak = s.get("peak_mid")
        if peak is None or mid > peak:
            peak = mid
            s["peak_mid"] = peak

        orders = []

        if position > 0 and peak is not None and mid < peak - PEPPER_STOP_LOSS:
            remaining = position
            for p in sorted(depth.buy_orders.keys(), reverse=True):
                if remaining <= 0:
                    break
                take = min(depth.buy_orders[p], remaining)
                if take > 0:
                    orders.append(Order(PEPPER, p, -take))
                    remaining -= take
            s["stopped_out"] = True
            return orders

        if s.get("stopped_out"):
            return orders

        if position < POS_LIMIT:
            buy_cap = POS_LIMIT - position
            for p in sorted(depth.sell_orders.keys()):
                if buy_cap <= 0:
                    break
                take = min(-depth.sell_orders[p], buy_cap)
                if take > 0:
                    orders.append(Order(PEPPER, p, take))
                    buy_cap -= take
            if buy_cap > 0 and best_bid is not None and best_ask is not None:
                passive_bid = best_bid + 1
                if passive_bid < best_ask:
                    orders.append(Order(PEPPER, passive_bid, buy_cap))
        return orders