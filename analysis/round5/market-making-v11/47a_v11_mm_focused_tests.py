from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]


def case(name, kind, product="", param="", env=None):
    return {"case": name, "kind": kind, "product": product, "param": param, "env": env or {}}


def build_cases():
    cases = [case("baseline", "baseline")]
    for product in ["PEBBLES_S", "GALAXY_SOUNDS_PLANETARY_RINGS", "OXYGEN_SHAKE_CHOCOLATE", "MICROCHIP_CIRCLE"]:
        cases.append(case("bid_off__" + product, "bid_off", product, env={"MM_BID_OFF_PRODUCTS": product}))
        cases.append(case("ask_off__" + product, "ask_off", product, env={"MM_ASK_OFF_PRODUCTS": product}))
    for product in ["MICROCHIP_OVAL", "OXYGEN_SHAKE_GARLIC", "GALAXY_SOUNDS_BLACK_HOLES", "MICROCHIP_SQUARE", "ROBOT_IRONING", "SLEEP_POD_SUEDE", "UV_VISOR_AMBER"]:
        cases.append(case("bid_on__" + product, "bid_on", product, env={"MM_BID_ON_PRODUCTS": product}))
        cases.append(case("ask_on__" + product, "ask_on", product, env={"MM_ASK_ON_PRODUCTS": product}))
        cases.append(case("reduce_only__" + product, "reduce_only", product, env={"MM_REDUCE_ONLY_PRODUCTS": product}))
    for product in ["OXYGEN_SHAKE_GARLIC", "GALAXY_SOUNDS_PLANETARY_RINGS", "MICROCHIP_CIRCLE", "ROBOT_IRONING", "PANEL_2X4"]:
        for size in [2, 5, 10]:
            cases.append(case("size_%s__%s" % (size, product), "size", product, str(size), {"MM_SIZE_BY_PRODUCT": "%s:%s" % (product, size)}))
    for product in ["MICROCHIP_OVAL", "MICROCHIP_SQUARE", "PEBBLES_S", "OXYGEN_SHAKE_GARLIC"]:
        for threshold in ["0.2", "0.4"]:
            cases.append(case("imb_%s__%s" % (threshold.replace(".", "p"), product), "imbalance", product, threshold, {"MM_IMB_FILTER_PRODUCTS": product, "MM_IMB_THRESHOLD_BY_PRODUCT": "%s:%s" % (product, threshold)}))
    for product in ["ROBOT_DISHES", "PEBBLES_L", "OXYGEN_SHAKE_MINT", "SNACKPACK_STRAWBERRY", "SNACKPACK_CHOCOLATE"]:
        cases.append(case("owned_mm_reduce__" + product, "owned_mm_reduce", product, "reduce", {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product, "MM_REDUCE_ONLY_PRODUCTS": product}))
    return cases


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    product_rows = []
    cases = build_cases()
    print("running %d focused v11 MM cases" % len(cases), flush=True)
    for idx, item in enumerate(cases, 1):
        row, products = run_case(item)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_focused_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_focused_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_focused_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_focused_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
