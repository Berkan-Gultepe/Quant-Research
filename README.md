# Quant Research

Self-directed quantitative trading research. I build and validate systematic strategies from academic papers — momentum, risk engineering, cross-asset dynamics — with an emphasis on **honest validation**: a strategy only ships after it clears significance, out-of-sample, robustness and cost hurdles.

> ⚠️ **Results under revision (2026-07).** During statistical re-validation I found a look-ahead bug in the original TSMOM code that had inflated its Sharpe to 1.86. The honest rebuild (v2) is below. I'm leaving the story visible because catching your own bugs — and documenting them — is the job.

---

## Strategies

| Strategy | Sharpe (gross) | Status | Honest verdict |
|---|---|---|---|
| [TSMOM v2](strategies/tsmom_v2/) | **0.76** | ✅ Hurdles 1–2 + Monte Carlo passed · costs pending | Real edge gross of costs; robust out-of-sample (IS 0.80 → OOS 0.69) and to parameter/path reshuffling. Not live until it survives transaction costs. |
| [Dual Momentum](strategies/dual_momentum/) | 0.66 | 🔄 Paper trading | No alpha vs. SPY (p = 0.23) — smooths the market, doesn't beat it |
| [ORB (prop firm)](strategies/orb_prop_firm/) | — | ⚰️ Abandoned | Significant gross (t = 5.43) but the edge died after slippage + commissions (t → 1.45). A cost-discipline lesson, kept on purpose. |

Exploratory work, not yet strategies: [alternative data](research/alternative_data/) — COT positioning, credit spreads, yield-curve regime.

---

## Validation standards

Every strategy clears the same hurdles before any capital — paper or real:

1. **Significance** — t-test on daily returns, t > 3 (Harvey–Liu–Zhu bar), CI lower bound > 0.
2. **Out-of-sample** — fixed IS/OOS split; OOS is touched once, never for tuning.
3. **Robustness** — parameter-sensitivity grid (a plateau, not a lucky spike) + Monte Carlo block-bootstrap (does the result depend on the lucky *order* of days?).
4. **Costs** — the edge must survive realistic slippage + commissions (rule of thumb: edge ≥ 3× costs).
5. **Live validation** — paper trading catches pipeline bugs; the strategy itself is validated only by *time*.

Failures are documented, not hidden — see the post-mortem below and the abandoned ORB.

---

## Post-mortem: how I caught my own look-ahead bias

While learning hypothesis testing, I re-implemented TSMOM from scratch and ran a t-test. Expected t ≈ 5–6 (consistent with the published Sharpe); got **t = 1.28, p = 0.20**. The rebuild was a faithful copy of the original — which meant the original had the bug.

**The bug — one line:**

```python
# WRONG (original): today's position × yesterday's return
returns = position * log_returns.shift(1)

# RIGHT: yesterday's position × today's return
returns = position.shift(1) * log_returns
```

The 12-month signal window *contains* yesterday's return, so the shifted-return version let the signal "know" the outcome of the day it was trading. Same data, same parameters, only that line changed:

| Version | Sharpe | t-stat | p-value |
|---|---|---|---|
| Original (bug) | 1.87 | 8.15 | 4.6×10⁻¹⁶ |
| Corrected | 0.29 | 1.28 | 0.20 |

**What I take from it:** a single honest significance test found a bug that had survived an IS/OOS split, a parameter grid and a "fully validated" label — validation built on broken code just validates the bug. And Sharpe 1.86 on 5 ETFs with vanilla momentum should have triggered suspicion: Moskowitz et al. (2012) report ~1.0 gross on 58 futures markets. When your simple version beats the paper by 80%, the likely explanation is a bug, not genius. The corrected, broadened rebuild lives in [`strategies/tsmom_v2/`](strategies/tsmom_v2/).

*Side-finding:* the audit extended to all strategies — the cross-sectional momentum code traded with inverted signs (buying losers). Its results are void; a clean re-test on a survivorship-free universe is queued.

---

## Reproduce

```bash
pip install -r requirements.txt
```

Then run any strategy from its folder (each has its own README, code and results). Data is pulled live from Yahoo Finance — no API key needed.

**Stack:** Python · pandas · numpy · scipy · statsmodels · yfinance · matplotlib

---

## Reference

> Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). *Time Series Momentum.*
> Journal of Financial Economics, 104(2), 228–250. https://doi.org/10.1016/j.jfineco.2011.11.003

---

*Portfolio in development — updated as strategies clear (or fail) the hurdles.*
