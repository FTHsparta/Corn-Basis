import pandas as pd

from load import load_merged

MARKET = ["kansas_city", "dodge_city", "garden_city"]

def add_basis(df):
    for market in MARKET:
        df[f"{market}_basis"] = df[market] - df["nearby"]
        df[f"{market}_basis_pct"] = df[f"{market}_basis"] / df["nearby"] * 100
        assert df[f"{market}_basis"].count() == (df[market].notna() & df["nearby"].notna()).sum(), f"basis count does not match null nearby values for {market}"
        
    row = df["cash_date"] == "2026-09-03"
    kc_basis = df.loc[row, "kansas_city_basis"].iloc[0]
    kc_basis_pct = df.loc[row, "kansas_city_basis_pct"].iloc[0]

    assert abs(kc_basis - 0.03125) < 1e-6, f"Expected KC basis 0.03125 on 2026-09-03, got {kc_basis}"
    assert abs(kc_basis_pct - 0.6037) < 1e-3, f"Expected KC basis pct 0.6037 on 2026-09-03, got {kc_basis_pct}"


    return df

if __name__ == "__main__":
    merged = load_merged("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")

    merged_cols = ["cash_date", "futures_date"] + MARKET + ["nearby"]
    print("=== merged ===")
    print(merged[merged_cols].head())
    print(merged[merged_cols].tail())
    print("\n=== missing values ===")
    print(merged.isna().sum())

    df = add_basis(merged)

    basis_cols = (
        ["cash_date", "nearby"]
        + [f"{market}_basis" for market in MARKET]
        + [f"{market}_basis_pct" for market in MARKET]
    )

    print("\n=== basis ===")
    print(df[basis_cols].head())
    print(df[basis_cols].tail())