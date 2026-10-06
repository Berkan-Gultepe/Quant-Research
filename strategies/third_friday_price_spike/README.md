# Third Friday Price Spike — ES/NQ, long into the SOQ, short after the open

**Status: ⚰️ Dead (two files) — in-sample 2010–21 the effect is there (ES +14.2 bp vs 3.8 bp control); out-of-sample 2022–26 it is gone (ES +3.2 bp net, t 0.30). A published anomaly that stopped working the year its paper came out.**
**Cases 14 / 14b | October 2026 | ninth run · literature-anchored · one pre-registered OOS look**

---

## Why this one

The strongest "forced flow" mechanism I had not yet tested, and the first candidate with a different calendar from my month-end cases: mid-month, twelve events a year, both legs inside the prop-firm session, on ES and NQ. Baltussen, Terstegge & Whelan (SSRN 4562800, 2023, R&R *Review of Financial Studies*, formerly *The Derivative Payoff Bias*) report that the S&P 500 rises systematically from the third-Thursday close into Friday's opening settlement (SOQ) of a.m.-settled SPX options — **+18.5 bp, t 4.7, 225 events 2003–2021** — and reverses after 9:30. Their E-mini version after full spread costs: **24 bp net per event**, 16 of 19 years positive.

**Mechanism:** a.m. SPX options stop trading Thursday 16:15 and settle against Friday's opening prices of all 500 constituents. Option market makers sit on fixed positions through an illiquid night; their inventory delta decays into expiry and they must buy. After 9:30 the pressure is gone and the price reverts until noon.

---

## Pre-registration

**Case 14 (written 05.10.2026 before touching the data).** Hypothesis: on SPX a.m. expiry days (third Friday; Thursday if Friday is a holiday) the ES trade *long 18:00 previous evening → 9:30, short 9:30 → 12:00* earns net ≥ 3.6 bp (3 × 1.2 bp cost). Three variants counted: V1 both legs unconditional (primary), V2 day leg only after a positive night, V3 night leg only. NQ as second series.

Dead if: (1) V1 IS net < 3.6 bp · (2a) same trade on all other Fridays ≥ 50 % of expiry-day V1 · (2b) night leg on expiry days minus night leg on other Fridays < 8 bp · (3) OOS 2022–26 mean ≤ 0 · (4) IS top-5 share > 50 % · (5) pre-sample 1993–2002 night leg on SPY ≤ 0 = flag only.
Splits: IS 2010–2021 (~144 events), OOS 2022–2026 (~57), one look after gate 5. Gate-5 hurdle t 3.5 (3 variants + tenth case of the year).

**Case 14b (written after case 14 died, before the OOS look).** The IS years were spent; 2022–2026 had been seen by neither me nor the paper. One variant (V1), ES primary, NQ second series, thresholds from the own ES replication only. Dead if: (1) ES V1 net ≤ 3.6 bp · (2) other-Friday V1 ≥ 50 % of expiry V1 · (3) ES V1 t (HAC) < 2.0. No top-5 clause (lesson from case 13). Alive → paper trading from 20.11.2026 as a third leg.

---

## Parameters

| Parameter | Value |
|---|---|
| Instruments | ES, NQ futures, Databento GLBX 1-min OHLCV, 2010-06 → 2026-07 |
| Contract | front month by 10–12 h volume on the Friday; on quarterly expiries the **next** contract (the front settles into the SOQ at 9:30) |
| Expiry day | third Friday; preceding Thursday when Friday is an NYSE holiday |
| Night leg | long 18:00 Thursday (first bar) → 9:30 Friday (first bar) |
| Day leg | short 9:30 → 12:00 |
| Cost | 1.2 bp round trip for both legs together (0.6 per leg) |
| Validation | inject +10 bp → 10.00 recovered · hand checks 20.03.2020 (night +297 / day short +152), 17.06.2022 (−22 / +22), 18.07.2025 (+15 / +19) · unconditional control: same trade on every other Friday |

---

## Results

**Case 14 — IS 2010–2021, gross, bp**

| | n | night 18:00→9:30 | day short 9:30→12:00 | V1 | V2 | short 9:30→9:45 |
|---|---|---|---|---|---|---|
| ES expiry days | 139 | **+7.0** (paper window 16:00→9:30: +8.5) | **+7.2** | **+14.2** | +12.0 | +6.0 |
| ES other Fridays | 449 | +1.7 | +1.6 | +3.8 (27 %) | | −0.9 |
| NQ expiry days | 139 | | +14.5 | **+22.5** | | |
| NQ other Fridays | 449 | | | +4.1 | | |

Quarterly expiries ES V1 **+30.4** (n 47) vs other months +5.9. 7:00→9:30 pre-open drift: no difference to other Fridays (2.2 vs 2.1). The reversal sits in 9:30–9:45, not in the morning.

Sentence 1 ✓ · 2a ✓ · **2b ✗** (night difference 5.3 bp < 8) → dead by the letter. The clause had been calibrated from the paper's *index* number (18.5 bp) and applied to an ES 18:00 window on 2010–21 — a threshold-calibration error, the second of the same type that day (case 13 top-5 clause). The payer was alive; the file was not. Hence 14b.

**Case 14b — OOS 2022-01 → 2026-07, one look, net bp**

| | n | V1 net | t (HAC) | hit rate | top-5 share | night | day short | 9:30→9:45 | quarterly | other months |
|---|---|---|---|---|---|---|---|---|---|---|
| ES expiry days | 55 | **+3.17** | **0.30** | 51 % | 449 % | −1.9 | +6.3 | +4.7 | −5.7 (n 18) | +9.2 |
| ES other Fridays | 182 | −5.5 | | | | −2.2 | −3.3 | | | |
| NQ expiry days | 55 | +15.4 | 1.13 | 60 % | 145 % | +1.2 | +15.4 | +9.8 | −1.1 | +25.2 |
| NQ other Fridays | | | | | | −5.4 | −4.5 | | | |

ES by year, net: 2022 +39.3 · 2023 +8.4 · 2024 −33.4 · 2025 +20.4 · 2026 −34.6. NQ: +57.6 · +17.0 · −25.8 · +52.4 · −52.6. Recency 2025–26 ES (n 19): +1.3. Pooled ES+NQ (n 110): +9.3, t 1.09.

Sentence 1 ✗ (3.17 ≤ 3.6) · 2 ✓ (control negative) · 3 ✗ (t 0.30) → **dead**.

---

## Verdict

In-sample the paper replicates in ES at roughly half its index magnitude (night +7 vs +18.5), with the quarterly expiries carrying most of it. Out-of-sample the **night leg has vanished** (−1.9 on expiry days vs −2.2 otherwise), the quarterly pattern has reversed sign, years alternate by ±35 bp, and only the 15-minute reversal after the open survives at a size that twelve events a year cannot turn into a tradable leg. NQ looks better (+15.4) but five days carry 145 % of the sum and t is 1.13. The paper's sample ends in 2021; it appeared in 2023. Whether arbitrage after publication, the 0DTE structural shift, or changed dealer behaviour — the payer stopped buying at night.

---

## What I learned

- A mechanism with t > 4 over 19 years can stop in the year after its paper is published. "When does the sample end?" is the first question, not the last; the gap between sample end and today is the real out-of-sample test, and it must be run before anything else.
- The night part of a settlement constraint is the arbitrageable part — whoever knows it buys earlier. The post-open reversal lives longer, but it is a 15-minute event, too small and too noisy at twelve events a year.
- Thresholds only from the own instrument, window and sample. A kill clause calibrated from the paper's index numbers killed a file whose effect was present (case 14), which cost a second file to repair. Now written into the template: one size criterion (3 × cost), controls as ratios, every clause with its sample stated.
- Read-across: Cboe's daily a.m.-settled SPX options (SPXO, launching November 2026) create the same settlement mechanics every day. Data collection from launch; expectations dampened by this result; hypothesis only with an own number, 2027.
