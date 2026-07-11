from concurrent.futures import ThreadPoolExecutor, as_completed

from _common import BASE_TOTAL, OUT_DIR, csv_text, run_case, write_csv

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

OWNED_PRODUCTS = [
    "ROBOT_DISHES",
    "PEBBLES_L",
    "OXYGEN_SHAKE_MINT",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_CHOCOLATE",
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "PANEL_2X2",
    "ROBOT_MOPPING",
    "ROBOT_VACUUMING",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SLEEP_POD_POLYESTER",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_YELLOW",
    "PEBBLES_XL",
    "PEBBLES_XS",
    "MICROCHIP_TRIANGLE",
]

ALL_MM = sorted(set(MM_PRODUCTS))


def build_cases():
    cases = [
        {"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}},
        {"case": "drop_all_current_mm", "kind": "drop_all", "product": "", "param": "", "env": {"DROP_MM_PRODUCTS": csv_text(ALL_MM)}},
    ]
    for product in ALL_MM:
        cases.append({"case": "drop_mm__" + product, "kind": "drop_mm", "product": product, "param": "", "env": {"DROP_MM_PRODUCTS": product}})
        cases.append({"case": "bid_off__" + product, "kind": "bid_off", "product": product, "param": "", "env": {"MM_BID_OFF_PRODUCTS": product}})
        cases.append({"case": "ask_off__" + product, "kind": "ask_off", "product": product, "param": "", "env": {"MM_ASK_OFF_PRODUCTS": product}})
        cases.append({"case": "bid_on__" + product, "kind": "bid_on", "product": product, "param": "", "env": {"MM_BID_ON_PRODUCTS": product}})
        cases.append({"case": "ask_on__" + product, "kind": "ask_on", "product": product, "param": "", "env": {"MM_ASK_ON_PRODUCTS": product}})
    for product in OWNED_PRODUCTS:
        cases.append({"case": "owned_mm__" + product, "kind": "owned_mm", "product": product, "param": "normal", "env": {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product}})
        cases.append({"case": "owned_mm_reduce__" + product, "kind": "owned_mm_reduce", "product": product, "param": "reduce", "env": {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product, "MM_REDUCE_ONLY_PRODUCTS": product}})
    return cases


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    rows = []
    product_rows = []
    print("running %d v11 MM attribution cases" % len(cases), flush=True)
    import os
    max_workers = int(os.environ.get("MM_V11_WORKERS", "1"))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_case, case) for case in cases]
        for idx, future in enumerate(as_completed(futures), 1):
            row, products = future.result()
            rows.append(row)
            product_rows.extend(products)
            if idx % 10 == 0 or int(row.get("delta", -10**9)) > 0:
                print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row.get("delta", ""), row.get("total", "")), flush=True)
            if idx % 10 == 0 or idx == len(cases):
                checkpoint = sorted(rows, key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
                write_csv(OUT_DIR / "v11_mm_attribution_summary.partial.csv", SUMMARY_FIELDS, checkpoint)
                write_csv(OUT_DIR / "v11_mm_attribution_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_attribution_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_attribution_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    baseline = [row for row in rows if row["case"] == "baseline"][0]
    print("baseline total=%s delta=%s expected_base=%s" % (baseline["total"], baseline["delta"], BASE_TOTAL), flush=True)
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]


if __name__ == "__main__":
    main()
