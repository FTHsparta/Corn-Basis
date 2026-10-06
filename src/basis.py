import pandas as pd
from pathlib import Path

from load import load_merged


MARKET = ["kansas_city", "dodge_city", "garden_city"]
SAMPLE_START = "2005-01-01"

def add_basis(df):
    for market in MARKET:
        df[f"{market}_basis"] = (df[market] - df["nearby"]) * 100 #calculates basis in cents
        df[f"{market}_basis_pct"] = (df[market] - df["nearby"]) / df["nearby"] * 100 #calculates percentage basis
        assert df[f"{market}_basis"].count() == (df[market].notna() & df["nearby"].notna()).sum(), f"basis count does not match null nearby values for {market}"
        
    row = df["cash_date"] == "2026-09-03"
    kc_basis = df.loc[row, "kansas_city_basis"].iloc[0]
    kc_basis_pct = df.loc[row, "kansas_city_basis_pct"].iloc[0]

    assert abs(kc_basis - 3.125) < 1e-6, f"Expected KC basis 3.125 on 2026-09-03, got {kc_basis}"
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

def export_excel(df, path):
    Path("output").mkdir(exist_ok = True)
    columns = (["cash_date", "futures_date"] + MARKET +["nearby"] + [f"{market}_basis" for market in MARKET] + [f"{market}_basis_pct" for market in MARKET] + [f"{market}_missing" for market in MARKET])
    data = df[columns].copy()
    date_cols = ["cash_date", "futures_date"]

    for col in date_cols:
        data[col] = data[col].dt.date

    gaps = []
    for market in MARKET:
        rows = df.loc[df[f"{market}_missing"], ["cash_date"]].copy()
        rows["market"] = market
        gaps.append(rows)
    missing = pd.concat(gaps)

    missing["cash_date"] = missing["cash_date"].dt.date
    missing = missing.reset_index(drop = True)


    with pd.ExcelWriter(path) as writer:
        data.to_excel(writer, sheet_name="data", index=False)
        missing.to_excel(writer, sheet_name="missing", index=False)

def interpolate_missing(df):
    df = df.copy()
    df = df.sort_values("cash_date").reset_index(drop=True)
    cash_copy = df[MARKET].copy()

    for market in MARKET:
       filled = df[f"{market}"].interpolate(method = "linear")
       not_missing = ~df[f"{market}_missing"]

       assert filled.isna().sum() == 0, f"There are missing values after interpolation"
       assert (filled[not_missing] == cash_copy[market][not_missing]).all(), f"{market}: a real week changed"


       df[market] = filled
    df = add_basis(df)

    row = df["cash_date"] == "2006-06-15"
    row1 = df["cash_date"] == "2006-06-08"
    row2 = df["cash_date"] == "2006-06-22"

    garden_city_before = df.loc[row1, "garden_city"].iloc[0]
    garden_city_after = df.loc[row2, "garden_city"].iloc[0]

    expected_value = ((garden_city_after + garden_city_before)/2)

    assert abs(df.loc[row, "garden_city"].iloc[0] - expected_value) < 1e-3, f"Garden City 6/15/2006 is not the average of 6/8 and 6/22"

    last_real = df["cash_date"] == "2013-09-26"
    first_filled = df["cash_date"] == "2013-10-03"
    second_filled = df["cash_date"] == "2013-10-10"
    second_real = df["cash_date"] == "2013-10-17"

    kc_last_real = df.loc[last_real, "kansas_city"].iloc[0]
    kc_first_filled = df.loc[first_filled, "kansas_city"].iloc[0]
    kc_second_filled = df.loc[second_filled, "kansas_city"].iloc[0]
    kc_second_real = df.loc[second_real, "kansas_city"].iloc[0]

    jump1 = kc_first_filled - kc_last_real
    jump2 = kc_second_filled - kc_first_filled
    jump3 = kc_second_real - kc_second_filled

    assert abs(jump1 - jump2) < 1e-6, f"The jump from 9/26/13 to 10/3/13 does not equal the jump from 10/3/13 to 10/10/13"
    assert abs(jump2 - jump3) < 1e-6, f"The jump from 10/03/13 to 10/10/13 does not equal the jump from 10/10/13 to 10/17/13"



    return df

def build_dataset(cash_path, futures_path):
    merged = load_merged(cash_path, futures_path)
    df = add_basis(merged)
    filtered = filter_sample(df)
    filtered = missing_observations(filtered)
    interpolated = interpolate_missing(filtered)

    assert len(interpolated) == 1131, f"Number of rows does not equal 1131 in interpolated data"
    assert interpolated["cash_date"].iloc[0] == pd.Timestamp("2005-01-06"), f"First date does not match expected value"
    assert interpolated["cash_date"].iloc[-1] == pd.Timestamp("2026-09-03"), f"last date does not match expected value"
    basis_columns = ([f"{market}_basis" for market in MARKET] + [f"{market}_basis_pct" for market in MARKET])
    assert interpolated[basis_columns].isna().sum().sum() == 0, f"There are still missing values after interpolating"
    missing_columns = ([f"{market}_missing" for market in MARKET])
    assert interpolated[missing_columns].sum().sum() == 12, f"Expected 12 flagged weeks"

    return interpolated



if __name__ == "__main__":
    interpolated = build_dataset("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")

    
    for market in MARKET:
        print(f"\n{market} missing:")
        print(interpolated.loc[interpolated[f"{market}_missing"], "cash_date"])
        


    
    check_dates = pd.to_datetime(["2006-06-08", "2006-06-15", "2006-06-22", "2013-09-26", "2013-10-03", "2013-10-10", "2013-10-17"])
    check_cols = ["cash_date"] + MARKET + [f"{market}_missing" for market in MARKET]

    print("\n=== interpolation check ===")
    print(interpolated.loc[interpolated["cash_date"].isin(check_dates), check_cols])

    basis_cols = (
        ["cash_date", "nearby"]
        + [f"{market}_basis" for market in MARKET]
        + [f"{market}_basis_pct" for market in MARKET]
    )

    print("\n=== basis ===")
    print(interpolated[basis_cols].head())
    print(interpolated[basis_cols].tail())

    stamp = pd.Timestamp.today().strftime("%Y%m%d")
    path = f"output/corn_basis_2005_{stamp}.xlsx"

    export_excel(interpolated, path)