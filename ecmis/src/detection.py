"""The three detection rules. Change the numbers below to make the rules stricter or looser.

How a day is judged: it is compared only with the days BEFORE it (the "recent days" window),
never with later days, so the check could have been run live on that day.

  Rule 1  Price move    : today's price change is at least PRICE_MULTIPLE times the recent typical
                         daily move, and at least MIN_PRICE_MOVE_PCT percent.
  Rule 2  Volume spike  : today's volume is at least VOLUME_MULTIPLE times the recent average volume.
  Rule 3  Price + volume: rules 1 and 2 on the same day (replaces the two single alerts).
"""
import pandas as pd

# --- Settings that can be changed for better analysis
WINDOW_DAYS = 20         # how many earlier trading days make up "recent days"
MIN_HISTORY_DAYS = 10    # need at least this many earlier days before a security can raise alerts
PRICE_MULTIPLE = 3.0     # price move must be this many times the recent typical move ...
MIN_PRICE_MOVE_PCT = 3.0 # ... and at least this many percent (ignores tiny moves in calm periods)
VOLUME_MULTIPLE = 3.0    # volume must be this many times the recent average
STRONG_FACTOR = 1.5      # a single-rule alert is "Medium" instead of "Low" if it beats its limit by this factor
# ---

ALERT_COLUMNS = ["alert_id", "date", "symbol", "rule", "priority", "price_change_pct", "typical_move_pct",
                 "volume", "avg_volume", "volume_ratio", "explanation"]


def add_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Add price change %, typical move and average volume. Baselines use earlier days only (shift(1))."""
    df = prices.sort_values(["symbol", "date"]).copy()
    by_symbol = df.groupby("symbol", group_keys=False)
    df["price_change_pct"] = by_symbol["close"].pct_change() * 100
    abs_change = df["price_change_pct"].abs()

    def earlier_mean(series: pd.Series) -> pd.Series:
        # shift(1): the baseline for day t is built from days before t, so no future data leaks in
        return series.groupby(df["symbol"]).transform(
            lambda s: s.shift(1).rolling(WINDOW_DAYS, min_periods=MIN_HISTORY_DAYS).mean())

    df["typical_move_pct"] = earlier_mean(abs_change)
    df["avg_volume"] = earlier_mean(df["volume"])
    # NaN (not infinity) when a baseline is zero or missing, so such days simply cannot trigger a rule
    df["price_ratio"] = abs_change / df["typical_move_pct"].where(df["typical_move_pct"] > 0)
    df["volume_ratio"] = df["volume"] / df["avg_volume"].where(df["avg_volume"] > 0)
    return df.reset_index(drop=True)


def find_alerts(prices: pd.DataFrame) -> pd.DataFrame:
    """Return one row per alert, newest first. Same input and settings always give the same alerts."""
    df = add_indicators(prices)
    price_hit = (df["price_ratio"] >= PRICE_MULTIPLE) & (df["price_change_pct"].abs() >= MIN_PRICE_MOVE_PCT)
    volume_hit = df["volume_ratio"] >= VOLUME_MULTIPLE

    alerts = []
    for row, p_hit, v_hit in zip(df.itertuples(index=False), price_hit, volume_hit):
        if not (p_hit or v_hit):
            continue
        rule = "Price + volume" if (p_hit and v_hit) else ("Price move" if p_hit else "Volume spike")
        if p_hit and v_hit:
            priority = "High"
        else:
            strong = (p_hit and row.price_ratio >= STRONG_FACTOR * PRICE_MULTIPLE) or \
                     (v_hit and row.volume_ratio >= STRONG_FACTOR * VOLUME_MULTIPLE)
            priority = "Medium" if strong else "Low"
        alerts.append({
            "alert_id": f"{row.symbol}-{row.date:%Y%m%d}",
            "date": row.date, "symbol": row.symbol, "rule": rule, "priority": priority,
            "price_change_pct": row.price_change_pct, "typical_move_pct": row.typical_move_pct,
            "volume": row.volume, "avg_volume": row.avg_volume, "volume_ratio": row.volume_ratio,
            "explanation": explain(row, rule),
        })
    result = pd.DataFrame(alerts, columns=ALERT_COLUMNS)
    return result.sort_values(["date", "symbol"], ascending=[False, True]).reset_index(drop=True)


def explain(row, rule: str) -> str:
    """Plain-language reason for an alert."""
    direction = "rose" if row.price_change_pct > 0 else "fell"
    price_text = (f"{row.symbol} {direction} {abs(row.price_change_pct):.1f}% on {row.date:%Y-%m-%d}. In the "
                  f"previous {WINDOW_DAYS} trading days its typical daily move was {row.typical_move_pct:.1f}%, so this "
                  f"move is {row.price_ratio:.1f} times larger (the rule asks for at least {PRICE_MULTIPLE:g} times "
                  f"and at least {MIN_PRICE_MOVE_PCT:g}%).")
    volume_text = (f"{row.symbol} traded {row.volume:,.0f} shares on {row.date:%Y-%m-%d}, which is "
                   f"{row.volume_ratio:.1f} times its average of {row.avg_volume:,.0f} over the previous "
                   f"{WINDOW_DAYS} trading days (the rule asks for at least {VOLUME_MULTIPLE:g} times).")
    if rule == "Price move":
        text = price_text
    elif rule == "Volume spike":
        text = volume_text
    else:
        text = price_text + " On the same day, " + volume_text[volume_text.index("traded"):]
    return text + " This is a prompt for a human to look closer, not proof of anything wrong."
