from concurrent.futures import ThreadPoolExecutor, as_completed

from _common import OUT_DIR, csv_text, product_size_map, run_case, write_csv

MM_PRODUCTS = [
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PANEL_2X4",
    "PEBBLES_S",
    "ROBOT_IRONING",
    "ROBOT_LAUNDRY",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_SUEDE",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
]

BASE_SIZE_OVERRIDES = {
    "GALAXY_SOUNDS_PLANETARY_RINGS": 1,
    "UV_VISOR_ORANGE": 1,
    "OXYGEN_SHAKE_MORNING_BREATH": 1,
    "OXYGEN_SHAKE_GARLIC": 1,
    "MICROCHIP_CIRCLE": 1,
    "PANEL_2X4": 1,
    "SNACKPACK_STRAWBERRY": 2,
    "ROBOT_IRONING": 1,
}


def build_cases():
    cases = [{"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}}]
    for size in (1, 2, 3, 5, 7, 10):
        cases.append({"case": "global_size_%s" % size, "kind": "global_size", "product": "", "param": str(size), "env": {"MM_SIZE": str(size)}})
    for product in MM_PRODUCTS:
        for size in (0, 1, 2, 3, 5, 10):
            env = {"MM_SIZE_BY_PRODUCT": "%s:%s" % (product, size)}
            kind = "drop_via_size" if size == 0 else "product_size"
            cases.append({"case": "size_%s__%s" % (size, product), "kind": kind, "product": product, "param": str(size), "env": env})
        cases.append({"case": "flat_only__" + product, "kind": "flat_only", "product": product, "param": "", "env": {"MM_FLAT_ONLY_PRODUCTS": product}})
        cases.append({"case": "reduce_only__" + product, "kind": "reduce_only", "product": product, "param": "", "env": {"MM_REDUCE_ONLY_PRODUCTS": product}})
        for threshold in (3, 5, 8):
            cases.append({"case": "inv_reduce_%s__%s" % (threshold, product), "kind": "inv_reduce", "product": product, "param": str(threshold), "env": {"MM_INVENTORY_REDUCE_THRESHOLD": str(threshold), "MM_REDUCE_ONLY_PRODUCTS": product}})
        for offset in (1, 2):
            cases.append({"case": "offset_%s__%s" % (offset, product), "kind": "offset", "product": product, "param": str(offset), "env": {"MM_OFFSET_BY_PRODUCT": "%s:%s" % (product, offset)}})
        for threshold in (0.2, 0.4, 0.6):
            cases.append({"case": "imb_%s__%s" % (str(threshold).replace(".", "p"), product), "kind": "imbalance", "product": product, "param": str(threshold), "env": {"MM_IMB_FILTER_PRODUCTS": product, "MM_IMB_THRESHOLD_BY_PRODUCT": "%s:%s" % (product, threshold)}})
    without_size_overrides = csv_text(sorted(BASE_SIZE_OVERRIDES))
    cases.append({"case": "remove_all_size_overrides", "kind": "bundle", "product": "", "param": "", "env": {"MM_SIZE_BY_PRODUCT": product_size_map((product, 10) for product in sorted(BASE_SIZE_OVERRIDES))}})
    for product, size in BASE_SIZE_OVERRIDES.items():
        cases.append({"case": "remove_size_override__" + product, "kind": "remove_size_override", "product": product, "param": str(size), "env": {"MM_SIZE_BY_PRODUCT": "%s:10" % product}})
    return cases


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    rows = []
    product_rows = []
    print("running %d v11 MM refinement cases" % len(cases), flush=True)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_case, case) for case in cases]
        for idx, future in enumerate(as_completed(futures), 1):
            row, products = future.result()
            rows.append(row)
            product_rows.extend(products)
            if idx % 15 == 0 or int(row.get("delta", -10**9)) > 0:
                print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row.get("delta", ""), row.get("total", "")), flush=True)
            if idx % 15 == 0 or idx == len(cases):
                checkpoint = sorted(rows, key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
                write_csv(OUT_DIR / "v11_mm_refinement_summary.partial.csv", SUMMARY_FIELDS, checkpoint)
                write_csv(OUT_DIR / "v11_mm_refinement_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_refinement_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_refinement_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]


if __name__ == "__main__":
    main()
