from basis import build_dataset

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

    error.to_excel("error_kc_pct.xlsx")