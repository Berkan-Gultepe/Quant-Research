# Dual Momentum (Antonacci)

**Paper:** Antonacci, G. (2014). *Dual Momentum Investing.* McGraw-Hill.
**Universe:** SPY · EFA · AGG · BIL (T-Bill proxy)
**Period:** 2007–2026 (BIL inception) · **Rebalancing:** Monthly
**Status:** 🔄 Paper trading — with honest expectations (see verdict)

---

## Core Idea

Each month: compare 12-month momentum of SPY vs. EFA (*relative momentum*), pick the winner. If the winner's momentum doesn't beat T-Bills (*absolute momentum*), go to bonds (AGG) instead.

```
winner = SPY if mom(SPY) > mom(EFA) else EFA
hold   = winner if mom(winner) > mom(BIL) else AGG
```

Signal uses `pct_change(12).shift(1)` on monthly closes — no look-ahead (verified 2026-07-06, see below).

---

## Results

| Metric | Dual Momentum | SPY Buy & Hold |
|---|---|---|
| Annualized Return | 11.0% | 13.7% |
| Annualized Volatility | 16.6% | 19.8% |
| Sharpe | 0.66 | 0.69 |
| Sortino | 0.80 | 0.84 |
| **Max Drawdown** | **−33.7%** | **−47.2%** |
| Calmar | 0.33 | 0.29 |
| Trading Days | 4,531 | 4,531 |


**Positions:** SPY 143 months · EFA 40 · AGG 35 (of 218)
**IS/OOS:** In-Sample Sharpe 0.61 (2007–2021) · Out-of-Sample 0.80 (2021–2026) — OOS/IS ratio 1.30
**Alpha/Beta vs. SPY:** Beta 0.63 · Alpha 2.39% p.a. (p < 0.001) · R² 0.57

---

## Significance Tests — and *what each one tests against*

The key methodological point of this strategy's evaluation:
**every test has an opponent, and "significant" only holds against that specific opponent.**

| Test | Opponent (null) | Result | Verdict |
|---|---|---|---|
| t-test on daily returns | Cash / doing nothing | p = 0.0049 | ✅ makes real money |
| Bootstrap 95%-CI (Sharpe) | Zero | [0.19, 1.13] | ✅ zero excluded |
| Sharpe test (Lo 2002) | Zero | z ≈ 2.8 | ✅ |
| **Paired t-test vs. SPY (monthly)** | **Buy & Hold** | **p = 0.23** | ❌ **not distinguishable from SPY** |
| Walk-forward vs. SPY (yearly) | Buy & Hold | beats SPY 2/19 years | ❌ |

A strategy can be highly significant against cash and still worthless — because a 0.1%-fee ETF delivers the same for free. The t-test vs. zero measures **beta + alpha combined**; the test vs. benchmark isolates **alpha alone**. Only alpha justifies the effort.

---

## Honest Verdict

**Dual Momentum does not beat the market — it smooths it.**

There is no statistically demonstrable alpha over SPY buy & hold. What the strategy *does* deliver: the market's return profile with roughly one-third less drawdown (−33.7% vs. −47.2%), beta 0.63, and its best year exactly when it matters (2008: +6.7% vs. SPY −28.3%).

That is a legitimate value proposition — **downside smoothing, not alpha** — and it should be labeled as such. Paper trading continues with this expectation, not with a market-beating one.

---

## Code Review Note (2026-07-06)

After finding a look-ahead bug in our TSMOM implementation (see main README post-mortem), this strategy was audited for the same error pattern. Result: **clean.** The signal chain (`shift(1)` on monthly momentum + forward-fill from signal date) contains no look-ahead — if anything it is one month over-lagged, which is conservative.

One bug was found and fixed in the *evaluation* code: the Lo (2002) Sharpe test mixed the annualized Sharpe with daily observation counts, producing a nonsensical z = 40. Corrected to daily units (z ≈ 2.8, consistent with the t-test).

---

## Reference

> Antonacci, G. (2014). *Dual Momentum Investing: An Innovative Strategy for Higher Returns with Lower Risk.* McGraw-Hill.
