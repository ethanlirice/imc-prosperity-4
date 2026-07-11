from _common import OUT_DIR, product_size_map, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]

TWO_SIDED = [
    "PEBBLES_S",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "SLEEP_POD_NYLON",
    "UV_VISOR_ORANGE",
    "MICROCHIP_CIRCLE",
]
ONE_SIDED = [
    "MICROCHIP_OVAL",
    "OXYGEN_SHAKE_GARLIC",
    "GALAXY_SOUNDS_BLACK_HOLES",
    "MICROCHIP_SQUARE",
    "UV_VISOR_AMBER",
    "ROBOT_IRONING",
    "PANEL_2X4",
    "SLEEP_POD_SUEDE",
    "UV_VISOR_RED",
]
SIZE_CANDIDATES = [
    "PEBBLES_S",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "GALAXY_SOUNDS_BLACK_HOLES",
    "OXYGEN_SHAKE_CHOCOLATE",
    "PANEL_1X4",
    "UV_VISOR_AMBER",
    "SLEEP_POD_SUEDE",
]
OWNED_PRODUCTS = [
    "ROBOT_DISHES",
    "PEBBLES_L",
    "OXYGEN_SHAKE_MINT",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_CHOCOLATE",
]
BASE_SIZE_OVERRIDES = {
    "GALAXY_SOUNDS_PLANETARY_RINGS": 1,
    "UV_VISOR_ORANGE": 1,
    "OXYGEN_SHAKE_MORNING_BREATH": 1,
    "OXYGEN_SHAKE_GARLIC": 1,
    "MICROCHIP_CIRCLE": 1,
    "PANEL_2X4": 1,
    "ROBOT_IRONING": 1,
}


def add(cases, case, kind, product="", param="", env=None):
    cases.append({"case": case, "kind": kind, "product": product, "param": param, "env": env or {}})


def build_cases():
    cases = []
    add(cases, "baseline", "baseline")
    for product in TWO_SIDED:
        add(cases, "bid_off__" + product, "bid_off", product, env={"MM_BID_OFF_PRODUCTS": product})
        add(cases, "ask_off__" + product, "ask_off", product, env={"MM_ASK_OFF_PRODUCTS": product})
        add(cases, "reduce_only__" + product, "reduce_only", product, env={"MM_REDUCE_ONLY_PRODUCTS": product})
    for product in ONE_SIDED:
        add(cases, "bid_on__" + product, "bid_on", product, env={"MM_BID_ON_PRODUCTS": product})
        add(cases, "ask_on__" + product, "ask_on", product, env={"MM_ASK_ON_PRODUCTS": product})
        add(cases, "reduce_only__" + product, "reduce_only", product, env={"MM_REDUCE_ONLY_PRODUCTS": product})
    for product in SIZE_CANDIDATES:
        for size in (1, 2, 5, 10):
            add(cases, "size_%s__%s" % (size, product), "size", product, str(size), {"MM_SIZE_BY_PRODUCT": "%s:%s" % (product, size)})
    for product in ("PEBBLES_S", "MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", "ROBOT_IRONING"):
        for threshold in (3, 5):
            add(cases, "inv_reduce_%s__%s" % (threshold, product), "inv_reduce", product, str(threshold), {"MM_INVENTORY_REDUCE_THRESHOLD": str(threshold), "MM_REDUCE_ONLY_PRODUCTS": product})
    for product in ("PEBBLES_S", "MICROCHIP_SQUARE", "OXYGEN_SHAKE_GARLIC", "ROBOT_IRONING", "SLEEP_POD_SUEDE", "MICROCHIP_CIRCLE"):
        for threshold in (0.2, 0.4):
            add(cases, "imb_%s__%s" % (str(threshold).replace(".", "p"), product), "imbalance", product, str(threshold), {"MM_IMB_FILTER_PRODUCTS": product, "MM_IMB_THRESHOLD_BY_PRODUCT": "%s:%s" % (product, threshold)})
    for product in OWNED_PRODUCTS:
        add(cases, "owned_mm__" + product, "owned_mm", product, "normal", {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product})
        add(cases, "owned_mm_reduce__" + product, "owned_mm_reduce", product, "reduce", {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product, "MM_REDUCE_ONLY_PRODUCTS": product})
    add(cases, "remove_all_size_overrides", "bundle", "", "", {"MM_SIZE_BY_PRODUCT": product_size_map((product, 10) for product in sorted(BASE_SIZE_OVERRIDES))})
    return cases


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    product_rows = []
    cases = build_cases()
    print("running %d targeted v11 MM cases" % len(cases), flush=True)
    for idx, case in enumerate(cases, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_targeted_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_targeted_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_targeted_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_targeted_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
