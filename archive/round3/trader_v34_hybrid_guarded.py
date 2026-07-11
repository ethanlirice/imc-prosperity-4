import archive.round3.trader_v32 as base
from datamodel import Order

# Website runs are short; avoid spending 20% of ticks in warmup.
base.ANCHOR_WARMUP = 50


class Trader(base.Trader):
    def hgp_scaled(self, depth, pos):
        sym = "HYDROGEL_PACK"
        if not depth.buy_orders or not depth.sell_orders:
            return []
        wm = self.wall_mid(depth)
        if wm is None:
            return []

        # Historical R3 book never exceeds ~30 visible lots per level.
        # Persist a guard for website anomaly regimes (e.g. 450 visible lots).
        max_visible = 0
        for v in depth.buy_orders.values():
            if v > max_visible:
                max_visible = v
        for v in depth.sell_orders.values():
            vv = -v
            if vv > max_visible:
                max_visible = vv
        if max_visible >= 50:
            self.sd["hgp_guard"] = True
        guarded = bool(self.sd.get("hgp_guard", False))

        fair_f = self.online_anchor("hgp_anchor", wm)
        if fair_f is None:
            return []
        FAIR = int(round(fair_f))

        TAKE_EDGE = 36
        TAKE_CLIP = 20
        PASSIVE_CLIP = 10
        SKEW = 4.0
        LIMIT = base.POS_LIMIT[sym]

        best_bid = max(depth.buy_orders)
        best_ask = min(depth.sell_orders)

        # Slow-state guard only applies once anomaly regime is detected.
        prev_slow = self.sd.get("hgp_slow_ema")
        slow_ema = wm if prev_slow is None else prev_slow + 0.005 * (wm - prev_slow)
        self.sd["hgp_slow_ema"] = slow_ema
        slow_dev = wm - slow_ema
        block_buy = guarded and slow_dev < -8.0 and pos > 20
        block_sell = guarded and slow_dev > 8.0 and pos < -20

        orders = []
        bc = max(0, LIMIT - pos)
        sc = max(0, LIMIT + pos)
        sim_pos = pos

        buy_left = 0 if block_buy else bc
        for ask_price in sorted(depth.sell_orders):
            if ask_price > FAIR - TAKE_EDGE or buy_left <= 0:
                break
            available = -depth.sell_orders[ask_price]
            quantity = min(available, buy_left, TAKE_CLIP)
            if quantity > 0:
                orders.append(Order(sym, ask_price, quantity))
                buy_left -= quantity
                sim_pos += quantity

        sell_left = 0 if block_sell else sc
        for bid_price in sorted(depth.buy_orders, reverse=True):
            if bid_price < FAIR + TAKE_EDGE or sell_left <= 0:
                break
            available = depth.buy_orders[bid_price]
            quantity = min(available, sell_left, TAKE_CLIP)
            if quantity > 0:
                orders.append(Order(sym, bid_price, -quantity))
                sell_left -= quantity
                sim_pos -= quantity

        used_buy = bc - buy_left if not block_buy else 0
        used_sell = sc - sell_left if not block_sell else 0
        bc_left = max(0, bc - used_buy)
        sc_left = max(0, sc - used_sell)

        adjusted_fair = FAIR - SKEW * (sim_pos / LIMIT)
        buy_quote = min(best_bid + 1, int(adjusted_fair))
        sell_base = adjusted_fair
        sell_quote = max(
            best_ask - 1,
            int(sell_base) if sell_base == int(sell_base) else int(sell_base) + 1,
        )

        if bc_left > 0 and buy_quote < best_ask and buy_quote < sell_quote:
            quantity = min(PASSIVE_CLIP, bc_left)
            if quantity > 0:
                orders.append(Order(sym, buy_quote, quantity))

        if sc_left > 0 and sell_quote > best_bid and sell_quote > buy_quote:
            quantity = min(PASSIVE_CLIP, sc_left)
            if quantity > 0:
                orders.append(Order(sym, sell_quote, -quantity))

        return orders

