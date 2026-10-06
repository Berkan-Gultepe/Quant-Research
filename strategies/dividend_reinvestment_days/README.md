# Dividend-reinvestment days — ES, long on high-payout days

**Status: ⚰️ Dead at gate 1 (back-of-envelope), no data touched — the published effect (~7 bp/day) is about three times too small to be certified in 16 years of ES at my significance hurdle.**
**Case 15 | October 2026 | tenth run (mid-month search) · literature-anchored · killed before any data purchase**

---

## Why this one

Hartzmark & Solomon, *Market-Wide Predictable Price Pressure* (American Economic Review 115(9), Sept. 2025; NBER w30688): on days with large aggregate dividend payments, value-weighted US market returns are higher — top quarter of payment days **+7.1 bp (t 4.27)**, top-10 days of the year +11.6 bp, 1926–2018, replicated in 58 countries, robust to day-of-week, turn-of-month, FOMC and macro controls. Mechanism: funds (fully-invested mandates) and DRIP plans reinvest dividends into the market on the payment date; the date and amount are known weeks ahead, yet the pressure persists. It was the only mid-month candidate with a living primary source after a full run through the payer table.

---

## Pre-registration (written before touching any dividend data)

Hypothesis: on trading days whose aggregate US dividend payment (known the evening before) is in the top quarter of the trailing 252 days, long ES 18:00 (prior evening) → 16:44 earns at least 1.8 bp (3 × 0.6 bp cost) **more** than on all other days. One variant. IS 2010-06 → 2018-12 (paper overlap), OOS 2019-01 → 2026-07 one look. Dead if: excess < 1.8 bp · other days ≥ 50 % of signal days · t (HAC) of the difference < 3.3 (gate-5 hurdle incl. +0.3 for the thirteenth case of the year).

---

## Gate 1 — back of the envelope

Only noise and sample size from my own ES daily table (18:00 → 15:59 window); no dividend data loaded, nothing sorted.

| window | days | top quarter | σ per day | SE of difference | **min. detectable effect (3 × SE)** | paper's expectation | t at full paper strength |
|---|---|---|---|---|---|---|---|
| IS 2010–18 | 2,121 | 530 | 128 bp | 6.4 | **19.3 bp** | 7.1 | 1.10 |
| OOS 2019–26 | 1,887 | 471 | 157 bp | 8.3 | **25.0 bp** | 7.1 | 0.85 |
| all 2010–26 | 4,008 | 1,002 | 142 bp | 5.2 | **15.6 bp** | 7.1 | 1.37 |

Reaching t 3.3 at 7 bp would take ≈ 4,400 top-quarter days — about 70 years of ES. The paper's t comes from 93 years and cross-country pooling; I have one country and 16 years.

---

## Verdict

Dead at gate 1. Not the mechanism — its certifiability in my instrument and sample. With data (29 $, three weeks of API pulls) the case would have produced a t around 1 and died at gate 5; the envelope said so first.

---

## What I learned

- A large t from a very long sample says nothing about detectability in a short one. New line on the gate-1 envelope: **expected t = paper effect / own SE** — below the hurdle means dead before data.
- Effects of ≤ 10 bp/day against 140 bp of daily noise are never a case for a single-instrument, 16-year sample; at most a reading. That now screens out every "small flow, daily" hypothesis (payday, dividends, Gotobi) at the pre-gate.
- The mid-month calendar is now searched end to end: third-Friday option settlement (cases 14/14b, dead OOS), the 16th payday (literature Sharpe 0.14 since 1990, card only), dividend days (this case). What flows mid-month is too small to certify.
