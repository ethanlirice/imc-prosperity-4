from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]
CASES = [
    {"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}},
    {"case": "bid_on__MICROCHIP_OVAL", "kind": "bid_on", "product": "MICROCHIP_OVAL", "param": "", "env": {"MM_BID_ON_PRODUCTS": "MICROCHIP_OVAL"}},
    {"case": "bid_on__ROBOT_IRONING", "kind": "bid_on", "product": "ROBOT_IRONING", "param": "", "env": {"MM_BID_ON_PRODUCTS": "ROBOT_IRONING"}},
    {"case": "bid_on__UV_VISOR_AMBER", "kind": "bid_on", "product": "UV_VISOR_AMBER", "param": "", "env": {"MM_BID_ON_PRODUCTS": "UV_VISOR_AMBER"}},
    {"case": "ask_on__GALAXY_SOUNDS_BLACK_HOLES", "kind": "ask_on", "product": "GALAXY_SOUNDS_BLACK_HOLES", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "GALAXY_SOUNDS_BLACK_HOLES"}},
    {"case": "ask_on__MICROCHIP_SQUARE", "kind": "ask_on", "product": "MICROCHIP_SQUARE", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "MICROCHIP_SQUARE"}},
    {"case": "ask_on__OXYGEN_SHAKE_GARLIC", "kind": "ask_on", "product": "OXYGEN_SHAKE_GARLIC", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "OXYGEN_SHAKE_GARLIC"}},
    {"case": "ask_on__PANEL_2X4", "kind": "ask_on", "product": "PANEL_2X4", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "PANEL_2X4"}},
    {"case": "ask_on__SLEEP_POD_SUEDE", "kind": "ask_on", "product": "SLEEP_POD_SUEDE", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "SLEEP_POD_SUEDE"}},
    {"case": "ask_on__UV_VISOR_RED", "kind": "ask_on", "product": "UV_VISOR_RED", "param": "", "env": {"MM_ASK_ON_PRODUCTS": "UV_VISOR_RED"}},
]


def main():
    rows = []
    product_rows = []
    for idx, case in enumerate(CASES, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(CASES), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_side_on_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_side_on_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_side_on_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_side_on_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
