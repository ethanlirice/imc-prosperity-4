from _common import OUT_DIR, csv_text, run_case, write_csv

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
SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]
CONTRIB_FIELDS = ["product", "drop_total", "mm_contribution", "drop_day2", "contrib_day2", "drop_day3", "contrib_day3", "drop_day4", "contrib_day4", "status"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = [{"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}}]
    cases.append({"case": "drop_all_current_mm", "kind": "drop_all", "product": "", "param": "", "env": {"DROP_MM_PRODUCTS": csv_text(MM_PRODUCTS)}})
    for product in MM_PRODUCTS:
        cases.append({"case": "drop_mm__" + product, "kind": "drop_mm", "product": product, "param": "", "env": {"DROP_MM_PRODUCTS": product}})
    rows = []
    product_rows = []
    for idx, case in enumerate(cases, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_core_attribution_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_core_attribution_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    by_case = {row["case"]: row for row in rows}
    base = by_case["baseline"]
    contrib = []
    for product in MM_PRODUCTS:
        row = by_case["drop_mm__" + product]
        contrib.append(
            {
                "product": product,
                "drop_total": row["total"],
                "mm_contribution": base["total"] - row["total"],
                "drop_day2": row["day2"],
                "contrib_day2": base["day2"] - row["day2"],
                "drop_day3": row["day3"],
                "contrib_day3": base["day3"] - row["day3"],
                "drop_day4": row["day4"],
                "contrib_day4": base["day4"] - row["day4"],
                "status": row["status"],
            }
        )
    contrib.sort(key=lambda row: -int(row["mm_contribution"]))
    rows.sort(key=lambda row: (row["status"] != "ok", -int(row["delta"])))
    write_csv(OUT_DIR / "v11_mm_core_attribution_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_core_attribution_product_day.csv", PRODUCT_FIELDS, product_rows)
    write_csv(OUT_DIR / "v11_mm_contribution_by_product.csv", CONTRIB_FIELDS, contrib)
    print("wrote v11_mm_contribution_by_product.csv", flush=True)


if __name__ == "__main__":
    main()
