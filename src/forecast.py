from basis import build_dataset
import numpy as np
import pandas as pd

MARKET = ["kansas_city", "dodge_city", "garden_city"]
SERIES = ["kansas_city_basis", "dodge_city_basis", "garden_city_basis", "kansas_city_basis_pct", "dodge_city_basis_pct","garden_city_basis_pct"]

def make_grid(df, col): #creates a dataset named grid that has one row per isoyear and one column per isoweek
    df = df.copy()
    df[["iso_year", "iso_week"]] = df["cash_date"].dt.isocalendar()[["year", "week"]].astype(int)
    grid = df.pivot(index = "iso_year", columns = "iso_week", values = col)
    return grid

def rolling_forecast(grid, years = 3):
    forecast = grid.shift(1).rolling(years).mean()
    forecast = forecast.loc[2009:]
    return forecast

def forecast_error(grid, forecast):
    error = (forecast - grid).loc[2009:]
    return error

def summary(error):
    error = error.stack().dropna()
    mean_error = error.mean()
    mae = error.abs().mean()
    rmse = (error ** 2).mean() ** 0.5
    n = len(error)

    return n, mean_error, mae, rmse
def weekly_detail(df, col, years = 3):
    grid = make_grid(df, col)
    forecast = rolling_forecast(grid, years)
    error = forecast_error(grid, forecast)
    dates = make_grid(df, "cash_date")
    detail = pd.DataFrame({"date": dates.stack(), "observed": grid.stack(), "forecast": forecast.stack(), "error": error.stack()})
    detail = detail.dropna(subset=["date"])
    return detail.loc[2009:]

def evaluate_all(df, years = 3):
    results = []
    for col in SERIES:
        grid = make_grid(df, col)
        forecast = rolling_forecast(grid, years)
        error = forecast_error(grid, forecast)
        n, me, mae, rmse = summary(error)
        results.append({"series": col, "n": n, "mean_error": me, "mae": mae, "rmse": rmse})
    return pd.DataFrame(results)

def week_all(df, years = 3):
    tables = []
    for col in SERIES:
        table = weekly_detail(df, col, years).drop(columns = "date").add_prefix(col + "_")
        tables.append(table)
    dates = weekly_detail(df, SERIES[0], years)[["date"]]

    

    prices = {"nearby": make_grid(df, "nearby")}
    for col in MARKET: 
        prices[col] = make_grid(df, col)

    
    all_markets = pd.concat(prices, axis = 1).stack()
    all_markets = all_markets.loc[2009:]
    all_markets = all_markets.dropna(how = "all")


    results = pd.concat([dates] + [all_markets] + tables, axis = 1)
    for market in MARKET:
        results[f"{market}_basis_pct_error_cents"] = results[f"{market}_basis_pct_error"] * results["nearby"]

    return results


def export_results(df, path, years = 3):
    summary_sheet = evaluate_all(df, years)
    weekly_sheet = week_all(df, years)
    with pd.ExcelWriter(path) as writer:
        summary_sheet.to_excel(writer, sheet_name = "summary", index = False)
        weekly_sheet.to_excel(writer, sheet_name = "weekly")

if __name__ == "__main__":
    df = build_dataset("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")
    grid = make_grid(df, "kansas_city_basis_pct")
    #print(grid.shape)
    #print(grid.loc[2023:2026, 35:37])

    forecast = rolling_forecast(grid)
    #print(forecast.shape)
    #print(forecast.loc[2024:2026, 35:37])
    #print(forecast[53].notna().sum())

    error = forecast_error(grid, forecast)
    #print(error.loc[2024:2026, 35:37])

    n, me, mae, rmse = summary(error)
    #print(n, me, mae, rmse)

    #print(evaluate_all(df, 3))
    #(evaluate_all(df, 4))

    forecast4 = rolling_forecast(grid, 4)
    #print(grid.loc[2022:2025, 36], forecast4.loc[2026,36])

    wd = weekly_detail(df, "kansas_city_basis_pct")
    #print(wd.shape)
    #print(wd.loc[(2026, 36)])

    wa = week_all(df)
    #print(wa.shape)
    #print(wa.columns.tolist())

    error.to_excel("output/error_kc_pct.xlsx")
    stamp = pd.Timestamp.today().strftime("%Y%m%d")
    for years in [3,4]:
        export_results(df,f"output/corn_basis_forecast_{years}yr_{stamp}.xlsx", years)

    print(wa.shape)
    print(wa.loc[(2026, 36), ["nearby", "garden_city"]])
    #print(wa["date"].isna().sum())
    print(wa.loc[(2009,1), "garden_city_basis_pct_error_cents"])
    print(wa.loc[((2026, 36), "garden_city_basis_pct_error_cents")])
    

