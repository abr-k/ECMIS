"""Checks for loading and cleaning the price CSV."""
import io

import pytest

from src.data import DataError, load_prices

GOOD = "date,symbol,close,volume\n2026-01-05,AAA,10,100\n2026-01-06,AAA,11,120\n"


def load(text):
    return load_prices(io.StringIO(text))


def test_sample_file_loads_cleanly():
    prices, warnings = load_prices("data/sample_prices.csv")
    assert warnings == []
    assert prices["symbol"].nunique() == 5 and len(prices) == 600
    assert (prices["close"] > 0).all()


def test_valid_csv_and_optional_name_column():
    prices, warnings = load(GOOD)
    assert warnings == [] and list(prices["name"]) == ["AAA", "AAA"]  # name falls back to the symbol


def test_column_names_are_case_insensitive():
    prices, _ = load("Date, Symbol ,CLOSE,Volume\n2026-01-05,aaa,10,100\n")
    assert prices.iloc[0]["symbol"] == "AAA"


def test_missing_required_column_is_refused_with_a_clear_message():
    with pytest.raises(DataError, match="volume"):
        load("date,symbol,close\n2026-01-05,AAA,10\n")


def test_bad_rows_are_dropped_and_reported():
    text = GOOD + "not-a-date,AAA,12,100\n2026-01-07,AAA,abc,100\n2026-01-08,AAA,-5,100\n2026-01-09,AAA,,100\n2026-01-12,,5,100\n"
    prices, warnings = load(text)
    assert len(prices) == 2
    assert "Dropped 5 row(s)" in warnings[0]


def test_duplicates_keep_the_last_row():
    prices, warnings = load(GOOD + "2026-01-06,AAA,99,1\n")
    assert len(prices) == 2 and prices.iloc[1]["close"] == 99 and "duplicate" in warnings[0]


@pytest.mark.parametrize("text", ["", "date,symbol,close,volume\n", "date,symbol,close,volume\nx,y,z,w\n"])
def test_files_with_no_usable_rows_are_refused(text):
    with pytest.raises(DataError):
        load(text)


def test_binary_junk_is_refused():
    with pytest.raises(DataError):
        load_prices(io.BytesIO(bytes(range(256)) * 10))
