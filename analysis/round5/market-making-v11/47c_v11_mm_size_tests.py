from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]
CASES = [
    {"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}},
    {"case": "size_2__OXYGEN_SHAKE_GARLIC", "kind": "size", "product": "OXYGEN_SHAKE_GARLIC", "param": "2", "env": {"MM_SIZE_BY_PRODUCT": "OXYGEN_SHAKE_GARLIC:2"}},
    {"case": "size_5__OXYGEN_SHAKE_GARLIC", "kind": "size", "product": "OXYGEN_SHAKE_GARLIC", "param": "5", "env": {"MM_SIZE_BY_PRODUCT": "OXYGEN_SHAKE_GARLIC:5"}},
    {"case": "size_10__OXYGEN_SHAKE_GARLIC", "kind": "size", "product": "OXYGEN_SHAKE_GARLIC", "param": "10", "env": {"MM_SIZE_BY_PRODUCT": "OXYGEN_SHAKE_GARLIC:10"}},
    {"case": "size_2__GALAXY_SOUNDS_PLANETARY_RINGS", "kind": "size", "product": "GALAXY_SOUNDS_PLANETARY_RINGS", "param": "2", "env": {"MM_SIZE_BY_PRODUCT": "GALAXY_SOUNDS_PLANETARY_RINGS:2"}},
    {"case": "size_5__GALAXY_SOUNDS_PLANETARY_RINGS", "kind": "size", "product": "GALAXY_SOUNDS_PLANETARY_RINGS", "param": "5", "env": {"MM_SIZE_BY_PRODUCT": "GALAXY_SOUNDS_PLANETARY_RINGS:5"}},
    {"case": "size_10__GALAXY_SOUNDS_PLANETARY_RINGS", "kind": "size", "product": "GALAXY_SOUNDS_PLANETARY_RINGS", "param": "10", "env": {"MM_SIZE_BY_PRODUCT": "GALAXY_SOUNDS_PLANETARY_RINGS:10"}},
    {"case": "size_2__MICROCHIP_CIRCLE", "kind": "size", "product": "MICROCHIP_CIRCLE", "param": "2", "env": {"MM_SIZE_BY_PRODUCT": "MICROCHIP_CIRCLE:2"}},
    {"case": "size_5__MICROCHIP_CIRCLE", "kind": "size", "product": "MICROCHIP_CIRCLE", "param": "5", "env": {"MM_SIZE_BY_PRODUCT": "MICROCHIP_CIRCLE:5"}},
    {"case": "size_10__MICROCHIP_CIRCLE", "kind": "size", "product": "MICROCHIP_CIRCLE", "param": "10", "env": {"MM_SIZE_BY_PRODUCT": "MICROCHIP_CIRCLE:10"}},
    {"case": "size_2__PANEL_2X4", "kind": "size", "product": "PANEL_2X4", "param": "2", "env": {"MM_SIZE_BY_PRODUCT": "PANEL_2X4:2"}},
    {"case": "size_5__PANEL_2X4", "kind": "size", "product": "PANEL_2X4", "param": "5", "env": {"MM_SIZE_BY_PRODUCT": "PANEL_2X4:5"}},
    {"case": "size_10__PANEL_2X4", "kind": "size", "product": "PANEL_2X4", "param": "10", "env": {"MM_SIZE_BY_PRODUCT": "PANEL_2X4:10"}},
    {"case": "size_2__ROBOT_IRONING", "kind": "size", "product": "ROBOT_IRONING", "param": "2", "env": {"MM_SIZE_BY_PRODUCT": "ROBOT_IRONING:2"}},
    {"case": "size_5__ROBOT_IRONING", "kind": "size", "product": "ROBOT_IRONING", "param": "5", "env": {"MM_SIZE_BY_PRODUCT": "ROBOT_IRONING:5"}},
    {"case": "size_10__ROBOT_IRONING", "kind": "size", "product": "ROBOT_IRONING", "param": "10", "env": {"MM_SIZE_BY_PRODUCT": "ROBOT_IRONING:10"}},
]


def main():
    rows = []
    product_rows = []
    for idx, case in enumerate(CASES, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(CASES), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_size_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_size_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_size_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_size_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
