# Nikkei leveraged-ETF rebalancing into the Osaka close — NKD, 15-minute window

**Status: ⚰️ Dead at gate 2 — the mechanism is real (placebo zero, in-sample +6 bp gross with every signature of a forced flow) but too small on the instrument I can trade: 6 bp gross against 3 bp cost, t 1.8. Out-of-sample never opened.**
**Case 16 | October 2026 | eleventh run · central-bank-anchored · pre-registered placebo period before the payer existed**

---

## Why this one

Nomura's Nikkei 225 leveraged ETFs — 1570 (2×, ¥600–725 bn) and 1357 (−2×, ¥64 bn) — must reset their futures exposure to the target leverage every day and do so into the Osaka closing auction. The Bank of Japan (Review 2016-E-1) measured that in 2015 this rebalancing demand "often exceeds 20 percent of the trading volume" in the closing window and that Nikkei futures "tend to rise/fall between 15:00 and 15:15 on days during which the Nikkei 225 rose/fell until 15:00". Japan's leveraged-ETF share of the equity market was about four times the US share. Daily, conditional on the day's move, inside the prop-firm session (01:30–02:45 ET), on a listed contract (NKD) — the first candidate with its own trading days rather than another month-end leg.

Fund demand per day = L(L−1)·AUM·r (Todorov 2024), so both the bull and the bear fund trade in the direction of the day's return: about ¥17 bn per 1 % move today.

---

## Pre-registration (written before buying the data)

Hypothesis: on days where the Nikkei — measured on the NKD front contract — moved from the prior day's Osaka auction to the cash close by more than the top-quintile threshold of |r| (set in-sample), NKD moves in the direction of the day's return from the cash close to the futures auction (15:30→15:45 JST; 15:00→15:15 before 5 Nov 2024) by at least 9 bp net (3 × 3 bp cost). One variant. Dead if: IS 04/2012–2018 V1 net < 9 bp · control (bottom half of |r|, same rule) ≥ 50 % of V1 · t (HAC) < 3.3 · OOS 2019–2026 one look, net ≤ 0.

**Placebo (gate 6b, mandatory):** NKD 06/2010–03/2012, before 1570 was listed (April 2012) — same market, same window, no payer. Expected ≈ 0.

---

## Parameters

| Parameter | Value |
|---|---|
| Instrument | NKD (CME Nikkei 225/USD), Databento GLBX 1-min OHLCV 2010-06 → 2026-10, 3.81 M bars, 40 contracts |
| Front | highest day-session volume (08:45–15:45 JST) |
| Day table | 4,198 weekdays → 3,815 after removing Japanese holidays/thin days (278), contract switches (71), gaps |
| Prices | prior auction (15:14 / 15:44 JST close), cash close (14:59 / 15:29), auction (15:14 / 15:44); regime break 2024-11-05 |
| Signal | r_day = prior auction → cash close; V1 = |r_day| ≥ 149 bp (top quintile, IS) |
| Cost | 3 bp round trip (NKD tick 5 pts = 1.1 bp) |
| Validation | inject +10 bp → 10.00 · hand checks 2011-03-15 (−983 bp day, window +76), 2011-08-09, 2013-05-23 |

---

## Results

| block | days | V1 n | gross | net | σ | t HAC | hit | long / short | control (|r| ≤ median) | quintiles Q1→Q5 (gross) |
|---|---|---|---|---|---|---|---|---|---|---|
| **placebo** 06/2010–03/2012 | 251 | 62 | **+1.1** | −1.9 | 23.9 | −0.88 | 44 % | −0.1 / +2.4 | +2.4 | 4.0 · −0.2 · 1.3 · −1.1 · 1.1 |
| **IS** 04/2012–2018 | 1,598 | 320 | **+6.2** | **+3.2** | 25.1 | **1.80** | 55 % | +6.8 / +5.5 | +0.7 (12 %) | −2.5 · 3.0 · 1.5 · 3.7 · **6.2** |

IS by year, net: 2012 −0.5 · 2013 +4.7 · 2014 −2.9 · 2015 +3.5 · 2016 +7.9 · 2017 +0.7 · 2018 +2.8. Top-5 share 38 %.

Sentence 1 ✗ (3.2 < 9) · 2 ✓ · 3 ✗ (t 1.8) → dead. Placebo confirmed (≈ 0 gross, 18 % of IS). OOS not opened.

---

## Verdict

The flow leaves every fingerprint a forced trade should: nothing before the fund existed, +6 bp after; the control days carry 12 % of it; both sides pay; the effect rises monotonically with the size of the day's move (as the mechanism predicts); no single day dominates. It is simply too small on NKD: a cost ratio of 2 and a t of 1.8 at n 320. The BoJ's chart implies ≥ 15 bp at 1.5 % moves; NKD shows less than half. The likely reason is that NKD is a USD-quanto proxy with no auction of its own — the Osaka auction spike arrives in Chicago damped and partly reversed. The out-of-sample years stay sealed for a possible successor measured on Osaka data.

---

## What I learned

- A central bank's chart of the home market is not a number for the proxy. Pre-gate question 6 ("does the flow go through the instrument?") now has a rider: through *this* instrument, or through one this instrument is merely coupled to? Coupling damps.
- A placebo period before the payer existed is the cleanest pre-sample I have run: zero without the fund, six with it. Wherever a payer has a birth date, the placebo goes in the pre-registration.
- My prior was 70 % for the in-sample passing; it failed on size, not on existence. The series continues with crude oil (UCO/SCO rebalance directly in CL futures — no proxy), at a lowered prior.
