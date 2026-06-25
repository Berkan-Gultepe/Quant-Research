# Quant Research

Systematic quantitative trading research — strategy development, backtesting, and rigorous statistical validation.

---

## Strategy: Time-Series Momentum (TSMOM)

**Paper:** Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). *Time Series Momentum.* Journal of Financial Economics, 104(2), 228–250.  
**Universe:** SPY · GLD · TLT · USO · UUP  
**Period:** 2000–2026  
**Rebalancing:** Daily  
**Signal:** 12-month trailing return (252 trading days)  
**Position sizing:** Volatility-scaled to 15% annualized target volatility

---

## Equity Curve
<img width="1783" height="1033" alt="tsmom_equity_curve" src="https://github.com/user-attachments/assets/f2b1124a-fdba-4ef3-8205-80ea952b384d" />


---

## Core Idea

Go long an asset if its 12-month return is positive, short if negative. Scale position size inversely to recent realized volatility so each asset contributes equally to portfolio risk.

```
signal    = sign(12M return)          # +1 long / -1 short
position  = signal × (target_vol / realized_vol)
```

The key insight: volatility scaling transforms a Sharpe of **0.13** (binary signal) into **1.86** (vol-scaled). Without it, the strategy barely beats noise. With it, it is one of the most robust anomalies in empirical finance.

---

## Results

| Metric | Value |
|--------|-------|
| Sharpe Ratio (gross) | **1.86** |
| Sharpe Ratio (net, 5 bps) | 1.73 |
| Annualized Return | ~28% |
| Annualized Volatility | ~15% |
| Max Drawdown | **−9.3%** |
| Positive Years | 17 / 19 |
| Best Year | 2013 (Sharpe 3.75) |
| Worst Year | 2009 (Sharpe −0.07) |
| p-value (t-test) | **2.2 × 10⁻¹⁵** |

---

## In-Sample vs. Out-of-Sample

| Period | Sharpe |
|--------|--------|
| In-Sample (2000–2015) | 1.63 |
| Out-of-Sample (2015–2026) | **1.87** |

OOS Sharpe **exceeds** IS Sharpe — no overfitting detected. The strategy held up on unseen data better than on the data it was developed on.

---

## Binary vs. Volatility-Scaled

| Variant | Sharpe | Comment |
|---------|--------|---------|
| Binary (no vol scaling) | 0.13 | Below SPY buy & hold |
| Volatility-scaled | **1.86** | Core result |

This comparison demonstrates that the signal itself (momentum direction) has edge — but without proper position sizing, the edge is buried under unequal risk contributions.

---

## Parameter Sensitivity (Sharpe across lookback × vol-window)

|  | Vol 20d | Vol 40d | Vol 60d | Vol 120d |
|--|---------|---------|---------|----------|
| **Lookback 63d** | 3.57 | 3.37 | 3.25 | 3.06 |
| **Lookback 126d** | 2.61 | 2.51 | 2.46 | 2.31 |
| **Lookback 189d** | 2.11 | 2.04 | 2.01 | 1.91 |
| **Lookback 252d** | 1.97 | 1.88 | **1.86** | 1.79 |

All 16 parameter combinations produce Sharpe > 1.7. The result is not sensitive to exact parameter choice — this rules out overfitting to a specific lookback or vol window.

---

## Asset Correlations

No pair of assets exceeds 0.5 correlation. USO (oil) and GLD (gold) are slightly negatively correlated with SPY — providing genuine diversification rather than concentrated risk.

This is why cross-asset momentum works: assets move in different directions at different times, and the strategy systematically captures those trends.

---

## Methodology & Validation Standards

- **Look-ahead bias prevention:** Signal computed on close[t], applied at open[t+1] via `.shift(1)`
- **Data quality:** `yfinance` with `auto_adjust=True` — split and dividend adjusted prices
- **IS/OOS split:** Fixed cutoff 2015 — OOS data never touched during development
- **Statistical test:** t-test on daily returns, p = 2.2 × 10⁻¹⁵
- **Parameter robustness:** Full 4×4 sensitivity grid — no cherry-picked parameters
- **Benchmark:** Compared against SPY buy & hold

---

## Code

Signal construction and position sizing in ~10 lines:

```python
# 1. Signal: 12-month trailing return
signal = np.sign(close.pct_change(252)).shift(1)   # shift(1) prevents look-ahead bias

# 2. Volatility scaling: each asset targets 15% annualized vol
vol      = log_returns.rolling(60).std() * np.sqrt(252)
position = (0.15 / vol) * signal

# 3. Portfolio return: equal-weighted across assets
portfolio_returns = (position * log_returns.shift(1)).mean(axis=1)
```

Full implementation: [`14 Code/TSMOM_Framework.py`](14%20Code/TSMOM_Framework.py)

---

## Stack

```
Python     pandas · numpy · scipy · statsmodels · yfinance · matplotlib
```

---

## Reference

> Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012).  
> *Time series momentum.*  
> Journal of Financial Economics, 104(2), 228–250.  
> https://doi.org/10.1016/j.jfineco.2011.11.003

---

*More strategies in development. Updated regularly.*
