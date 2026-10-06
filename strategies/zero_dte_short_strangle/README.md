# 0DTE variance risk premium — short SPXW strangle ±1 %, 10:00 → settlement

**Status: ⚰️ Dead at gate 5 — the premium is collected (3.9 index points a day, 87 % winning days) and almost entirely handed back on the 16 % of days that pay out: +0.39 points net per day, S/T 0.034, t 0.9. Not a tail problem — the tail clause passed — a pricing problem: at this moneyness the 0DTE strangle is nearly fair.**
**Case 20 | October 2026 | own data (ThetaData SPXW trade+NBBO, SPX 1-second) · the twentieth case of the year, hurdle 3.6 · a documented risk premium, not a forced flow**

---

## Why this one

Zero-day SPX options are the most-traded contract in the world and their buyers are, in the literature and in my own August 2026 measurement, systematic overpayers: far out-of-the-money puts trade at up to 8× fair value, with seller margins of 24–87 % by moneyness bucket. The variance risk premium itself is documented since Bakshi & Kapadia (2003) and Carr & Wu (2009). The open question from August was the *seller's* P&L distribution — does the premium survive the days it pays out?

---

## Pre-registration (written before computing a single P&L)

Sell one SPXW 0DTE strangle at 10:00 ET — put at the nearest 5-point strike to spot × 0.99, call at spot × 1.01 — **at the bid**, hold to settlement (SPX close), 2 × $1.30 commission. One variant. IS 2022-05 → 2024-06, OOS 2024-07 → 2026-08 one look. Dead if: IS net ≤ 0.10 pts/day · **IS Calmar (annual net ÷ max drawdown) < 0.5** · t (HAC) < 3.6 · OOS net ≤ 0 or OOS drawdown > 2 × IS drawdown. Prior written before the look: 35 %, revised to 18 % before the look because the OOS contains 9 April 2025 (+9.5 %) — a day that costs a +1 % call about a year of premium.

---

## Data and build

1,068 expiry days, quotes at 10:00 from the first trade in 10:00–10:10 at the target strike (one missing, 15 neighbour strikes), median lag 0 minutes, median spread 0.10 (put) / 0.05 (call) points. **Median premium 1.95 points per strangle (put 1.45, call 0.45)** — 0.04 % of the index. Settlement = last SPX 1-second print (on early-close days the series is stale after 13:00, so the last print is the correct settlement). Inject +1 → 1.00. Hand checks: 13 Oct 2022 (CPI reversal, call pays 104.6, net −90.8), 13 Mar 2023 (SVB Monday, premium 19.5 kept), 15 Apr 2024 (put pays 53.8, net −51.9).

---

## Results — IS 05/2022–06/2024, n 534

| net/day | median | σ | S/T | t HAC | hit | PF | annual net | max DD | Calmar | worst 5 days | put leg | call leg | payout days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **+0.39** | +1.20 | 11.2 | **0.034** | **0.90** | 87 % | 1.15 | +96 | −135 | **0.71** | −367 (all 2022) = 178 % of the pot | +0.22 | +0.19 | 16 % |

By realized daily range: calm +0.95 · mid +2.87 · wild −2.66. By year: 2022 +0.69 · 2023 +0.33 · 2024 +0.11.

Sentence 1 ✓ · 2 ✓ (Calmar 0.71) · **3 ✗ (t 0.90)** → dead. OOS not opened.

---

## Verdict

The strangle collects 3.9 points gross and keeps 0.39: 16 % of days return the premium, and the five worst days (all in 2022) exceed the whole pot. That is not a fat tail wrecking a good trade — the drawdown is small (Calmar 0.71 passes) because the pot is small. It is a nearly fair price. A signal-to-noise of 0.034 per day would need about 11,000 days (45 years) to reach t 3.6. The premium also shrinks year by year, consistent with the growth of option-selling funds since 2023. The August finding stands as a *price* finding — far-OTM puts are overpriced — but ±1 % is roughly one daily sigma for a 0DTE at 10:00, not far out; further out the premium is 0.05–0.20 points with spreads of 30–50 % of it and payoff-to-premium ratios in the thousands. Mispricing that cannot be harvested at tradable moneyness.

---

## What I learned

- A price finding is not a P&L finding. For premia the pre-gate size question is not premium ÷ cost but **expected net premium after payouts ÷ daily σ**, and S/T × √n against the hurdle — the same certifiability test that killed case 15 before data, here settled with own numbers.
- The second admissible class in my template (documented risk premia) meets the same wall as forced flows in US closing windows: too many counterparties. The 0DTE premium has been hunted since 2023; what remains is fair.
- Calmar passing on a small pot is not quality. S/T and n are.
- The raw data lived on an external drive that threw I/O errors mid-build; the data are irreplaceable (subscription cancelled). Back up before computing — now a rule in the data catalogue.
