# ORR — Opening Range Reversion (False-Breakout Fade)

**Status: ❌ Dead — the signal has no directional edge (~coin flip at symmetric R:R)**
**KW32 | August 2026**

---

## Strategy Overview

The mirror image of [ORB](../orb_prop_firm): instead of *following* the opening-range breakout,
**fade** it. Hypothesis: opening-range breakouts are mostly false (stop-runs with no real order
flow behind them), so a break that pokes out and returns should keep reverting toward the middle.

| Parameter | Value |
|-----------|-------|
| Instrument | ES futures (Databento 1-min, front-month, RTH) |
| Opening Range | First 30 min (09:30–10:00 ET) |
| Entry window | 10:00–11:00 ET |
| Signal | False breakout that closes back inside the range within N=5 min |
| Direction | Fade (short an up-break / long a down-break) |
| Stop | Breakout extreme (v1) → **symmetric half-range** (final) |
| Target | VWAP (v1) → **fixed half-range** (final) |
| Volume filter | return-bar volume > 1.5× OR-median (v1) → **removed** (final) |
| Cost | 1.3 ticks round-turn |

---

## Diagnostic — four stages, one variable at a time

The point of the exercise was to trace the failure from the *exit* back to the *signal*.

| Stage | Change | Gross avg | Real win rate | Skew | Sharpe (ann.) |
|-------|--------|-----------|---------------|------|---------------|
| v1   | VWAP target (dynamic) + volume filter | −1.95 t | **37%** (but 69% "target"!) | −0.80 | −2.16 |
| v1.5 | fixed **half-range** target | −0.70 t | 42% | −0.41 | −0.68 |
| v1.6 | + **symmetric** half-range stop | −0.77 t | 48.1% | **+0.02** | −0.68 |
| v1.7 | + volume filter **removed** (3411 trades) | −0.26 t | **48.6%** | +0.03 | −0.70 |

**Decisive result (v1.7):** at symmetric R:R (skew neutralized), win rate 48.6% over 3411 trades,
SE ≈ 0.86% → **not statistically different from 50%**. The signal does not predict reversion.

---

## Key Lessons

1. **A dynamic VWAP target lies.** v1 reported 69% "target hit" but only 37% *real* wins — because
   VWAP moves and "price ≤ VWAP" for a short can trigger *above* the entry. Use a fixed target level
   for any reversion test.
2. **Fades are negative-skew — but that is an exit artifact, not fate.** The fat left tail came from
   the far stop at the breakout extreme (trend days ran −107 ticks). A fixed, symmetric stop
   neutralizes the skew (+0.02).
3. **The signal isolator (the reusable bit):** to test whether a signal has a real edge, strip it to
   **symmetric R:R and read the win rate vs 50%**. This removes every place exit curve-fitting could
   hide. 48.6% ≈ 50% → no edge; no target/stop/filter can rescue that.
4. **Prop-box requirement is edge AND skew, not one:** ORR ended with acceptable (neutral) skew but no
   edge → still dead. Neutral skew is *necessary, not sufficient*.

---

## The ORB + ORR double conclusion

- **ORB** (follow the breakout): gross Sharpe ~0.15 → no edge.
- **ORR** (fade the breakout): 48.6% at symmetric R:R → no edge.

Both sides of the same coin tested. **The ES opening-range break carries no tradeable directional
information** — it is noise in both directions. Next candidate → out of the opening-range class,
into structural / forced-flow ideas (see research notes: structural-constraint catalog).

---

## Files

| File | Description |
|------|-------------|
| `orr_backtest.py` | Full backtest; four config flags reproduce the four diagnostic stages above |

## Dependencies

```
pip install pandas numpy scipy pyarrow
```

Data: Databento GLBX.MDP3 ES 1-min OHLCV, cleaned to front-month-by-volume (not shipped here).
Point `DATA_PATH` at your cleaned parquet.

---

*Documented and abandoned KW32, August 2026. Archived for reference — not for live trading.*
