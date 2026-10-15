from basis import build_dataset
from forecast import make_grid, rolling_forecast, forecast_error
import pandas as pd, numpy as np, matplotlib.pyplot as plt
import numpy as np

def plot_prices(df, path):
    fig, ax = plt.subplots(figsize = (10,5))
    ax.plot(df["cash_date"], df[["kansas_city", "dodge_city", "garden_city", "nearby"]], label = ["Kansas City", "Dodge City", "Garden City", "Nearby"])
    ax.set_title("Weekly corn cash and nearby futures prices")
    ax.set_xlabel("Date")
    ax.set_ylabel("$/bu")
    ax.legend()
    ax.grid(alpha = .3)
    fig.tight_layout()
    fig.savefig(path, dpi = 300)
    plt.close(fig)

def plot_basis(df, path):
    fig, ax = plt.subplots(figsize = (10,5))
    ax.plot(df["cash_date"], df[["kansas_city_basis", "dodge_city_basis", "garden_city_basis"]], label = ["Kansas City", "Dodge City", "Garden City"])
    ax.set_title("Weekly corn basis")
    ax.set_xlabel("Date")
    ax.set_ylabel("cents/bu")
    ax.legend()
    ax.axhline(0, color = "black", linewidth = 0.8)
    ax.grid(alpha = .3)
    fig.tight_layout()
    fig.savefig(path, dpi = 300)
    plt.close(fig)
    
def plot_errors_year(df, year, path):
    fig, ax = plt.subplots(figsize = (10,5))
    grid = make_grid(df, "garden_city_basis")
    error3 = forecast_error(grid, rolling_forecast(grid, 3))   
    error4 = forecast_error(grid, rolling_forecast(grid, 4))  
    row3 = error3.loc[year]                                   
    row4 = error4.loc[year]
    ax.plot(row3.index, row3.values, marker = "o", label = "3-yr MA")   
    ax.plot(row4.index, row4.values, marker = "o", label = "4-yr MA")
    ax.axhline(0, color = "black", linewidth = 0.8)
    ax.set_title(f"Garden City basis forecast errors, {year}")
    ax.set_xlabel("ISO week")
    ax.set_ylabel("Forecast error (cents/bu)")
    ax.legend()
    ax.grid(alpha = .3)
    fig.tight_layout()
    fig.savefig(path, dpi = 300)
    plt.close(fig)

def plot_errors_scatter(df, path):
    fig, ax = plt.subplots(figsize = (10,5))
    grid = make_grid(df, "garden_city_basis")
    error3 = forecast_error(grid, rolling_forecast(grid, 3))
    years = range(2015, 2026)
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
    for year, color in zip(years, colors):
        row = error3.loc[year]
        ax.scatter(row.index, row.values, color = color, s = 15, label = year)
    ax.axhline(0, color = "black", linewidth = 0.8)
    ax.set_xticks(range(1, 53, 4))
    ax.set_xlabel("ISO week")
    ax.set_ylabel("Error (cents/bu)")
    ax.legend(title = "Year", loc = "upper left", bbox_to_anchor = (1.01, 1))
    fig.tight_layout()
    fig.savefig(path, dpi = 200)
    plt.close(fig)

if __name__ == "__main__":
    df = build_dataset("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")
    plot_prices(df, "output/prices.png")
    plot_basis(df, "output/basis.png")
    print(df.loc[df["cash_date"] == "2026-09-03", ["kansas_city_basis", "nearby", "kansas_city_basis_pct"]])
    plot_errors_year(df, 2025, f"output/gc_errors_scatter.png")
    plot_errors_scatter(df, f"output/gc_errors_scatter.png")
    ##print(f"{df.loc[df['cash_date'] == '2009-03-12']}")
    ##print(f"{df.loc[df['cash_date'] == '2016-05-19']}")
    ##print(f"{df.loc[df['cash_date'] == '2015-03-05']}")
    ##print(f"{df.loc[df['cash_date'] == '2011-03-12']}")

    ##cols = ["cash_date", "kansas_city", "dodge_city", "garden_city", "nearby"]
    ##print(df.loc[df["cash_date"].between("2009-11-26", "2009-12-10"), cols])  