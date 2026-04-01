"""
Streamlit UI for the year-end rebalanced SPY / SHV / VIXY backtest.

Run from the project directory:
  streamlit run streamlit_app.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import backtester as bt

st.set_page_config(page_title="Portfolio backtest", layout="wide")
st.title("Year-end rebalanced portfolios")
st.caption(
    f"Data: {bt.START} → {bt.END} (yfinance; Adj Close when provided, else Close). "
    f"Rebalance on the last trading day of each calendar year. "
    f"Starting capital ${bt.INITIAL:,.0f}."
)


@st.cache_data(ttl=86_400, show_spinner="Loading market data…")
def load_prices_cached(start: str, end: str) -> pd.DataFrame:
    return bt.load_prices(start, end)


with st.sidebar:
    st.header("Benchmark")
    spy_bench_pct = st.slider("SPY %", 0, 100, 60, 1, key="bench_spy")
    shv_bench_pct = 100 - spy_bench_pct
    st.metric("SHV % (remainder)", f"{shv_bench_pct}%")

    st.divider()
    st.header("Barbell")
    spy_bar_pct = st.slider("SPY %", 0, 100, 5, 1, key="bar_spy")
    vixy_max = max(0, 100 - spy_bar_pct)
    if "vixy_bar" in st.session_state:
        st.session_state.vixy_bar = int(min(st.session_state.vixy_bar, vixy_max))
    vixy_bar_pct = st.slider(
        "VIXY %",
        0,
        vixy_max,
        min(5, vixy_max),
        1,
        key="vixy_bar",
        help="ProShares VIX Short-Term Futures ETF",
    )
    shv_bar_pct = 100 - spy_bar_pct - vixy_bar_pct
    st.metric("SHV % (remainder)", f"{shv_bar_pct}%")

prices = load_prices_cached(bt.START, bt.END)
if prices.empty:
    st.error("No overlapping price data.")
    st.stop()

w_bench = {"SPY": spy_bench_pct / 100.0, "SHV": shv_bench_pct / 100.0}
w_barbell = {
    "SPY": spy_bar_pct / 100.0,
    "VIXY": vixy_bar_pct / 100.0,
    "SHV": shv_bar_pct / 100.0,
}

v_bench = bt.simulate_yearly_rebalance(prices, w_bench)
v_barbell = bt.simulate_yearly_rebalance(prices, w_barbell)

bench_label = f"Benchmark ({spy_bench_pct}% SPY, {shv_bench_pct}% SHV)"
barbell_label = (
    f"Barbell ({spy_bar_pct}% SPY, {vixy_bar_pct}% VIXY, {shv_bar_pct}% SHV)"
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Benchmark total return", f"{bt.total_return_from_initial(v_bench):.2%}")
with c2:
    st.metric("Barbell total return", f"{bt.total_return_from_initial(v_barbell):.2%}")
with c3:
    st.metric("Benchmark max drawdown", f"{bt.max_drawdown(v_bench):.2%}")
with c4:
    st.metric("Barbell max drawdown", f"{bt.max_drawdown(v_barbell):.2%}")

fig, ax = plt.subplots(figsize=(11, 5))
for label, start, end in bt.SHADES:
    ax.axvspan(
        pd.Timestamp(start),
        pd.Timestamp(end),
        color="red",
        alpha=0.18,
        label=label,
        zorder=0,
    )
ax.plot(v_bench.index, v_bench.values, label=bench_label, linewidth=1.8)
ax.plot(v_barbell.index, v_barbell.values, label=barbell_label, linewidth=1.8)
ax.set_title("Portfolio value over time")
ax.set_xlabel("Date")
ax.set_ylabel("Value ($)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.grid(True, alpha=0.3)
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc="upper left")
fig.tight_layout()
st.pyplot(fig, clear_figure=True)
plt.close(fig)

st.caption(
    f"Sample: {v_bench.index[0].date()} → {v_bench.index[-1].date()} · "
    f"Final: benchmark ${v_bench.iloc[-1]:,.2f}, barbell ${v_barbell.iloc[-1]:,.2f}"
)
