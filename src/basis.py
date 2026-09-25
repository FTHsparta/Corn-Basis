import pandas as pd

from load import load_merged

MARKET = ["kansas_city", "dodge_city", "garden_city"]
SAMPLE_START = "2005-01-01"

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

def filter_sample(df, start = SAMPLE_START):
    study_sample = df[df["cash_date"] >= start] #creates the study sample using the start date (No data values before Jan 1st, 2005)
    trimmed = study_sample.dropna(subset = ["nearby"]) #deletes the rows missing nearby values

    before = len(study_sample) #counts length of study sample before trimming
    dropped = before - len(trimmed) #subtracts the length before with the trimmed to get the number of dropped rows

    

    assert trimmed["nearby"].isna().sum() == 0, f"Missing value in nearby columns" #makes sure that trimmed sample has no missing nearby values
    assert dropped == 2, f"Expected 2 rows with missing nearby values but got {dropped}" #makes sure that correct number of rows were dropped

    return trimmed.reset_index(drop=True) #resets the index of the trimmed study sample

def missing_observations(df):
    for market in MARKET:
        df[f"{market}_missing"] = df[market].isna() 
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
    filtered = filter_sample(df)

    filtered = missing_observations(filtered)
    for market in MARKET:
        print(f"\n{market} missing:")
        print(filtered.loc[filtered[f"{market}_missing"], "cash_date"])
        
    print("\n=== filtered ===")
    print(filtered.isna().sum())


    basis_cols = (
        ["cash_date", "nearby"]
        + [f"{market}_basis" for market in MARKET]
        + [f"{market}_basis_pct" for market in MARKET]
    )

    print("\n=== basis ===")
    print(filtered[basis_cols].head())
    print(filtered[basis_cols].tail())