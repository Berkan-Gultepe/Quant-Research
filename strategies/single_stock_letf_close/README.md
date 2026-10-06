# Single-stock leveraged-ETF rebalancing into the closing auction — TSLA, NVDA

**Status: ⚰️ Dead at gate 6 — in-sample (Aug 2022–2024) the payer is there with every pre-registered fingerprint (+19 bp gross, t 3.5, close gains 24 bp relative to the half hour before it, next-morning reversal); out-of-sample (2025–Oct 2026) the same flow is larger than ever and the closing window has turned *negative*. The flow is now being served, not paid for.**
**Case 18 | October 2026 | eleventh run · prospectus-anchored · placebo before the funds existed · gates 1–6 walked one by one**

---

## Why this one

2× single-stock leveraged ETFs on Tesla (TSLL $3.9–5.0 bn, TSLR, TSLT) and Nvidia (NVDL $3.9 bn) must reset exposure to target leverage every day; they hold swaps, and the dealers hedge in the stock into the closing auction that sets the NAV reference. Daily demand is L(L−1)·AUM·r (Todorov 2024): for TSLA roughly $15–19 bn × the day's return — on a 5 % day $0.8 bn into a closing auction of $2–3 bn, a quarter to a third of it. Korea's single-stock LETF episode of May–July 2026 (arXiv 2608.03703, "Preying on Leveraged ETFs") showed the same mechanism moving a whole market within weeks. After cases 16 and 17 died on *flow ÷ window liquidity*, this was the highest such ratio I knew of. Not a prop-firm leg (the stocks and their CME futures are on no prop list); an own-account candidate.

---

## Pre-registration (written before buying the data)

On days where the stock has moved from the prior official close to 15:30 ET by more than the top-quintile threshold of |r| (set in-sample, per stock), the stock moves from 15:30 to the official close (closing cross) in the direction of the day's return by ≥ 6 bp net (3 × 2 bp). One variant, pooled TSLA + NVDA, pooled t as the gate-5 metric. Dead if: IS (TSLA from 2022-08-09, NVDA from 2022-12-13, to 2024-12-31) pooled net < 6 bp · control (bottom half of |r|) ≥ 50 % of V1 · t (HAC) < 3.3 · OOS 2025-01 → 2026-10 one look, net ≤ 0. **Placebo (mandatory):** both stocks before their first leveraged fund existed. Pre-registered readings to separate a payer from plain intraday momentum: the 15:00–15:30 pre-window, and the next morning 9:30–10:00 (Korea's prediction: an auction overshoot reverses).

---

## Parameters

| Parameter | Value |
|---|---|
| Data | Databento XNAS.ITCH 1-min OHLCV, TSLA + NVDA, 2018-05 → 2026-10, 1.67 M bars (09:30–16:05 ET), $2.14 |
| Official close | the 16:00 bar (closing cross is in the feed: 15.4 % of daily volume in that single bar) |
| Exclusions | half days (18 per stock, detected by post-13:00 volume < 5 %), split days (NVDA 2021-07-20, 2024-06-10; TSLA 2020-08-31, 2022-08-25) |
| Signal | r_day = prior close → 15:30; V1 = top quintile of |r| (IS): TSLA ≥ 410 bp, NVDA ≥ 338 bp |
| Cost | 2 bp round trip assumed (MOC order; spread 0.2–0.6 bp) |
| Validation | inject +10 bp → 10.00 · hand checks TSLA 2020-09-08, 2024-10-24, NVDA 2024-08-29 |

---

## Results

| block | days | V1 n | gross | net | σ | t HAC | hit | top-5 | TSLA / NVDA | long / short | control | pre-window | **close − pre-window** | next morning |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| placebo (before the funds) | 2,213 | 512 | +7.2 | +5.2 | 107 | 0.99 | 56 % | 74 % | +5.0 / +9.1 | — | +2.1 (29 %) | +27.3 | **−20.1** | +9.2 |
| **IS** listing → 2024 | 1,105 | 222 | **+19.2** | **+17.2** | 67 | **3.54** | 59 % | 24 % | +23.9 (t 3.5) / +13.7 (t 1.8) | +14.9 / **+26.0** | +1.4 (7 %) | +15.3 | **+3.9** | **−12.8** |
| **OOS** 2025 → Oct 2026 | 872 | 153 | **−9.2** | **−11.2** | 74 | **−1.42** | 54 % | — | −14.2 (t −1.6) / −3.6 | −6.2 / **−24.2** (TSLA) | −0.2 (2 %) | +15.8 | **−25.0** | −10.4 |

Gate 3: median +20, quartiles −26/+62, skew −0.2, AC(1) +0.10, stationary. Gate 4 (IS): PF 1.96, max DD −585 bp (15 % of the pot), S/T per trade 0.26 (TSLA 0.34, short side 0.34). Gate 5: t 3.54 vs hurdle 3.3 (18th case of the year), passed. Gate 6: OOS net −11.2; 2025 −14.6 (n 105), 2026 −3.9 (n 48); IS+OOS pooled +5.6, t 1.2. Dead.

---

## Verdict

In-sample the payer is real, and it is identified by shape, not just level: relative to the half hour before it, the closing window gained 24 bp once the funds existed (placebo −20 → IS +4), and the auction's move reversed the next morning (+9 → −13) — an overshoot from mechanical demand, exactly as the Korean episode predicts. Out-of-sample the demand is larger than ever (TSLL has grown fivefold) and the closing window is negative: the pre-window momentum is unchanged (+16), the close is −9, the short side −24. The flow did not disappear; it is being served. Market makers and arbitrageurs position into 15:30 and take the other side of the fund in the auction, collecting the premium the fund paid in 2023–24. A change in the issuers' execution after the 2024–25 scrutiny would produce the same picture. The next-morning reversal persists (−10) because the auction still overshoots — now the other way.

---

## What I learned

- **Known closing flows in large US names have a half-life of about two years.** Case 6 (Nasdaq-100 LETFs: alive 2010–18, dead from 2019), case 14b (SPX a.m. settlement: alive to 2021, dead from 2022), case 18 (alive 2022–24, reversed from 2025). Same pattern three times. The decay check now carries a number: a US close-flow mechanism counts as decay-prone once it has been public for two years, and the out-of-sample must contain the years after that.
- Korea (weeks old) was the wrong analogue for the US (years old): predators amplify in young markets and absorb in mature ones. My own graveyard was the right prior; I reached for the exciting one instead. Prior written before the data: 50 % alive, 75 % conditional on IS — the second number was wrong, on the lifetime of the effect, not its existence.
- The two pre-registered readings — close minus pre-window, and next-morning reversal — separate a payer from momentum *in both directions*: they established the payer in-sample and showed its absorption out-of-sample. They belong in every close-flow pre-registration.
- Where the mechanism goes next: new single-stock leveraged funds in their first 12–24 months, before the hunters are positioned. One dollar of data per name.
