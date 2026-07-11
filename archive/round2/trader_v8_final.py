"""
Round 2 trader v8_final — v7_final + OSMIUM 10000-anchor fair value.

CORE CHANGE vs v7_final:
  OSMIUM fair value is now anchor-blended:
    fair_value = wall_mid + alpha * (10000 - wall_mid)
  with alpha = 0.58 (empirical plateau; tested 0.3..1.0).

Rationale: OSMIUM mid shows strong mean reversion to 10000. On R1 and R2
data, corr(dev-from-10000, future_return) ≈ -0.66 to -0.80 at lags
500-2000 ticks. The half-reversion coefficient is ~0.55-0.60.

The previous FV (wall_mid alone) ignored this, causing biased takes:
when wall_mid drifted to 10005, old logic would buy asks at 10004 (edge
1 vs wall, but near breakeven vs the true 10000 mean). New FV of 10002.9
makes the take threshold 10002, skipping the adverse trade.

Backtest (R2, 3 days, prosperity4btx):
  --match-trades none  : 252,967  (+3,882 vs v7_final 249,085)
  --match-trades worse : 301,531  (+3,229 vs v7_final 298,302)

alpha=0.5 gives 252,399/301,687 (slightly higher worse, lower none).
alpha=0.58 is primary-metric peak across 0.3..1.0 sweep.

Takes capture the entire gain; makes are neutral (verified via
trader_v8_takesonly.py control).

v8 iteration rejected (all regressed or near-neutral):
  v8b asymmetric edge by dev bucket:     −654/−3050
  v8c aggressive cover at anchor:        −490/−181
  v8d edge=0 takes at |dev|>=5:          +238/−173
  v8e tight fair-based make:             0/−42,284  (catastrophic worse)
  v8f tight+clip make:                   0/−38,848
  v8g v8a + anchor-clip on makes:        0/−3,007
  Dynamic alpha (piecewise on |dev|):    −1,038/−2,105
  OBI-weighted FV blend (w=-1..2):       ±77 near-noise
  Size-filter toxic takes (15..25):      0/−156 noise
  Cover-width sweep (-1..1):             near-noise
  Asymmetric tight make:                 0/−27,024

OSMIUM architecture (mostly unchanged from v7_final):
  - Fair value = wall_mid + 0.58*(10000 - wall_mid)
    Still uses wall_mid computed from (min_bid + max_ask)/2 on deep books,
    with persistence on shallow books (<2 levels AND spread <18).
  - Takes: buy at p <= fair-1, sell at p >= fair+1, cover at fair.
  - Makes: penny-inside wall, clipped to not cross fair (unchanged).
  - Size skew at |pos|>=30 (80%) and |pos|>=55 (67%) (unchanged).

PEPPER unchanged (7-tick take cap + passive bb+1 fallback).
MAF bid unchanged (2000).

Backtest:
  prosperity4btx trader.py 2 --match-trades none  --merge-pnl --data ./data
  prosperity4btx trader.py 2 --match-trades worse --merge-pnl --data ./data
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
