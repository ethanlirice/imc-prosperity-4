from importlib.machinery import SourceFileLoader


mod = SourceFileLoader("sweep36", "analysis/round5/hidden-paths/36_reanchor_integration_sweep.py").load_module()

CASES = [
    ("robot_mint", "ROBOT_DISHES,OXYGEN_SHAKE_MINT"),
    ("robot_strawberry", "ROBOT_DISHES,SNACKPACK_STRAWBERRY"),
    ("robot_chocolate", "ROBOT_DISHES,SNACKPACK_CHOCOLATE"),
    ("robot_mint_strawberry", "ROBOT_DISHES,OXYGEN_SHAKE_MINT,SNACKPACK_STRAWBERRY"),
    ("robot_mint_chocolate", "ROBOT_DISHES,OXYGEN_SHAKE_MINT,SNACKPACK_CHOCOLATE"),
    ("robot_strawberry_chocolate", "ROBOT_DISHES,SNACKPACK_STRAWBERRY,SNACKPACK_CHOCOLATE"),
    ("robot_mint_strawberry_chocolate", "ROBOT_DISHES,OXYGEN_SHAKE_MINT,SNACKPACK_STRAWBERRY,SNACKPACK_CHOCOLATE"),
    ("mint_strawberry_chocolate", "OXYGEN_SHAKE_MINT,SNACKPACK_STRAWBERRY,SNACKPACK_CHOCOLATE"),
]


def main():
    for name, products in CASES:
        print("running", name, products, flush=True)
        row, _ = mod.run_case(name, products)
        print(row, flush=True)


if __name__ == "__main__":
    main()
