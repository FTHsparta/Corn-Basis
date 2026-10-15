from basis import build_dataset
import pandas as pd, numpy as np, matplotlib.pyplot as plt

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


if __name__ == "__main__":
    df = build_dataset("data/raw/Grainpr.xlsx", "data/raw/cornfutures.xlsx")
    plot_prices(df, "output/prices.png")
