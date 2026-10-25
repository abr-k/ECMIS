"""Small Plotly charts used by the app."""
import pandas as pd
import plotly.graph_objects as go

NAVY, TEAL, RED = "#0B1F3A", "#0E7C86", "#B42318"


def _style(fig: go.Figure, title: str, height: int = 340) -> go.Figure:
    fig.update_layout(title=title, height=height, template="plotly_white", margin=dict(l=40, r=20, t=50, b=30),
                      hovermode="x unified", legend=dict(orientation="h"))
    return fig


def compare_prices_chart(prices: pd.DataFrame) -> go.Figure:
    """Every security's price, rebased to 100 on its first day so they can share one chart."""
    fig = go.Figure()
    for symbol, g in prices.groupby("symbol"):
        g = g.sort_values("date")
        fig.add_trace(go.Scatter(x=g["date"], y=g["close"] / g["close"].iloc[0] * 100, mode="lines", name=symbol))
    return _style(fig, "Prices compared (first day = 100)")


def price_chart(one: pd.DataFrame, alerts: pd.DataFrame) -> go.Figure:
    """Closing price for one security; red diamonds mark alert days."""
    fig = go.Figure(go.Scatter(x=one["date"], y=one["close"], mode="lines", name="Close", line=dict(color=NAVY)))
    marks = one[one["date"].isin(alerts["date"])]
    if len(marks):
        fig.add_trace(go.Scatter(x=marks["date"], y=marks["close"], mode="markers", name="Alert day",
                                 marker=dict(color=RED, size=11, symbol="diamond")))
    return _style(fig, "Closing price")


def volume_chart(one: pd.DataFrame) -> go.Figure:
    """Daily volume with the average of the earlier days, which is what the volume rule compares with."""
    fig = go.Figure(go.Bar(x=one["date"], y=one["volume"], name="Volume", marker=dict(color=TEAL)))
    fig.add_trace(go.Scatter(x=one["date"], y=one["avg_volume"], mode="lines", name="Average of earlier days",
                             line=dict(color=NAVY, dash="dash")))
    return _style(fig, "Trading volume")
