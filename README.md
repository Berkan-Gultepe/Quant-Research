# Quant Research

Self-directed quantitative trading research. I build and validate systematic strategies from academic papers — focusing on momentum, risk engineering, and cross-asset dynamics.

Background in finance with a focus on systematic approaches. Currently developing a research portfolio of backtested strategies with rigorous statistical validation standards (IS/OOS split, significance testing, parameter robustness).

> ⚠️ **Results under revision (2026-07-06).** During statistical re-validation I discovered a look-ahead bug in the TSMOM return calculation. The headline numbers below (Sharpe 1.86, p = 2.2×10⁻¹⁵) are artifacts of that bug — the honest result of the same implementation is **Sharpe 0.29 (t = 1.28, p = 0.20, not significant)**. Full post-mortem below; re-validation with corrected code and a broader asset universe is in progress. I'm leaving the original numbers visible because catching your own bugs — and documenting them — is the job.

---

## Strategies in this repo

| Strategy | Sharpe | Status | Honest verdict |
|---|---|---|---|
| TSMOM (below) | ~~1.86~~ 0.29* | ⚠️ Re-validation | Look-ahead artifact — see post-mortem |
| [Dual Momentum](strategies/dual_momentum/) | 0.66 | 🔄 Paper trading | No alpha vs. SPY (p = 0.23) — smooths the market, doesn't beat it |

*\*Honest value after bug fix (5-ETF universe). Re-validation with broader universe in progress.*

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

## Post-Mortem: How I caught my own look-ahead bias (2026-07-06)

**What happened.** While learning hypothesis testing, I re-implemented TSMOM from scratch and ran a t-test on the daily returns. Expected: t ≈ 5–6, consistent with the published Sharpe. Got: t = 1.28, p = 0.20. The rebuild was a faithful copy of the original — which meant the original had the bug.

**The bug.** One line:

```python
# WRONG (original):
signal  = np.sign(close.pct_change(252)).shift(1)
returns = position * log_returns.shift(1)

# RIGHT:
signal  = np.sign(close.pct_change(252))
returns = position.shift(1) * log_returns
```

The original multiplied today's position by *yesterday's* return. Since the momentum signal window (12-month return ending yesterday) *contains* yesterday's return, the signal already knew the outcome of the day it was trading. Systematically long on up-days — dream numbers out of thin air.

**The proof.** Same data, same parameters, only the line above changed:

| Version | Sharpe | t-stat | p-value |
|---|---|---|---|
| Original (bug) | 1.87 | 8.15 | 4.6×10⁻¹⁶ |
| Corrected | 0.29 | 1.28 | 0.20 |

**What I take from it.**
1. A single honest significance test on a clean rebuild found a bug that had survived IS/OOS splits, a 4×4 parameter grid and a "fully validated" label. Validation built on top of broken code validates the bug.
2. Sharpe 1.86 on 5 ETFs with vanilla momentum should have triggered suspicion — Moskowitz et al. (2012) report ~1.0 gross on 58 futures markets. When your simple version beats the paper by 80%, the most likely explanation is a bug, not genius.
3. Re-validation (corrected code, broader universe, transaction costs) is in progress. Results will be published here — whatever they are.

---

## Results — ⚠️ invalid, see post-mortem above

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

- **Look-ahead bias prevention:** ~~Signal computed on close[t], applied at open[t+1] via `.shift(1)`~~ ⚠️ This claim was wrong — the shift was applied in the wrong place (see post-mortem). Corrected pattern: `position.shift(1) * returns`
- **Data quality:** `yfinance` with `auto_adjust=True` — split and dividend adjusted prices
- **IS/OOS split:** Fixed cutoff 2015 — OOS data never touched during development
- **Statistical test:** t-test on daily returns, p = 2.2 × 10⁻¹⁵
- **Parameter robustness:** Full 4×4 sensitivity grid — no cherry-picked parameters
- **Benchmark:** Compared against SPY buy & hold

---

## Code

Signal construction and position sizing in ~10 lines:

```python
# 1. Signal: 12-month trailing return (unshifted — timing handled once, at the end)
signal = np.sign(close.pct_change(252))

# 2. Volatility scaling: each asset targets 15% annualized vol
vol      = log_returns.rolling(60).std() * np.sqrt(252)
position = (0.15 / vol) * signal

# 3. Portfolio return: yesterday's position earns today's return
portfolio_returns = (position.shift(1) * log_returns).mean(axis=1)
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
