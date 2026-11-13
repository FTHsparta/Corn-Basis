from basis import build_dataset
import numpy as np
import pandas as pd

import basis

MARKET = ["kansas_city", "dodge_city", "garden_city"]
SERIES = ["kansas_city_basis", "dodge_city_basis", "garden_city_basis", "kansas_city_basis_pct", "dodge_city_basis_pct","garden_city_basis_pct"]
HORIZON = [16, 20, 24]
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

def evaluate_all(df, years = 3, weight = 1):
    results = []
    for col in SERIES:
        market = col.split("_basis")[0] #Grabs the market name from the series name (e.g., "kansas_city" from "kansas_city_basis")
        if col.endswith("_pct"):
            basis = "pct_points"
        else: 
            basis = "absolute"
        grid = make_grid(df, col)
        forecast = rolling_forecast(grid, years)
        error = forecast_error(grid, forecast)
        n, me, mae, rmse = summary(error)
        results.append({"market":market, "basis": basis, "horizon": "plain", "n": n, "mean_error": me, "mae": mae, "rmse": rmse})

        for horizon in HORIZON: 
            Taylor_data = modern_information_forecast(df, horizon, col, weight, years)
            adjusted_error = forecast_error(grid, Taylor_data["adjusted_forecast"].unstack())
            n, me, mae, rmse = summary(adjusted_error)
            results.append({"market": market, "basis": basis, "horizon": horizon, "n": n, "mean_error": me, "mae": mae, "rmse": rmse})

            if col.endswith("_pct"):
                adjusted_cents_pct_error = adjusted_error * make_grid(df, "nearby")
                cents_n, cents_mean_error, cents_mae, cents_rmse = summary(adjusted_cents_pct_error)
                results.append({"market": market, "basis": "pct_cents", "horizon": horizon, "n": cents_n, "mean_error": cents_mean_error, "mae": cents_mae, "rmse": cents_rmse})

        if col.endswith("_pct"):
            cents_pct_error = error * make_grid(df, "nearby")

            cents_n, cents_mean_error, cents_mae, cents_rmse = summary(cents_pct_error)
            results.append({"market": market, "basis": "pct_cents", "horizon": "plain", "n": cents_n, "mean_error": cents_mean_error, "mae": cents_mae, "rmse": cents_rmse})

    return pd.DataFrame(results)

def modern_information_forecast(df, horizon, col, weight, years): #Applies Taylor's modern information forecast to the interpolated data
    detail = weekly_detail(df, col, years) #Grabs the weekly detail table which has weeks and error (what we want)
    error_table = detail[["date", "error"]] #Grabs the weeks and errors and puts it into its own table
    error_table["error"] = error_table["error"].shift(horizon) #Shifts all of the errors by the horizon amount 
    detail["adjusted_forecast"] = detail["forecast"] - (weight * error_table["error"]) #Uses the formula with the lambda (weight) to calculate the adjusted forecast
    detail["adjusted_error"] = detail["adjusted_forecast"] - detail["observed"] #Calculates the adjusted error

    return detail #returns the data

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

def optimize_lambda(df, years = 3):

    lambdas = np.linspace(0, 1, 101) #creates a list of 101 evenly spaced numbers between 0 and 1, which will be used as weights for the modern information forecast
    results = []
    nearby = make_grid(df, "nearby").stack() #creates a grid of nearby prices for each week and year
    for col in SERIES:
        for horizon in HORIZON:
            errors = []
            errors_cents = []
            for weight in lambdas:
                Taylor_data = modern_information_forecast(df, horizon, col, weight = weight, years = years)
                adjusted_error = Taylor_data["adjusted_error"].dropna() # Drops any missing values in the adjusted error series
                if col.endswith("_pct"):
                    cents_error = Taylor_data["adjusted_error"] * nearby # Calculates the adjusted error in cents for percentage basis series
                    errors_cents.append(cents_error.abs().mean()) # Calculates the mean absolute error for the adjusted error in cents and appends it to the errors_cents list
                    
                errors.append(adjusted_error.abs().mean()) # Calculates the mean absolute error for the adjusted error series and appends it to the errors list
            error_series = pd.Series(errors, index = lambdas) # Creates a pandas Series object with the errors list as values and the lambdas list as index. This allows for easy identification of the optimal lambda value that minimizes the mean absolute error.

            if col.endswith("_pct"):
                cents_series = pd.Series(errors_cents, index = lambdas) # Creates a pandas Series object with the errors_cents list as values and the lambdas list as index. This allows for easy identification of the optimal lambda value that minimizes the mean absolute error in cents.
                results.append({
                    "basis": "pct_cents",
                    "series": col,
                    "horizon": horizon,
                    "optimal lambda": cents_series.idxmin(),
                    "min mae": cents_series.min(),
                    "mae at 1": errors_cents[-1],
                    "mae at 0": errors_cents[0]
                })
            results.append({ #creates a dictionary with the market, series, horizon, optimal lambda, minimum mean absolute error, and mean absolute error at lambda = 1. This dictionary is appended to the results list.
                "basis": "absolute" if not col.endswith("_pct") else "pct_points",
                "series": col,
                "horizon": horizon,
                "optimal lambda": error_series.idxmin(),
                "min mae": error_series.min(),
                "mae at 1": errors[-1],
                "mae at 0": errors[0]
            })

    return pd.DataFrame(results)

def export_results(df, path, years = 3):
    summary_sheet = evaluate_all(df, years)
    weekly_sheet = week_all(df, years)
    measures = ["n", "mean_error", "mae", "rmse"]
    with pd.ExcelWriter(path) as writer:
        for measure in measures:
            table = summary_sheet.pivot(index = ["market", "basis"], columns = "horizon", values = measure)
            table = table[["plain", 16, 20, 24]].round(2) 
            table.columns = ["base forecast", "16-week", "20-week", "24-week"]
            table.to_excel(writer, sheet_name = measure)
        weekly_sheet.to_excel(writer, sheet_name = "weekly_detail")



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

    #error.to_excel("output/error_kc_pct.xlsx")
    stamp = pd.Timestamp.today().strftime("%Y%m%d")
    #for years in [3,4]:
        #export_results(df,f"output/corn_basis_forecast_{years}yr_{stamp}.xlsx", years)

    #print(wa.shape)
    #print(wa.loc[(2026, 36), ["nearby", "garden_city"]])
    #print(wa["date"].isna().sum())
    #print(wa.loc[(2009,1), "garden_city_basis_pct_error_cents"])
    #print(wa.loc[((2026, 36), "garden_city_basis_pct_error_cents")])
    
    #modern_information = modern_information_forecast(df, 16, "garden_city_basis", weight = 1, 3) #Calls the modern information function for garden city
    #print(summary(modern_information["adjusted_error"].unstack())) #Turns it back int oa grid with years as rows and weeks as columns. Prints the results 
    #print(modern_information.shape) #prints the shape of the adjusted forecast
    #modern_information.to_excel(f"output/modern_information_forecast_{stamp}.xlsx") #outputs it to excel



    #adjusted_results_3year = evaluate_all(df, 3, 1)
    #adjusted_results_4year = evaluate_all(df, 4, 1)
    #adjusted_results_3year.to_excel(f"output/adjusted_results_3year_{stamp}.xlsx")
    #adjusted_results_4year.to_excel(f"output/adjusted_results_4year_{stamp}.xlsx")

    #export_results(df, f"output/corn_basis_forecast_3yrs_{stamp}.xlsx", years = 3)
    #export_results(df, f"output/corn_basis_forecast_4yrs_{stamp}.xlsx", years = 4)


    optimized_lambda_3yr = optimize_lambda(df, 3)
    optimized_lambda_3yr.to_excel(f"output/optimized_lambda_3yr_{stamp}.xlsx", index = False)

    optimized_lambda_4yr = optimize_lambda(df, 4)
    optimized_lambda_4yr.to_excel(f"output/optimized_lambda_4yr_{stamp}.xlsx", index = False)