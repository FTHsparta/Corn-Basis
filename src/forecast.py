from basis import build_dataset
import numpy as np
import pandas as pd

SERIES = ["kansas_city_basis", "dodge_city_basis", "garden_city_basis", "kansas_city_basis_pct", "dodge_city_basis_pct","garden_city_basis_pct"]

def make_grid(df, col): #creates a dataset named grid that has one row per isoyear and one column per isoweek
    df = df.copy()
    df[["iso_year", "iso_week"]] = df["cash_date"].dt.isocalendar()[["year", "week"]].astype(int)
    grid = df.pivot(index = "iso_year", columns = "iso_week", values = col)
    return grid

def rolling_forecast(grid):
    forecast = grid.shift(1).rolling(3).mean()
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
def weekly_detail(df, col):
    grid = make_grid(df, col)
    forecast = rolling_forecast(grid)
    error = forecast_error(grid, forecast)
    dates = make_grid(df, "cash_date")
    detail = pd.DataFrame({"date": dates.stack(), "observed": grid.stack(), "forecast": forecast.stack(), "error": error.stack()})
    detail = detail.dropna(subset=["date"])
    return detail.loc[2009:]

def evaluate_all(df):
    results = []
    for col in SERIES:
        grid = make_grid(df, col)
        forecast = rolling_forecast(grid)
        error = forecast_error(grid, forecast)
        n, me, mae, rmse = summary(error)
        results.append({"series": col, "n": n, "mean_error": me, "mae": mae, "rmse": rmse})
    return pd.DataFrame(results)

def week_all(df):
    tables = []
    for col in SERIES:
        table = weekly_detail(df, col).drop(columns = "date").add_prefix(col + "_")
        tables.append(table)
    dates = weekly_detail(df, SERIES[0])[["date"]]
    return pd.concat([dates] + tables, axis = 1)

def export_results(df, path):
    summary_sheet = evaluate_all(df)
    weekly_sheet = week_all(df)
    with pd.ExcelWriter(path) as writer:
        summary_sheet.to_excel(writer, sheet_name = "summary", index = False)
        weekly_sheet.to_excel(writer, sheet_name = "weekly")

if __name__ == "__main__":
    df = build_dataset("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")
    grid = make_grid(df, "kansas_city_basis_pct")
    print(grid.shape)
    print(grid.loc[2023:2026, 35:37])

    forecast = rolling_forecast(grid)
    print(forecast.shape)
    print(forecast.loc[2024:2026, 35:37])
    print(forecast[53].notna().sum())

    error = forecast_error(grid, forecast)
    print(error.loc[2024:2026, 35:37])

    n, me, mae, rmse = summary(error)
    print(n, me, mae, rmse)

    print(evaluate_all(df))

    wd = weekly_detail(df, "kansas_city_basis_pct")
    print(wd.shape)
    print(wd.loc[(2026, 36)])

    wa = week_all(df)
    print(wa.shape)
    print(wa.columns.tolist())

    error.to_excel("error_kc_pct.xlsx")
    export_results(df, "corn_basis_forecast_3yr_20261001.xlsx")