"""Loading and checking the price CSV.

Required columns- date, symbol, close, volume.   Optional column- name.
Bad rows are dropped and reported as warnings; a file with no usable rows raises DataError.
"""
import pandas as pd

REQUIRED_COLUMNS = ["date", "symbol", "close", "volume"]


class DataError(ValueError):
    """The file cannot be used at all."""


def load_prices(source) -> tuple[pd.DataFrame, list[str]]:
    """Read a CSV (file path or uploaded file) -> (clean table sorted by symbol and date, warnings)."""
    try:
        df = pd.read_csv(source)
    except Exception as exc:  # empty file, binary junk, wrong encoding ...
        raise DataError(f"The file could not be read as a CSV ({type(exc).__name__}).") from exc

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataError(f"Missing required column(s): {', '.join(missing)}. Expected: {', '.join(REQUIRED_COLUMNS)}.")
    if "name" not in df.columns:
        df["name"] = df["symbol"]

    warnings = []
    start_rows = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df["symbol"] = df["symbol"].astype("string").str.strip().str.upper()

    valid = df["date"].notna() & df["symbol"].notna() & (df["symbol"] != "") & (df["close"] > 0) & (df["volume"] >= 0)
    if not valid.all():
        warnings.append(f"Dropped {int((~valid).sum())} row(s) with a missing or invalid date, symbol, close or volume.")
    df = df[valid]

    before = len(df)
    df = df.drop_duplicates(subset=["symbol", "date"], keep="last")
    if len(df) < before:
        warnings.append(f"Dropped {before - len(df)} duplicate row(s) (same symbol and date); the last one was kept.")

    if df.empty:
        raise DataError(f"No usable rows were found in the {start_rows} row(s) of the file.")

    df = df[["date", "symbol", "name", "close", "volume"]].copy()
    df["symbol"] = df["symbol"].astype(str)
    df["name"] = df["name"].astype(str)
    df["volume"] = df["volume"].astype(float)
    return df.sort_values(["symbol", "date"]).reset_index(drop=True), warnings
