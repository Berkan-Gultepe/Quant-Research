# Week 27 — Alternative Data & Macro Regime Filter

**KW27 | Juli 2026**

Research focus: incorporating alternative data (COT positioning, credit spreads, yield curve) as macro regime filters for systematic strategies.

---

## Files

| File | Description |
|------|-------------|
| `01_cot_zscore.py` | COT Commitment of Traders — Non-Commercial Z-Score signal for short/long squeeze detection |
| `02_makro_regime.py` | HY-Spread + Yield Curve regime classifier — empirical analysis 2005–2026 |
| `03_tsmom_with_macro_filter.py` | TSMOM baseline extended with macro regime filter |

---

## Key Findings

### Macro Regime (2005–2026, 773 trading days)

| Regime | Days | Mean Return/Day | Std | Worst Day |
|--------|------|----------------|-----|-----------|
| Risk-On | 453 | +0.096% | 0.80% | −2.95% |
| Risk-Off | 320 | +0.041% | 1.06% | −5.98% |

→ Risk-Off regime: **57% lower returns**, **32% higher volatility**

Risk-Off defined as: `HY_Spread > 4%` OR `Yield_2s10s < 0`

### COT Signal (KW27 readings)

| Instrument | Z-Score | Signal |
|-----------|---------|--------|
| Japanese Yen (6J) | −4.27σ | ⚠️ Extreme short squeeze risk |
| VIX Futures (VX) | −3.0σ | ⚠️ Short squeeze risk |

Short Squeeze Mechanism: speculators already max short → no sellers left → any trigger → forced covering → cascade buy → asset explodes up.

### Signal Hierarchy

```
① Yield Curve (T10Y2Y)   — Leading indicator, 6–18 month lead time
② HY-Spread              — Regime confirmation (coincident)
③ COT Z-Score            — Tactical timing
→ Conflicting signals = no trade
```

---

## Data Sources

- **FRED:** `BAMLH0A0HYM2` (HY Spread), `T10Y2Y` (Yield Curve)
- **CFTC:** Disaggregated COT Report (weekly, Tuesday data / Friday release)
- **Yahoo Finance:** `^GSPC`, ETF prices

---

## Dependencies

```
pip install yfinance pandas-datareader pandas numpy matplotlib
```
