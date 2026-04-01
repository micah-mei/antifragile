"""
Backtest 60/40 vs barbell with year-end rebalancing only.
Data: SPY, SHV, VIXY via yfinance, 2012-01-01 through 2024-01-01 (end exclusive).

Barbell: 90% SHV, 5% SPY, 5% VIXY (ProShares VIX Short-Term Futures). Legacy barbell
(10% SPY, 90% SHV) is simulated for return comparison under the same annual rebalance rule.

Run with --no-show to write portfolio_backtest.png instead of opening a window
(useful for headless or automated runs).

Interactive UI: ``streamlit run streamlit_app.py`` from this directory.
"""

from __future__ import annotations

import argparse
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

START = "2012-01-01"
END = "2024-01-01"
INITIAL = 10_000.0

W_6040 = {"SPY": 0.60, "SHV": 0.40}
W_BARBELL = {"SPY": 0.05, "VIXY": 0.05, "SHV": 0.90}
W_BARBELL_LEGACY = {"SPY": 0.10, "SHV": 0.90}

# Crisis window for shading (sample starts 2012; 2008 not in range)
SHADES = [
    ("2020 COVID crash", "2020-02-01", "2020-04-30"),
]


def load_prices() -> pd.DataFrame:
    raw = yf.download(
        ["SPY", "SHV", "VIXY"],
        start=START,
        end=END,
        progress=False,
        auto_adjust=True,
    )
    if raw.empty:
        raise RuntimeError("No data returned from yfinance.")
    close = raw["Close"].copy()
    close = close.dropna(how="any")
    close = close.sort_index()
    return close


def _year_end_rebalance_dates(index: pd.DatetimeIndex) -> set[pd.Timestamp]:
    """Last trading session in each calendar year present in the index."""
    dates: set[pd.Timestamp] = set()
    for y in index.year.unique():
        sub = index[index.year == y]
        dates.add(pd.Timestamp(sub.max()))
    return dates


def simulate_yearly_rebalance(
    prices: pd.DataFrame,
    weights: dict[str, float],
    initial: float = INITIAL,
) -> pd.Series:
    """
    Hold fixed shares between year-ends; rebalance to target weights at each
    calendar year's last trading close (including drifting weights intra-year).
    """
    tickers = list(weights.keys())
    tw = sum(weights.values())
    w = {t: weights[t] / tw for t in tickers}

    px = prices[tickers].astype(float)
    idx = px.index
    rebalance_on = _year_end_rebalance_dates(idx)

    shares: dict[str, float] = {}
    values: list[float] = []

    for i, d in enumerate(idx):
        row = px.loc[d]
        if i == 0:
            for t in tickers:
                shares[t] = (initial * w[t]) / row[t]
            v = float(sum(shares[t] * row[t] for t in tickers))
        else:
            v = float(sum(shares[t] * row[t] for t in tickers))
            if d in rebalance_on:
                for t in tickers:
                    shares[t] = (v * w[t]) / row[t]
        values.append(v)

    return pd.Series(values, index=idx, name="portfolio_value")


def max_drawdown(series: pd.Series) -> float:
    """Largest peak-to-trough decline as a positive fraction (e.g. 0.35 == 35%)."""
    s = series.astype(float)
    running_max = s.cummax()
    underwater = (s - running_max) / running_max
    return float(-underwater.min())


def print_max_drawdown_for_portfolios(
    sixty_forty: pd.Series,
    barbell: pd.Series,
    sixty_forty_name: str = "60/40",
    barbell_name: str = "Barbell (5% SPY, 5% VIXY, 90% SHV)",
) -> None:
    print(f"{sixty_forty_name} maximum drawdown: {max_drawdown(sixty_forty):.2%}")
    print(f"{barbell_name} maximum drawdown: {max_drawdown(barbell):.2%}")


def total_return_from_initial(series: pd.Series) -> float:
    """Total return vs the $10,000 starting capital (end of sample)."""
    return float(series.iloc[-1] / INITIAL - 1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPY/SHV/VIXY year-end rebalance backtest",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Save portfolio_backtest.png and skip interactive window",
    )
    args = parser.parse_args()

    prices = load_prices()
    if prices.empty:
        raise RuntimeError("No overlapping rows after dropna.")

    v_6040 = simulate_yearly_rebalance(prices, W_6040)
    v_barbell = simulate_yearly_rebalance(prices, W_BARBELL)
    v_barbell_legacy = simulate_yearly_rebalance(prices, W_BARBELL_LEGACY)

    tr_6040 = total_return_from_initial(v_6040)
    tr_bar = total_return_from_initial(v_barbell)
    tr_legacy = total_return_from_initial(v_barbell_legacy)

    print(f"Backtest window: {v_6040.index[0].date()} → {v_6040.index[-1].date()}")
    print(f"Rebalancing: last trading day of each calendar year only.")
    print(f"60/40 total return (from ${INITIAL:,.0f}): {tr_6040:.2%}")
    print(f"Barbell (10% SPY, 90% SHV) total return [comparison]: {tr_legacy:.2%}")
    print(f"Barbell (5% SPY, 5% VIXY, 90% SHV) total return: {tr_bar:.2%}")
    print(
        f"Barbell change vs 10% SPY-only (same annual rebalance): "
        f"{tr_bar - tr_legacy:+.2%} absolute return",
    )
    print(f"Final value 60/40: ${v_6040.iloc[-1]:,.2f}")
    print(f"Final value Barbell (5/5/90): ${v_barbell.iloc[-1]:,.2f}")
    print()
    print_max_drawdown_for_portfolios(v_6040, v_barbell)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    for label, start, end in SHADES:
        ax.axvspan(
            pd.Timestamp(start),
            pd.Timestamp(end),
            color="red",
            alpha=0.18,
            label=label,
            zorder=0,
        )

    ax.plot(v_6040.index, v_6040.values, label="60/40 (60% SPY, 40% SHV)", linewidth=1.5)
    ax.plot(
        v_barbell.index,
        v_barbell.values,
        label="Barbell (5% SPY, 5% VIXY, 90% SHV)",
        linewidth=1.5,
    )

    ax.set_title("Year-end rebalanced portfolios: $10,000 start")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value ($)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(True, alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper left")
    fig.tight_layout()
    if args.no_show:
        out_path = "portfolio_backtest.png"
        fig.savefig(out_path, dpi=150)
        print(f"\nSaved chart to {out_path}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
