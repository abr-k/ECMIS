"""Checks for the three rules, using small hand-made data so the expected answer is obvious."""
import numpy as np
import pandas as pd

from src import detection
from src.data import load_prices
from src.detection import find_alerts


def make_prices(closes, volumes, symbol="AAA"):
    return pd.DataFrame({"date": pd.bdate_range("2026-01-05", periods=len(closes)), "symbol": symbol,
                         "name": symbol, "close": closes, "volume": volumes})


def calm(n=40):
    """Prices that rise 1% a day and a steady volume: nothing unusual."""
    return list(100 * 1.01 ** np.arange(n)), [1000.0] * n


def test_calm_market_raises_no_alerts():
    closes, volumes = calm()
    assert find_alerts(make_prices(closes, volumes)).empty


def test_price_move_alone():
    closes, volumes = calm()
    closes[30:] = [c * 1.10 for c in closes[30:]]  # +10% on top of the usual +1% on day 30
    alerts = find_alerts(make_prices(closes, volumes))
    assert list(alerts["rule"]) == ["Price move"]
    assert alerts.iloc[0]["date"] == pd.bdate_range("2026-01-05", periods=40)[30]
    assert "rose 11.1%" in alerts.iloc[0]["explanation"]


def test_volume_spike_alone():
    closes, volumes = calm()
    volumes[30] = 5000
    alerts = find_alerts(make_prices(closes, volumes))
    assert list(alerts["rule"]) == ["Volume spike"] and alerts.iloc[0]["volume_ratio"] == 5.0


def test_price_and_volume_together_is_one_high_alert():
    closes, volumes = calm()
    closes[30:] = [c * 0.90 for c in closes[30:]]
    volumes[30] = 5000
    alerts = find_alerts(make_prices(closes, volumes))
    assert list(alerts["rule"]) == ["Price + volume"] and list(alerts["priority"]) == ["High"]
    assert "fell 9.1%" in alerts.iloc[0]["explanation"]


def test_single_rule_priority_is_medium_only_when_clearly_above_the_limit():
    closes, volumes = calm()
    volumes[20], volumes[30] = 3500, 6000  # 3.5x (just over 3x) and 6x (over 1.5 * 3x)
    alerts = find_alerts(make_prices(closes, volumes)).set_index("date")
    dates = pd.bdate_range("2026-01-05", periods=40)
    assert alerts.loc[dates[20], "priority"] == "Low" and alerts.loc[dates[30], "priority"] == "Medium"


def test_baseline_ignores_the_future():
    """Changing days AFTER day 30 must not change what is decided about day 30 (no look-ahead)."""
    closes, volumes = calm()
    volumes[30] = 5000
    before = find_alerts(make_prices(closes, volumes))
    volumes2 = list(volumes)
    volumes2[31:] = [900_000.0] * 9
    after = find_alerts(make_prices(closes, volumes2))
    day30 = pd.bdate_range("2026-01-05", periods=40)[30]
    assert before[before["date"] == day30].iloc[0]["volume_ratio"] == after[after["date"] == day30].iloc[0]["volume_ratio"]


def test_too_little_history_means_no_alert():
    closes, volumes = calm(8)
    volumes[7] = 100_000
    assert find_alerts(make_prices(closes, volumes)).empty


def test_zero_baseline_does_not_crash_or_alert():
    alerts = find_alerts(make_prices([10.0] * 30, [0.0] * 30))  # flat price and zero volume: baselines are 0
    assert alerts.empty


def test_securities_are_judged_separately():
    closes, volumes = calm()
    volumes_spiky = list(volumes)
    volumes_spiky[30] = 5000
    both = pd.concat([make_prices(closes, volumes, "AAA"), make_prices(closes, volumes_spiky, "BBB")])
    alerts = find_alerts(both)
    assert list(alerts["symbol"]) == ["BBB"]


def test_results_are_reproducible_and_thresholds_can_be_changed(monkeypatch):
    prices, _ = load_prices("data/sample_prices.csv")
    first, second = find_alerts(prices), find_alerts(prices)
    pd.testing.assert_frame_equal(first, second)
    monkeypatch.setattr(detection, "VOLUME_MULTIPLE", 100.0)
    assert "Volume spike" not in set(find_alerts(prices)["rule"])


def test_sample_data_alerts_match_the_three_planted_events():
    prices, _ = load_prices("data/sample_prices.csv")
    alerts = find_alerts(prices)
    planted = alerts[alerts["symbol"].isin(["DMBK", "DMCF", "DMTL"]) & (alerts["priority"] != "Low")]
    assert sorted(zip(planted["symbol"], planted["rule"])) == [
        ("DMBK", "Price + volume"), ("DMCF", "Volume spike"), ("DMTL", "Price move")]
