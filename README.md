# The Antifragile Portfolio: Barbell Strategy Simulator

**An interactive quantitative backtesting tool that contrasts Nassim Nicholas Taleb’s barbell allocation philosophy with a classic 60/40 benchmark—built as a portfolio-quality demonstration of financial reasoning and production-minded Python engineering.**

**Repository:** [github.com/micah-mei/antifragile](https://github.com/micah-mei/antifragile)

Traditional portfolio theory often leans on Gaussian comfort: mean–variance optimization and “balanced” blends implicitly treat extreme events as rare curiosities. This project takes the opposite stance: it makes **tail risk and convexity** first-class citizens in both the investment narrative and the codebase.

---

## The Philosophy

### The problem (the *why*)

Many institutional and retail frameworks still behave as if returns were neatly normal. A standard **60/40** portfolio—**60% equities (SPY)** and **40% short-duration Treasuries (SHV)**—can be **fragile** to **fat-tailed** shocks: liquidity seizures, volatility spikes, and correlation breakdowns (e.g., the **2008** financial crisis or the **2020** COVID crash). When the left tail matters, “average” risk metrics understate what actually happens to wealth.

### The solution (the *what*)

**Taleb’s barbell** (in a quantitative, ETF-realistic form implemented here) deliberately avoids a **fragile middle**: it allocates **heavily** to **hyper-safe, liquid** exposure (short-term U.S. Treasuries via **SHV**) and keeps a **small** sleeve in **convex or aggressive** instruments—here **S&P 500 (SPY)** and **short-term VIX futures exposure (VIXY)** as a stylized volatility sleeve. The app lets you **stress-test** that barbell against a **configurable 60/40 benchmark** on the same calendar, with **year-end rebalancing** so both strategies share a fair, transparent rule set.

> **Disclaimer:** This project is for **education and engineering demonstration** only. It is **not** investment advice, a solicitation, or a recommendation. Past simulated performance does not guarantee future results. **VIXY** and similar products have unique risks (roll yield, contango, decay) that simplified backtests may not fully capture.

---

## Engineering Highlights

- **Interactive UI (Streamlit)**  
  A clean, responsive layout with a **dynamic sidebar**: allocation sliders **clamp automatically** so **SPY + VIXY cannot exceed 100%**, with **SHV** filling the remainder—reducing user error without extra clicks.

- **Bulletproof data pipeline (yfinance + pandas)**  
  Built to survive real-world API quirks:
  - **Dynamically selects `Adj Close` when present**, otherwise falls back to **`Close`**, including **MultiIndex** frames returned by multi-ticker downloads.
  - **Normalizes the datetime index** to naive calendar dates via `pd.to_datetime(pd.Series(idx).dt.date)` **before** `dropna()`, mitigating **timezone misalignment** across tickers that would otherwise produce empty frames after row-wise NA drops.

- **Optimized performance**  
  **`@st.cache_data`** on the price loader (with a sensible TTL) so **Yahoo Finance is not hit on every slider move**; only the lightweight simulation and chart refresh.

- **Visual analytics (matplotlib)**  
  Comparative **equity curves** on a **$10,000** base, with a **highlighted COVID crash window (Feb–Apr 2020)** to anchor drawdowns and recovery in a recognizable macro episode.

- **Automated deployment (Infrastructure as Code)**  
  **`render.yaml`** defines a **free-tier** Render **web service** (`barbell-dashboard`) with explicit **build** and **start** commands for reproducible cloud deploys.

---

## Tech Stack

- **Python**
- **Pandas** — alignment, time series, portfolio path simulation  
- **yfinance** — historical OHLC / adjusted prices  
- **Streamlit** — interactive dashboard and caching  
- **Matplotlib** — equity-curve visualization  
- **Git** — version control  
- **Render** — hosted deployment via Blueprint  

---

## Local Installation

```bash
git clone https://github.com/micah-mei/antifragile.git
cd antifragile

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

**Optional — command-line backtest & static plot**

```bash
python backtester.py              # interactive matplotlib window
python backtester.py --no-show    # writes portfolio_backtest.png, no GUI
```

---

## Project Structure

| File | Role |
|------|------|
| **`backtester.py`** | Core **quant engine**: loads prices, implements **year-end rebalancing** simulation, drawdown and return helpers, and a **CLI** entry point with optional PNG export. |
| **`streamlit_app.py`** | **Product layer**: wires sliders and metrics to `backtester`, applies **`st.cache_data`** for data fetch, renders **matplotlib** figures in-app. |
| **`render.yaml`** | **IaC** for **Render.com**: single **Python web** service **`barbell-dashboard`**, `pip install -r requirements.txt`, and `streamlit run streamlit_app.py --server.port $PORT`. |
| **`requirements.txt`** | Pinned dependency surface for local and cloud installs. |

---

## License & Attribution

This project is released under the [MIT License](LICENSE). Deployments and redistributions should still respect **yfinance** / **Yahoo** data terms of use.

---

*Built to read well on a resume or portfolio site: rigorous framing of tail risk, honest limitations of the model, and software practices that belong in a small production service—not just a notebook.*
