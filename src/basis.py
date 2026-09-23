from load import load_merged
MARKET = ['kansas_city', 'dodge_city', 'garden_city']
def add_basis(df):
    for market in MARKET: 
        df[f"{market}_basis"] = df[market] - df["nearby"]
        df[f"{market}_basis_pct"] = df[f"{market}_basis"] / df["nearby"] * 100
        
    return df

if __name__ == "__main__":
    merged = load_merged("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")
    df = add_basis(merged)
    print(df.head())
    print(df.tail())

