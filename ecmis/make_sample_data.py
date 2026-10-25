"""Creates data/sample_prices.csv: fictional prices and volumes with three planted unusual days.

Run:  python make_sample_data.py
The same seed always gives the same file, so results are reproducible.
"""
import numpy as np
import pandas as pd

SEED = 7
DAYS = 120
START = "2026-01-05"

# symbol: (name, starting price, typical daily volatility, typical volume)
SECURITIES = {
    "DMBK": ("Demo Bank Holdings (fictional)", 48.0, 0.010, 52_000),
    "DMCF": ("Demo Coffee Exporters (fictional)", 120.0, 0.012, 24_000),
    "DMCM": ("Demo Cement Works (fictional)", 75.0, 0.011, 38_000),
    "DMTL": ("Demo Telecom Services (fictional)", 210.0, 0.009, 30_000),
    "DMEN": ("Demo Energy Utilities (fictional)", 95.0, 0.008, 18_000),
}

# Planted unusual days: symbol -> (day number, price change, volume multiplier)
PLANTED = {
    "DMBK": (90, +0.14, 5.0),   # big price jump on heavy volume   -> "Price + volume"
    "DMCF": (100, 0.0, 6.0),    # heavy volume, normal price       -> "Volume spike"
    "DMTL": (80, -0.09, 1.0),   # big price drop, normal volume    -> "Price move"
}


def make_prices() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dates = pd.bdate_range(START, periods=DAYS)
    rows = []
    for symbol, (name, price, vol, base_volume) in SECURITIES.items():
        for day, date in enumerate(dates):
            change = rng.normal(0, vol)
            volume = base_volume * np.exp(rng.normal(0, 0.15))
            if symbol in PLANTED and PLANTED[symbol][0] == day:
                _, change, multiplier = PLANTED[symbol]
                volume = base_volume * multiplier
            price = price * (1 + change)
            rows.append((date.strftime("%Y-%m-%d"), symbol, name, round(price, 2), int(volume)))
    return pd.DataFrame(rows, columns=["date", "symbol", "name", "close", "volume"])


if __name__ == "__main__":
    make_prices().to_csv("data/sample_prices.csv", index=False)
    print("Wrote data/sample_prices.csv")
