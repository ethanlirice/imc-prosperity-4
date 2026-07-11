"""
v29 — Round 3 trader, iterated from v20 with forensic HYDROGEL execution.

Promoted result:
- v20 baseline reproduced locally: none=554,663, worse=560,271.
- v29: none=554,878, worse=657,744.
- Lift is entirely HYDROGEL in market-trade-sensitive matching:
  HYDROGEL worse total moves from 23,057 to 120,530 across D0-D2.

Verified-positive deltas vs v14 (data-driven):
1. CORE_OPTION_EMA_ALPHA = 2e-5 (was 0.0003).
   Evidence: alpha sweep shows monotonic improvement as alpha drops; v18 plateau.
2. CORE_OPTION_STRIKES extended to include 5400, 5500.
   Evidence: VEV_5400 fires 35-71/day → +9k contribution. VEV_5500 fires rarely (~5/3-days)
   but contributes a small positive (~991/3-days) under edge=3.
3. Per-strike `dynamic_edge`:
   - K == 4000: max(14, 1.5 * spread) — wide-edge override; deep ITM with wide L1 spread.
   - K >= 5400: max(3, spread)         — tight-edge for spread=1 OTM.
   - else:      max(5, spread)         — default.
   Evidence: A3 fire-rate test + simulation ceiling per-strike.
4. HYDROGEL_PACK fair = EMA(wall_mid), alpha moved to 0.02.
   Evidence: A1 isolation sweep — fixed=10000 yields 17,927; EMA-α=0.02 yields 23,236.
   Daily wall_mid means are 9991/9992/9989, never 10000.
5. HYDROGEL four-bot execution:
   - L2 wall maker -> fast EMA(wall_mid) fair.
   - L1 symmetric maker -> keep safe v20 two-sided outer quotes.
   - Aggressive buyer bot -> add inside ask when price is high vs slow EMA.
   - Aggressive seller bot -> add inside bid when price is low vs slow EMA.
   Evidence: notebook 05 passive replay showed EMA5000-aligned taker fading
   generated 52,321 vs 23,282 for quote-both and -25,937 for wrong-way fading.
   Hard one-sided quoting regressed in prosperity4btx, so v29 keeps both safe
   quote sides and adds a protected inside-L1 probe only when slow_dev is extreme.

Removed from v14 (verified zero contribution):
- smile_sleeve and its call from run() — dead code; backtest unchanged when removed.
- solve3 helper.
- bs_call, implied_vol, NormalDist import — only used by smile_sleeve.
- SMILE_STRIKES, FIT_STRIKES constants — only used by smile_sleeve.

NOT included (tested and rejected this session):
- Parity-driven fair on VEV_4000/4500 (regressed -118k vs v18).
- Free-option bids on VEV_6000/6500 (verified 0 EV — engine liquidates at 0).
- Inventory skew on options sizing (no measurable PnL change).
- Take-take IV scalping on spread-1 strikes (spread cost dominates).
"""
import json

from datamodel import Order, OrderDepth, TradingState

CORE_OPTION_STRIKES = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500]
POS_LIMIT = {"HYDROGEL_PACK": 200, "VELVETFRUIT_EXTRACT": 200}
for _k in [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]:
    POS_LIMIT[f"VEV_{_k}"] = 300

# HYDROGEL_PACK params — EMA(wall_mid) anchor (v20 change).
HYDROGEL_FAIR_ALPHA = 0.02
HYDROGEL_HALF_SPREAD = 4
HGP_ORDER_FRACTION = 0.4
HYDROGEL_FAIR_SEED = 10000.0  # used only on the very first tick before we see a wall
HGP_SLOW_ALPHA = 2.0 / 5001.0  # EMA5000 equivalent from notebook 05
HGP_SIZE_SKEW = 0.25
HGP_L3_MULT = 0.70
HGP_RECYCLE_POS = 80
HGP_PROBE_DEV = 10.0
HGP_PROBE_SIZE = 8  # plateau starts at 8; 12 was identical in tests

# Core option sleeve params.
CORE_OPTION_EMA_ALPHA = 0.00002
CORE_OPTION_INV_SKEW = 0.005
CORE_OPTION_TAKE_LOT = 30


class Trader:
    def __init__(self):
        self.sd = {}

    def best(self, depth):
        bid = max(depth.buy_orders) if depth.buy_orders else None
        ask = min(depth.sell_orders) if depth.sell_orders else None
        return bid, ask

    def wall_mid(self, depth):
        if not depth.buy_orders or not depth.sell_orders:
            return None
        return (min(depth.buy_orders) + max(depth.sell_orders)) / 2

    def vamp(self, depth):
        b, a = self.best(depth)
        if b is None or a is None:
            return None
        bv = depth.buy_orders[b]
        av = -depth.sell_orders[a]
        if bv + av == 0:
            return (b + a) / 2
        return (b * av + a * bv) / (bv + av)

    # HYDROGEL_PACK four-bot model:
    # 1. L2 wall maker: wall_mid is the fast fair anchor.
    # 2. L1 symmetric maker: keep the robust two-sided outer maker from v20.
    # 3. Aggressive seller bot: fade with an inside bid when low vs slow EMA.
    # 4. Aggressive buyer bot: fade with an inside ask when high vs slow EMA.
    def hgp_ntrader(self, depth, pos):
        sym = "HYDROGEL_PACK"
        if not depth.buy_orders or not depth.sell_orders:
            return []
        lim = POS_LIMIT[sym]
        b, a = self.best(depth)
        wm = self.wall_mid(depth)
        mid = (b + a) / 2
        prev = self.sd.get("hgp_fair")
        if prev is None:
            fair_value = wm if wm is not None else HYDROGEL_FAIR_SEED
        else:
            fair_value = prev + HYDROGEL_FAIR_ALPHA * ((wm if wm is not None else prev) - prev)
        self.sd["hgp_fair"] = fair_value

        prev_slow = self.sd.get("hgp_slow")
        slow = mid if prev_slow is None else prev_slow + HGP_SLOW_ALPHA * (mid - prev_slow)
        self.sd["hgp_slow"] = slow
        slow_dev = mid - slow
        has_bid3 = len(depth.buy_orders) >= 3
        has_ask3 = len(depth.sell_orders) >= 3

        half_spread = HYDROGEL_HALF_SPREAD
        orders = []
        # Aggressive take below fair-1.
        if a is not None and a < fair_value - 1:
            avail = abs(sum(v for p, v in depth.sell_orders.items() if p <= fair_value - 1))
            buy_qty = min(lim - pos, avail)
            if buy_qty > 0:
                orders.append(Order(sym, a, buy_qty))
                pos += buy_qty
        # Aggressive take above fair+1.
        if b is not None and b > fair_value + 1:
            avail = sum(v for p, v in depth.buy_orders.items() if p >= fair_value + 1)
            sell_qty = min(pos + lim, avail)
            if sell_qty > 0:
                orders.append(Order(sym, b, -sell_qty))
                pos -= sell_qty
        # Make with inventory skew.
        skew = int(pos / lim * half_spread)
        our_bid = int(round(fair_value)) - half_spread - skew
        our_ask = int(round(fair_value)) + half_spread - skew
        if b is not None:
            our_bid = min(our_bid, b)
        if a is not None:
            our_ask = max(our_ask, a)
        bc = lim - pos
        sc = lim + pos
        bid_mult = 1.0
        ask_mult = 1.0
        if slow_dev < 0:
            bid_mult += HGP_SIZE_SKEW
            ask_mult -= HGP_SIZE_SKEW
        elif slow_dev > 0:
            ask_mult += HGP_SIZE_SKEW
            bid_mult -= HGP_SIZE_SKEW
        if has_bid3:
            bid_mult *= HGP_L3_MULT
        if has_ask3:
            ask_mult *= HGP_L3_MULT
        if pos > HGP_RECYCLE_POS:
            ask_mult = max(ask_mult, 1.25)
            bid_mult *= 0.75
        elif pos < -HGP_RECYCLE_POS:
            bid_mult = max(bid_mult, 1.25)
            ask_mult *= 0.75

        bs = min(bc, max(1, int(bc * HGP_ORDER_FRACTION * bid_mult)))
        asz = min(sc, max(1, int(sc * HGP_ORDER_FRACTION * ask_mult)))
        if bc > 0 and our_bid > 0:
            orders.append(Order(sym, our_bid, bs))
        if sc > 0:
            orders.append(Order(sym, our_ask, -asz))

        # Tiny inside-L1 probe for the exact notebook-05 passive edge. The strict
        # threshold keeps it out of normal backtester-adverse quote churn.
        if b + 1 < a - 1:
            if slow_dev < -HGP_PROBE_DEV and not has_bid3 and bc > 0 and pos < HGP_RECYCLE_POS:
                orders.append(Order(sym, b + 1, min(HGP_PROBE_SIZE, bc)))
            elif slow_dev > HGP_PROBE_DEV and not has_ask3 and sc > 0 and pos > -HGP_RECYCLE_POS:
                orders.append(Order(sym, a - 1, -min(HGP_PROBE_SIZE, sc)))
        return orders

    # VELVETFRUIT_EXTRACT: random-walk MM around vamp, take/clear/make. (unchanged from v14)
    def mm_rw(self, sym, depth, pos, key, alpha=0.2, take_w=1, clear_w=2, max_sz=50):
        lim = POS_LIMIT[sym]
        orders = []
        v = self.vamp(depth)
        if v is None:
            return orders
        prev = self.sd.get(key)
        fv = v if prev is None else prev + alpha * (v - prev)
        self.sd[key] = fv
        b, a = self.best(depth)
        bc = lim - pos
        sc = lim + pos
        for px in sorted(depth.sell_orders):
            if px <= fv - take_w and bc > 0:
                vol = min(-depth.sell_orders[px], bc)
                if vol > 0:
                    orders.append(Order(sym, px, vol))
                    bc -= vol
        for px in sorted(depth.buy_orders, reverse=True):
            if px >= fv + take_w and sc > 0:
                vol = min(depth.buy_orders[px], sc)
                if vol > 0:
                    orders.append(Order(sym, px, -vol))
                    sc -= vol
        pa = pos + sum(o.quantity for o in orders)
        if pa > 0:
            p = int(round(fv + clear_w))
            if p in depth.buy_orders and sc > 0:
                v2 = min(depth.buy_orders[p], pa, sc)
                if v2 > 0:
                    orders.append(Order(sym, p, -v2))
                    sc -= v2
        elif pa < 0:
            p = int(round(fv - clear_w))
            if p in depth.sell_orders and bc > 0:
                v2 = min(-depth.sell_orders[p], -pa, bc)
                if v2 > 0:
                    orders.append(Order(sym, p, v2))
                    bc -= v2
        if b is not None and a is not None:
            sp = a - b
            edge = max(1, sp // 2)
            mb = int(round(fv - edge))
            ma = int(round(fv + edge))
            if mb <= b:
                mb = b + 1
            if ma >= a:
                ma = a - 1
            if mb < ma:
                if bc > 0:
                    orders.append(Order(sym, mb, min(max_sz, bc)))
                if sc > 0:
                    orders.append(Order(sym, ma, -min(max_sz, sc)))
        return orders

    # Core option sleeve: ultra-slow per-strike anchor + per-strike edge thresholds. (v15-v18)
    def trade_core_option(self, sym, depth, pos, out):
        b, a = self.best(depth)
        if b is None or a is None:
            return
        bv = depth.buy_orders[b]
        av = -depth.sell_orders[a]
        mid = (b + a) / 2
        spread = a - b
        K = int(sym.split("_")[-1])
        key = f"oema_{sym}"
        prev = self.sd.get(key)
        fair_raw = mid if prev is None else prev
        fair = fair_raw - CORE_OPTION_INV_SKEW * pos
        if K == 4000:
            dynamic_edge = max(14.0, spread * 1.5)
        elif K >= 5400:
            dynamic_edge = max(3.0, spread * 1.0)
        else:
            dynamic_edge = max(5.0, spread * 1.0)
        lim = POS_LIMIT[sym]
        bc = lim - pos
        sc = lim + pos
        if a <= fair - dynamic_edge:
            q = min(CORE_OPTION_TAKE_LOT, av, bc)
            if q > 0:
                out.setdefault(sym, []).append(Order(sym, a, q))
        elif b >= fair + dynamic_edge:
            q = min(CORE_OPTION_TAKE_LOT, bv, sc)
            if q > 0:
                out.setdefault(sym, []).append(Order(sym, b, -q))
        new_ema = fair_raw + CORE_OPTION_EMA_ALPHA * (mid - fair_raw)
        self.sd[key] = new_ema

    def run(self, state):
        if state.traderData:
            try:
                self.sd = json.loads(state.traderData)
            except Exception:
                self.sd = {}
        else:
            self.sd = {}
        result = {}

        if "HYDROGEL_PACK" in state.order_depths:
            pos = state.position.get("HYDROGEL_PACK", 0)
            result["HYDROGEL_PACK"] = self.hgp_ntrader(state.order_depths["HYDROGEL_PACK"], pos)

        if "VELVETFRUIT_EXTRACT" in state.order_depths:
            pos = state.position.get("VELVETFRUIT_EXTRACT", 0)
            result["VELVETFRUIT_EXTRACT"] = self.mm_rw(
                "VELVETFRUIT_EXTRACT",
                state.order_depths["VELVETFRUIT_EXTRACT"],
                pos,
                "vfv",
                max_sz=50,
            )

        for K in CORE_OPTION_STRIKES:
            sym = f"VEV_{K}"
            if sym in state.order_depths:
                pos = state.position.get(sym, 0)
                self.trade_core_option(sym, state.order_depths[sym], pos, result)

        return result, 0, json.dumps(self.sd)
