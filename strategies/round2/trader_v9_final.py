"""Round 2 trader v9_final — v8_final + 3 additive refinements.

v8_final core unchanged:
  - OSMIUM fair_value = wall_mid + 0.58*(10000 - wall_mid)
  - PEPPER rush-to-limit with 7-tick take cap + passive-bb+1 fallback
  - MAF bid (now shaded)

REFINEMENTS:
  1. MAF bid shaded to 511 (from 2000). Rationale: median-cutoff auction;
     retail/student competitors anchor to round numbers (100/500/1000).
     511 breaks psychological thresholds while preserving margin.
  2. Informed-trader toxicity detection via state.own_trades buyer/seller.
     Rolling markout per counterparty ID; adverse IDs trigger a
     temporary +2 spread widening for 10 ticks (1000 timestamp units).
  3. PEPPER unwind-at-fair: near pos limit & near EOD, fire aggregated
     TAKE order at floor/ceil(mid) to lock in accrued drift.

Backtest baseline (R2, v8_final):
  none:  252,967   worse:  301,531

v9_final MUST preserve v8 take/make logic exactly for OSMIUM and keep
the PEPPER accumulator unchanged except for the new unwind override.
"""

import json
from datamodel import TradingState, Order

OSMIUM = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"

POS_LIMIT = 80
PEPPER_STOP_LOSS = 300
PEPPER_TAKE_CAP = 7
OSMIUM_DEFAULT_HALFSPREAD = 11

MAF_BID = 511
WALL_SPREAD_MIN = 18

SKEW_MED = 30
SKEW_HEAVY = 55

OSMIUM_ANCHOR = 10000
OSMIUM_ANCHOR_ALPHA = 0.58

TOX_MARKOUT_LAG = 500
TOX_MIN_COUNT = 2
TOX_THRESHOLD = -1.0
TOX_WIDEN_TICKS = 1000
TOX_WIDEN_AMOUNT = 2


class Trader:

    def bid(self):
        return MAF_BID

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

    def _update_toxicity(self, state, td, cur_mid):
        """<20 line rolling toxicity tracker using own_trades buyer/seller IDs."""
        tox = td.setdefault("tox", {})
        pend = td.setdefault("pend", [])
        new_pend = []
        for ts_p, px, sd, cp in pend:
            if state.timestamp - ts_p >= TOX_MARKOUT_LAG:
                mk = (cur_mid - px) if sd == 1 else (px - cur_mid)
                rec = tox.setdefault(cp, [0.0, 0])
                rec[0] += mk
                rec[1] += 1
            else:
                new_pend.append((ts_p, px, sd, cp))
        td["pend"] = new_pend
        for t in state.own_trades.get(OSMIUM, []):
            cp = t.buyer if t.seller == "SUBMISSION" else t.seller
            if cp and cp != "SUBMISSION":
                sd = 1 if t.buyer == "SUBMISSION" else -1
                new_pend.append((state.timestamp, t.price, sd, cp))
        toxic = {k for k, v in tox.items() if v[1] >= TOX_MIN_COUNT and v[0] / v[1] < TOX_THRESHOLD}
        recent_cps = {cp for _, _, _, cp in new_pend}
        if recent_cps & toxic:
            td["swu"] = state.timestamp + TOX_WIDEN_TICKS
        return TOX_WIDEN_AMOUNT if state.timestamp < td.get("swu", 0) else 0

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

        persisted_mid = td.get("osm_wall_mid")
        persisted_bid_wall = td.get("osm_bid_wall")
        persisted_ask_wall = td.get("osm_ask_wall")

        if has_bids and has_asks:
            bid_wall = min(depth.buy_orders.keys())
            ask_wall = max(depth.sell_orders.keys())
            observed_mid = (bid_wall + ask_wall) / 2
            deep_bids = len(depth.buy_orders) >= 2
            deep_asks = len(depth.sell_orders) >= 2
            wide_enough = (ask_wall - bid_wall) >= WALL_SPREAD_MIN
            deep_enough = (deep_bids and deep_asks) or wide_enough
            if deep_enough or persisted_mid is None:
                wall_mid = observed_mid
                td["osm_wall_mid"] = wall_mid
                td["osm_bid_wall"] = bid_wall
                td["osm_ask_wall"] = ask_wall
            else:
                wall_mid = persisted_mid
                bid_wall = persisted_bid_wall if persisted_bid_wall is not None else bid_wall
                ask_wall = persisted_ask_wall if persisted_ask_wall is not None else ask_wall
        else:
            wall_mid = persisted_mid if persisted_mid is not None else 10000.0
            sbw = persisted_bid_wall if persisted_bid_wall is not None else wall_mid - OSMIUM_DEFAULT_HALFSPREAD
            saw = persisted_ask_wall if persisted_ask_wall is not None else wall_mid + OSMIUM_DEFAULT_HALFSPREAD
            bid_wall = min(depth.buy_orders.keys()) if has_bids else sbw
            ask_wall = max(depth.sell_orders.keys()) if has_asks else saw

        fair_value = wall_mid + OSMIUM_ANCHOR_ALPHA * (OSMIUM_ANCHOR - wall_mid)

        if has_bids and has_asks:
            cur_mid = (max(depth.buy_orders.keys()) + min(depth.sell_orders.keys())) / 2
        else:
            cur_mid = wall_mid
        tox_widen = self._update_toxicity(state, td, cur_mid)

        buy_cap = POS_LIMIT - position
        sell_cap = POS_LIMIT + position

        if has_asks:
            for p in sorted(depth.sell_orders.keys()):
                avail = -depth.sell_orders[p]
                if p <= fair_value - 1:
                    take = min(avail, buy_cap)
                elif p <= fair_value and position < 0:
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
                if p >= fair_value + 1:
                    take = min(avail, sell_cap)
                elif p >= fair_value and position > 0:
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
            bp = max(depth.buy_orders.keys())
            bv = depth.buy_orders[bp]
            over = bp + 1
            if bv > 1 and over < fair_value:
                bid_price = max(bid_price, over)
            elif bp < fair_value:
                bid_price = max(bid_price, bp)

        if has_asks:
            sp = min(depth.sell_orders.keys())
            sv = -depth.sell_orders[sp]
            under = sp - 1
            if sv > 1 and under > fair_value:
                ask_price = min(ask_price, under)
            elif sp > fair_value:
                ask_price = min(ask_price, sp)

        if tox_widen:
            bid_price -= tox_widen
            ask_price += tox_widen

        buy_sz = buy_cap
        sell_sz = sell_cap
        apos = abs(position)
        if apos >= SKEW_HEAVY:
            if position > 0:
                buy_sz = max(1, (buy_cap * 2 + 2) // 3)
            else:
                sell_sz = max(1, (sell_cap * 2 + 2) // 3)
        elif apos >= SKEW_MED:
            if position > 0:
                buy_sz = max(1, (buy_cap * 4 + 3) // 5)
            else:
                sell_sz = max(1, (sell_cap * 4 + 3) // 5)

        if buy_cap > 0:
            orders.append(Order(OSMIUM, bid_price, buy_sz))
        if sell_cap > 0:
            orders.append(Order(OSMIUM, ask_price, -sell_sz))
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

        # Unwind-at-fair: near limit & near EOD, fire aggregated TAKE at fair (floor/ceil)
        near_eod = state.timestamp >= 900000
        if near_eod and abs(position) > 70:
            if position > 70 and best_bid is not None:
                target = min(int(mid), best_bid)
                orders.append(Order(PEPPER, target, -position))
                return orders
            if position < -70 and best_ask is not None:
                target = max(int(mid) + 1, best_ask)
                orders.append(Order(PEPPER, target, -position))
                return orders

        if position < POS_LIMIT:
            total_remaining = POS_LIMIT - position
            take_cap = min(total_remaining, PEPPER_TAKE_CAP)
            for p in sorted(depth.sell_orders.keys()):
                if take_cap <= 0:
                    break
                take = min(-depth.sell_orders[p], take_cap)
                if take > 0:
                    orders.append(Order(PEPPER, p, take))
                    take_cap -= take
                    total_remaining -= take
            if total_remaining > 0 and best_bid is not None and best_ask is not None:
                passive_bid = best_bid + 1
                if passive_bid < best_ask:
                    orders.append(Order(PEPPER, passive_bid, total_remaining))
        return orders
