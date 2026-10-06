# Vol-control rebalancing into the ES close — S&P Risk Control rule

**Status: ⚰️ Dead at gate 2 — the flow has the shape of a forced trade (control zero, deleveraging > releveraging, nothing in the half hour before) but leaves 2 bp gross in the most liquid 30 minutes in the world, carried by five days, with more of it showing up the day *before* than in the window itself.**
**Case 17 | October 2026 | eleventh run · rule-anchored (public index methodology) · zero data cost**

---

## Why this one

Products linked to S&P Risk Control indices (fixed index annuities, structured notes) must set their equity weight every day to *target volatility ÷ realized volatility*, rebalanced at the close. The rule is public (S&P Risk Control methodology: EWMA decay 0.94/0.97, two-day lag, cap 150 %), so the daily weight change Δw is computable from index closes two days ahead. Sell-side estimates put vol-control AUM at $300–500 bn "predominantly expressed through S&P 500 futures"; February 2018 saw $50–100 bn sold in 48 hours. A mechanical payer, daily, conditional on volatility changes — different days from my month-end legs, inside the prop-firm session, on ES. The one box candidate my own data could test for free.

---

## Pre-registration (written before computing the signal)

Signal: w_t = min(1.5, 0.10 / σ_{t−2}), σ = max(EWMA_0.94, EWMA_0.97) of same-contract ES daily close returns, annualized; Δw_t = w_t − w_{t−1}. V1 = top quintile of |Δw| (threshold from IS), direction sign(Δw), ES 15:30 → 16:00 ET. One variant. Dead if: IS 2013–2018 net < 1.8 bp (3 × 0.6) · control (bottom half of |Δw|) ≥ 50 % of V1 · t (HAC) < 3.3 · OOS 2019–2026 one look, net ≤ 0. Placebo 06/2010–2012 (risk-control products still small). Pre-registered readings: deleveraging vs releveraging, the same window on t−1 (sunshine test), the 15:00–15:30 pre-window (panic vs close-specific flow).

---

## Results (data: `k1_schluss_tage`, 3,922 days)

Signal sanity: median weight 0.73, cap binding on 2 % of days; V1 threshold |Δw| ≥ 2.0 percentage points ≈ $8 bn at $400 bn AUM. Inject +10 bp → 10.00.

| block | V1 n | gross | net | σ | t HAC | hit | top-5 | Δw<0 / Δw>0 | control | t−1 window | 15:00–15:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| placebo 2010–12 | 75 | +6.9 | +6.3 | 33.8 | 1.03 | 52 % | 108 % | +9.2 / −0.9 | −0.2 | −3.3 | −4.8 |
| **IS 2013–18** | 291 | **+2.1** | **+1.5** | 23.7 | **1.18** | 53 % | **117 %** | +4.2 / −0.2 | +0.1 | **+3.0** | −0.4 |

IS by year, net: 2013 +2.6 · 2014 +4.5 · 2015 +1.1 · 2016 −2.7 · 2017 +0.5 (n 96) · 2018 +1.8. Placebo is August 2011 (the downgrade Monday: Δw −18 pp, close −161 bp).

Sentence 1 ✗ · 2 ✓ · 3 ✗ → dead. OOS not opened.

---

## Verdict

The shape is right and the size is not. Control days carry nothing, the half hour before the window carries nothing, and deleveraging days move the close more than releveraging days in both samples — exactly what a close-of-day rebalance should look like. But $8 bn into ES's closing half hour is 5–8 % of its volume, and the market absorbs that for about 2 bp, with the pot in five days. Worse, the same window on the day *before* carries +3 bp: a flow known two days ahead gets traded a day early. Prior probability I wrote before the signal: 25 %.

---

## What I learned

- Two cases in one night, one lesson from both sides: case 16 (Nikkei leveraged ETFs) had a large payer and a damped proxy instrument; case 17 has a large payer and an instrument too liquid to dent. **The effect is flow ÷ window liquidity, not flow.** Pre-gate question 4 now needs the denominator — the instrument's volume in the window, not the day.
- "Known shortly before" is not a soft criterion. A flow known two days ahead shows up on t−1.
- The data on my disk are now exhausted for box legs: ES/NQ close flows (cases 3, 6, 17), ES nights (8, 14), ES calendar (7 alive, 15), FX (A), Treasuries (13 alive), NKD (16). Anything else on the listed instruments needs new data (CL, RTY) or new products (SPXO, November 2026).
