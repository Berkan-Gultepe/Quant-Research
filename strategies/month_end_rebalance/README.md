# Month-End Rebalancing Flow — ES, last 10 minutes

**Status: ⚰️ Dead — [one half-sentence: why]**
**Case 2 | September 2026 | first full run through the 9-gate protocol**

---

## Why this one

[2–3 sentences: conditional hypothesis, pre-registered before any data, why month-end]

---

## Mechanism

[60/40 example in 3 sentences · why the flow runs *against* the month's return · why the last hour (benchmark = closing price → tracking error)]

---

## Pre-registration (written before touching the data)

- Dead if: [sentence 1 — net < 2 bp per trade]
- Dead if: [sentence 2 — sign not correct in *both* groups]
- Dead if: [sentence 3 — top-5 month-ends carry > 50 % of total]
- Dead if: [sentence 4 — 2023–2026 adjusted return ≤ 0]
- Threshold derived, not guessed: cost 0.7 bp × 3 = **2 bp** · noise 16 bp/trade → SE 1.16 bp at N 190 → detectable effect ≥ **3.5 bp**
- Splits: IS 2010–2019 / OOS 2020–2026 · variants counted: **1**

---

## Parameters

| Parameter | Value |
|-----------|-------|
| Instrument | ES futures, Databento GLBX 1-min OHLCV, June 2010 – July 2026 |
| Contract | front month = highest volume in the window, per day |
| Window | 15:50 open → 15:59 close, New York time (tz-aware, DST handled) |
| Condition | sign of the month's return measured up to 15:50 of the last trading day (no look-ahead) |
| Adjusted return | r × (−sign): after up-months the flow should be selling, after down-months buying |
| Cost | 0.7 bp round-trip (1 tick spread + commission) |
| Validation | inject test +10 bp → 9.99 recovered · 3 days checked by hand |
| N | 193 month-ends |

---

## Results

| Group | n | mean r (bp) | adjusted (bp) | expected sign |
|-------|---|-------------|---------------|---------------|
| after up-months (+1) | 128 | [−3.91] | [+3.91] | negative ✓ |
| after down-months (−1) | 65 | [−8.44] | [−8.44] | positive ✗ |
| **all** | 193 | [−0.25 gross / −0.95 net] | | |

[Pot, profit factor, max drawdown, worst / best month-end — one line]

![adjusted return](plots/monthly_adjusted_return.png)

---

## Verdict

[your verdict sentence, translated: metric vs. threshold → dead, scope (instrument · window · years · N), which pre-registered sentences fired, not Peso-driven]

---

## What I learned

- [both groups negative → the last 10 minutes fall on average regardless of month sign → new backlog card, post hoc, untested (NQ is not fresh data — correlation)]
- [protocol lesson: gate 4 must run on IS only — OOS was consumed here; fixed in the template]
- [one sentence on what the mechanism might mean: funds trade earlier / spread out / arbitraged ahead]
