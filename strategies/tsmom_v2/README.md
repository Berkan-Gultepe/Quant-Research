# TSMOM v2 — honest re-validation

Corrected rebuild of Time-Series Momentum after a look-ahead bug was found in v1
(inflated Sharpe 1.86 → honest 0.29 on the original 5-ETF universe). This v2 runs
on a broadened, growing **24-asset universe** (equities, bonds, commodities, FX).

**Paper:** Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, JFE 104(2).

## Files
- `tsmom_v2.py` — strategy: signal (12M trend) → vol-scaled position → returns (`position.shift(1) * log_returns`).
- `validation.py` — IS/OOS split, 5×5 parameter sensitivity, Monte Carlo block-bootstrap.

## Results (KW28 — all GROSS of transaction costs)

| Test | Result | Verdict |
|---|---|---|
| Significance | Sharpe **0.76** · t 3.83 · p 1.3e-4 · CI [+2.9%, +8.9%] | ✅ Hurdle 1 |
| IS / OOS | IS 0.80 → OOS 0.69 (14% decay, both significant) | ✅ Hurdle 2a |
| Sensitivity | all 25 cells positive (0.42–0.80), plateau at 126–252 lookback | ✅ Hurdle 2b |
| Monte Carlo | P(Sharpe>0)=100%, backtest = median, worst-5% DD **−26%** | ✅ robust |
| Costs (KW29) | pending | ⏳ decisive |

## Honest verdict
Real edge **gross of costs**, robust to out-of-sample and to parameter/path reshuffling.
Not yet a live strategy — the transaction-cost hurdle (KW29) is the one that killed ORB
(t 5.43 → 1.45). Kill-switch calibrated to the Monte-Carlo worst-case drawdown (−26%),
not the single-backtest −16.5%. And that −26% is a floor, not a ceiling (bootstrap never
draws worse than history).
