# Young single-stock leveraged ETFs — testing the "payer pays for two years" thesis

**Status: ⚰️ Thesis refuted in one pre-registered look — five funds launched 2022–2026 (MU, INTC, SNDK, MSTR, COIN; two of them $3–5 bn) leave nothing in the closing window during their first 24 months: +3 bp gross, t 0.2, control days carry more than signal days. Case 18's in-sample was an episode, not a rule.**
**Case 19 | October 2026 | eleventh run · out-of-sample test of the lifetime thesis from case 18 · placebo per name from its own listing date**

---

## Why this one

Case 18 found that TSLA/NVDA 2× funds paid for the close in 2022–24 (+19 bp, close gaining 24 bp relative to the pre-window, next-morning reversal) and were served rather than paid from 2025 on. Together with cases 6 (Nasdaq-100 LETFs, dead from 2019) and 14b (SPX a.m. settlement, dead from 2022), that suggested a rule: a known closing flow in US names has a half-life of about two years, so *young* funds should still pay. Five large single-stock funds with verifiable listing dates make that a one-look test: MUU on MU (10/2024, $5.0 bn), INTW on INTC (2/2025), SNXX on SNDK (1/2026, $2.9 bn), MSTX/MSTU on MSTR (8–9/2024), CONL on COIN (8/2022 — the one name that has lived through both phases).

---

## Pre-registration (written before buying the data)

Per name: placebo = everything before the first 2× fund; build-up = listing + 0–3 months (excluded); young = +3 → +24 months; old = beyond. Thresholds (top-quintile |r| from prior close to 15:30, and the median for the control) taken **from each name's placebo only**. Window 15:30 → official close (closing cross). One variant. Thesis confirmed if young-phase pooled net ≥ 6 bp, control < 50 %, t (HAC) ≥ 3.3 **and** COIN-old ≤ 0; refuted if any of the first three fails; undecided if young passes but COIN-old > 0. Readings: per name, close minus pre-window, next-morning reversal, a decay curve by fund age.

---

## Results (Databento XNAS.ITCH 1-min, 3.0 M bars, $3.01)

Auction share of the 16:00 bar: INTC 35 %, MU 24 %, SNDK 21 %, MSTR 16 %, COIN 14 %. Only split: MSTR 10:1 on 2024-08-08. Inject +10 → 10.00.

| block | days | V1 n | gross | net | σ | t HAC | hit | top-5 | control | pre-window | **close − pre-window** | next morning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| placebo (before listing, 5 names) | 5,367 | 1,076 | +4.6 | +2.6 | 105 | 0.64 | 49 % | 120 % | −0.6 (−14 %) | +29.4 | **−24.8** | +2.2 |
| **young** (+3 → +24 months) | 1,760 | 559 | **+3.1** | **+1.1** | 106 | **0.20** | 53 % | 287 % | +4.4 (**141 %**) | +12.6 | **−9.5** | +6.0 |
| old (COIN from 9/2024, MSTR from 9/2026) | 565 | 96 | −4.2 | −6.2 | 96 | −0.61 | 47 % | — | +0.8 | +20.1 | −24.3 | +12.2 |

Young phase by name: COIN +12.6 (t 0.9) · INTC +4.1 (t 0.3) · MSTR −7.0 · MU +2.0 (t 0.0) · SNDK +10.3 (n 37). Decay curve by fund age (net / close − pre-window): 0–3 m +1.7/−21 · 3–6 −7.9/−41 · 6–12 +5.5/+1 · 12–18 −3.0/−17 · 18–24 +7.8/+13 · 24–36 −0.9/−25 · 36–60 −12.7/−24 — no hill, no decay, noise.

Sentences 1 ✗ · 2 ✗ · 3 ✗ · COIN-old ≤ 0 ✓ (moot). **Thesis refuted.** Placebo +4.6 vs young +3.1: no difference with or without the fund.

---

## Verdict

Funds launched from 2024 on leave nothing in the close from their first months — neither in level nor in the two fingerprints that identified the payer in case 18. The only faint echo is COIN's young phase (2022–24, the same era as TSLL): +12.6 bp at t 0.9. The lifetime of a known closing flow is not two years; it is the time the other side needs to learn it, and that learning happened once, on TSLA in 2023–24. Since then every new fund is served from day one. Korea 2026 was a market without that learning curve, not evidence for the US.

---

## What I learned

- The leveraged-ETF rebalancing family is now measured end to end and closed: Nasdaq-100/S&P (case 6, dead from 2019), Nikkei via NKD (case 16, a proxy, 6 bp), silver (Todorov, n.s. to 2020), natural gas (costs), TSLA/NVDA (case 18, alive 2023–24, dead from 2025), young funds (case 19, never there). One living patch in seven measurements, and it is over.
- The decay rule from case 18 is corrected: **once the counterparty has learned a type of flow, new instances of it decay immediately.** The pre-gate decay check now asks whether the other side has already learned this *type*, not whether this *fund* is new.
- A thesis born from one episode gets tested before it becomes a rule. This one cost $3 and twenty minutes and would otherwise have shaped the next year's search.
- Prior written before the look: 45 %. Too high; after case 18's out-of-sample the honest number was 25 %.
