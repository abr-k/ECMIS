"""ECMIS - the Streamlit app. Run with:  streamlit run app.py

This file only draws the pages. The real work happens in src/:
  src/data.py       loads and checks the CSV
  src/detection.py  finds the alerts (three simple rules)
  src/storage.py    saves alert status and notes (SQLite)
  src/charts.py     builds the charts
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from src import DISCLAIMER, SYNTHETIC_NOTICE, charts
from src.data import DataError, load_prices
from src.detection import MIN_PRICE_MOVE_PCT, PRICE_MULTIPLE, VOLUME_MULTIPLE, WINDOW_DAYS, add_indicators, find_alerts
from src.storage import STATUSES, load_reviews, save_review

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_prices.csv"
PAGES = ["Dashboard", "Market Analysis", "Alerts"]


def get_data():
    """Prices from the uploaded CSV if there is one, otherwise the fictional sample file."""
    uploaded = st.sidebar.file_uploader("Use your own CSV (optional)", type=["csv"])
    st.sidebar.caption("Columns: date, symbol, close, volume (name is optional).")
    if uploaded is not None:
        try:
            prices, warnings = load_prices(uploaded)
            for message in warnings:
                st.sidebar.warning(message)
            return prices, f"Uploaded file: {uploaded.name}", False
        except DataError as exc:
            st.sidebar.error(f"{exc} Showing the sample data instead.")
    prices, _ = load_prices(SAMPLE_CSV)
    return prices, "Fictional sample data", True


def alerts_with_reviews(alerts: pd.DataFrame) -> pd.DataFrame:
    """Add the saved status and note to each alert (alerts nobody has reviewed are 'New')."""
    reviews = load_reviews()
    alerts = alerts.copy()
    alerts["status"] = alerts["alert_id"].map(lambda a: reviews.get(a, {}).get("status", "New"))
    alerts["note"] = alerts["alert_id"].map(lambda a: reviews.get(a, {}).get("note", ""))
    return alerts


def alert_table(alerts: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": alerts["date"].dt.strftime("%Y-%m-%d"), "Security": alerts["symbol"], "Alert": alerts["rule"],
        "Priority": alerts["priority"], "Price change %": alerts["price_change_pct"].round(1),
        "Volume vs average": alerts["volume_ratio"].round(1).astype(str) + "x", "Status": alerts["status"]})


# ------------------------------------------------------------------------------ pages
def dashboard(prices, alerts):
    latest_date = prices["date"].max()
    open_alerts = int((alerts["status"] != "Closed").sum())
    a, b, c, d = st.columns(4)
    a.metric("Securities", prices["symbol"].nunique())
    b.metric("Latest data", f"{latest_date:%Y-%m-%d}")
    c.metric("Alerts", len(alerts))
    d.metric("Not yet closed", open_alerts)

    st.subheader("Latest prices")
    indicators = add_indicators(prices)
    latest = indicators.sort_values("date").groupby("symbol").tail(1).sort_values("symbol")
    st.dataframe(pd.DataFrame({
        "Security": latest["symbol"], "Name": latest["name"], "Close": latest["close"].round(2),
        "Change today %": latest["price_change_pct"].round(2), "Volume": latest["volume"].astype(int)}),
        hide_index=True)

    st.plotly_chart(charts.compare_prices_chart(prices), key="compare_prices")
    st.subheader("Newest alerts")
    if alerts.empty:
        st.info("No alerts were generated for this data.")
    else:
        st.dataframe(alert_table(alerts.head(5)), hide_index=True)
        st.caption("Open the Alerts page to read the explanations and record your review.")


def market_analysis(prices, alerts):
    symbol = st.selectbox("Security", sorted(prices["symbol"].unique()))
    one = add_indicators(prices[prices["symbol"] == symbol]).sort_values("date")
    st.plotly_chart(charts.price_chart(one, alerts[alerts["symbol"] == symbol]), key="price")
    st.plotly_chart(charts.volume_chart(one), key="volume")
    st.subheader("Recent days")
    recent = one.sort_values("date", ascending=False).head(15)
    st.dataframe(pd.DataFrame({
        "Date": recent["date"].dt.strftime("%Y-%m-%d"), "Close": recent["close"].round(2),
        "Change %": recent["price_change_pct"].round(2), "Volume": recent["volume"].astype(int),
        "Volume vs average": recent["volume_ratio"].round(2)}), hide_index=True)
    st.caption("The first days of a security have no 'average of earlier days' yet, so they are left blank.")


def alerts_page(alerts):
    st.caption(f"Rules (edit them in src/detection.py): price move >= {PRICE_MULTIPLE:g}x the typical daily move "
               f"and >= {MIN_PRICE_MOVE_PCT:g}%; volume >= {VOLUME_MULTIPLE:g}x the average; both on one day = High. "
               f"'Recent days' means the previous {WINDOW_DAYS} trading days.")
    if alerts.empty:
        st.info("No alerts were generated for this data.")
        return

    f1, f2, f3 = st.columns(3)
    status = f1.selectbox("Status", ["All"] + STATUSES)
    priority = f2.selectbox("Priority", ["All", "High", "Medium", "Low"])
    symbol = f3.selectbox("Security", ["All"] + sorted(alerts["symbol"].unique()))
    shown = alerts
    if status != "All":
        shown = shown[shown["status"] == status]
    if priority != "All":
        shown = shown[shown["priority"] == priority]
    if symbol != "All":
        shown = shown[shown["symbol"] == symbol]
    if shown.empty:
        st.info("No alert matches these filters.")
        return
    st.dataframe(alert_table(shown), hide_index=True)

    st.subheader("Review an alert")
    labels = {r.alert_id: f"{r.date:%Y-%m-%d}  {r.symbol}  {r.rule}  ({r.priority}, {r.status})" for r in shown.itertuples()}
    chosen = st.selectbox("Choose an alert", list(labels), format_func=labels.get)
    row = shown[shown["alert_id"] == chosen].iloc[0]

    st.markdown("**Why this alert appeared**")
    st.write(row["explanation"])
    st.markdown(f"**Values:** price change {row['price_change_pct']:+.1f}% (typical {row['typical_move_pct']:.1f}%), "
                f"volume {row['volume']:,.0f} (average {row['avg_volume']:,.0f}, {row['volume_ratio']:.1f}x).")

    new_status = st.selectbox("Status of this alert", STATUSES, index=STATUSES.index(row["status"]),
                              key=f"status_{chosen}")
    note = st.text_area("Note (optional)", value=row["note"], max_chars=1000, key=f"note_{chosen}")
    if st.button("Save review"):
        save_review(chosen, new_status, note)
        st.session_state["saved"] = f"Saved: {chosen} is now '{new_status}'."
        st.rerun()


# ------------------------------------------------------------------------------ main
def main():
    st.set_page_config(page_title="ECMIS prototype", layout="wide")
    st.sidebar.title("ECMIS")
    page = st.sidebar.radio("Page", PAGES)
    prices, source_label, is_sample = get_data()

    st.title(page)
    st.warning(DISCLAIMER)
    st.caption(f"Data: {source_label} | {prices['date'].min():%Y-%m-%d} to {prices['date'].max():%Y-%m-%d}"
               + (f" | {SYNTHETIC_NOTICE}" if is_sample else ""))
    if "saved" in st.session_state:
        st.success(st.session_state.pop("saved"))

    alerts = alerts_with_reviews(find_alerts(prices))
    if page == "Dashboard":
        dashboard(prices, alerts)
    elif page == "Market Analysis":
        market_analysis(prices, alerts)
    else:
        alerts_page(alerts)


main()
