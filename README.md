# Quant Research

Self-directed quantitative trading research. I build and validate systematic strategies from academic papers — momentum, risk engineering, cross-asset dynamics — with an emphasis on **honest validation**: a strategy only ships after it clears significance, out-of-sample, robustness, cost, multiple-testing and implementability hurdles.

> ⚠️ **Look-ahead bug found and fixed (July 2026).** During statistical re-validation I found a bug in the original TSMOM code that had inflated its Sharpe to 1.86. The honest rebuild (v2) is below and has since been through the full hurdle set — it clears six of seven. I'm leaving the story visible because catching your own bugs, and documenting them, is the job.

---

## Strategies

| Strategy | Sharpe | Status | Honest verdict |
|---|---|---|---|
| [TSMOM v2](strategies/tsmom_v2/) | **0.76** gross<br>**0.61** net | ✅ 6 of 7 hurdles<br>❌ fails implementability<br>🟢 Paper live since 2026-07-16 | Survives costs at 5 bp (t = 3.08), and survives the multiple-testing correction: **deflated Sharpe 96.6%, deflated t 1.83** after accounting for the 25-cell parameter search. Clears every bar — each one narrowly. **Cost-sensitive, not cost-proof**: dead at 20 bp. **Fails hurdle 6:** vol-scaling asks for up to **58x** leverage on a single quiet asset (~45x gross notional) — not fundable with any broker or futures account. A per-asset leverage cap is the blocking item before real money. Paper-only until then. |
| [Dual Momentum](strategies/dual_momentum/) | 0.66 | ⏸️ Validated, not traded | No alpha vs. SPY (p = 0.23) — it smooths the market rather than beating it. Significant against cash (p = 0.005), not against the benchmark that matters. **Not traded, on purpose:** if it can't beat buy-and-hold, the honest alternative is buy-and-hold. Kept as a documented negative result. |
| [ORB (prop firm)](strategies/orb_prop_firm/) | — | ⚰️ Abandoned | Significant gross (t = 5.43) but the edge died after slippage + commissions (t → 1.45). A cost-discipline lesson, kept on purpose. |

Research, not strategies: [portfolio construction](research/portfolio_construction/) — why risk allocation ≠ capital allocation, and what financing costs do to a levered risk-parity blend · [alternative data](research/alternative_data/) — COT positioning, credit spreads, yield-curve regime.

---

## Validation standards

Every strategy clears the same hurdles before any capital — paper or real:

1. **Significance** — t-test on daily returns, t > 3 (Harvey–Liu–Zhu bar), CI lower bound > 0.
2. **Out-of-sample** — fixed IS/OOS split; OOS is touched once, never for tuning.
3. **Robustness** — parameter-sensitivity grid (a plateau, not a lucky spike) + Monte Carlo block-bootstrap (does the result depend on the lucky *order* of days?).
4. **Costs** — the edge must survive realistic slippage + commissions (rule of thumb: edge ≥ 3× costs). Cost is modelled as `turnover × rate`, because turnover is the multiplier that decides which strategies die.
5. **Multiple testing** — the raw t-stat of the *best* cell in a parameter grid is inflated by the search itself. Corrected with the **deflated Sharpe ratio** (Bailey & López de Prado): the winning Sharpe is measured against the Sharpe a lucky-best-of-N search would produce anyway.
6. **Implementability** — does a broker, an instrument and an account size exist that can actually carry the position the sizing math demands? A strategy can clear every statistical hurdle and still be untradeable. **TSMOM v2 currently fails this one** (see below), which is why it is paper-only.
7. **Live validation** — paper trading catches pipeline bugs and tests discipline; the edge itself is validated only by *time*. At Sharpe 0.61 that means roughly a decade — paper trading proves the plumbing, not the alpha.

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
