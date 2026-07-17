# TSMOM v2 — honest re-validation

Corrected rebuild of Time-Series Momentum after a look-ahead bug was found in v1
(inflated Sharpe 1.86 → honest 0.29 on the original 5-ETF universe). This v2 runs
on a broadened, growing **24-asset universe** (equities, bonds, commodities, FX).

**Paper:** Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, JFE 104(2).

## Files
- `tsmom_v2.py` — strategy: signal (12M trend) → vol-scaled position → returns (`position.shift(1) * log_returns`).
- `validation.py` — IS/OOS split, 5×5 parameter sensitivity, Monte Carlo block-bootstrap, **net-of-cost + Deflated Sharpe (KW29)**.
- `plot_results.py` — generates `results.png` (equity vs SPY + Monte Carlo cone).

## Reproduce

```bash
pip install numpy pandas yfinance scipy matplotlib
python tsmom_v2.py        # strategy + gross metrics (prints start date & length as sanity check)
python validation.py      # IS/OOS, sensitivity grid, Monte Carlo
python plot_results.py    # writes results.png
```

Daily data is pulled live from Yahoo Finance (24-asset universe, 2001–present). No API key needed.

## Results (KW28–29)

| Test | Result | Verdict |
|---|---|---|
| Significance (gross) | Sharpe **0.76** · t 3.83 · p 1.3e-4 · CI [+2.9%, +8.9%] | ✅ Hurdle 1 |
| IS / OOS | IS 0.80 → OOS 0.69 (14% decay, both significant) | ✅ Hurdle 2a |
| Sensitivity | all 25 cells positive (0.42–0.80), plateau at 126–252 lookback | ✅ Hurdle 2b |
| Monte Carlo | P(Sharpe>0)=100%, backtest = median, worst-5% DD **−26%** | ✅ robust |
| Costs (KW29) | net Sharpe **0.61** (5 bp) · t 3.08 · turnover 19.55/yr | ✅ survives (conditional) |
| Deflated Sharpe (KW29) | DSR **96.6%** · deflated t **1.83** (N=25, s_a 0.124) | ✅ passes multiple-testing |

Cost-sensitivity: 3 bp→0.67 · 5 bp→0.61 · 10 bp→0.46 (t<3) · 20 bp→0.16 (dead). Cost-sensitive, not cost-proof.

## Charts

![TSMOM v2 equity vs SPY (log scale) and Monte Carlo cone of 10k bootstrapped paths](results.png)

*Left: TSMOM v2 vs SPY buy-and-hold, log scale. Right: 10,000 block-bootstrapped equity paths — the real backtest (red) runs through the middle, and the lower edge stays above 1 (no path to ruin, gross of costs).*

> Run `python plot_results.py` to generate `results.png`, then commit it alongside the code.

## Honest verdict
Passes **all five hurdles** — significance, IS/OOS, sensitivity, Monte Carlo, costs *and*
Deflated Sharpe — but each only narrowly. The honest number after everything is a
**deflated t ≈ 1.8**, not the raw 3.08: costs shrink the edge (net Sharpe 0.61) and the
multiple-testing correction shrinks it further. Survives where ORB died (t 5.43 → 1.45)
because of far lower turnover. Green for **paper trading at very small size**, not "all in".
Kill-switch calibrated to the Monte-Carlo worst-case drawdown (−26%), not the single-backtest
−16.5%. Open before real money: per-asset leverage cap (vol-scaling wants ~10× on SHY),
vol-dependent costs, real broker rates.
