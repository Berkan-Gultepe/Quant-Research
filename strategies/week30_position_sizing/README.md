# Week 30 — Position Sizing & Risk

Die Positionsgrößen- und Risiko-Werkzeuge der Woche, angewandt auf **TSMOM v3**
(die handelbare, gecappte Version — siehe [`../tsmom_v3`](../tsmom_v3)).

Beide Skripte importieren die Strategie-Logik aus `tsmom_v3` — **nicht dupliziert**,
eine Quelle der Wahrheit.

## `kelly.py` — wie groß?

`f* = μ/σ² = Sharpe/σ` — der optimale Hebel für maximales log-Wachstum.

- Vorteil skaliert **linear** mit `f`, Volatilität **quadratisch** mit `f²` →
  die Wachstumskurve ist **unsymmetrisch**: links ein sanfter Hang, rechts eine
  Klippe. Doppelt so viel setzen wie `f*` löscht den **gesamten** Vorteil (`g = 0`).
- Deshalb ist **Half-Kelly Logik, nicht Vorsicht**: symmetrisch unsicheres μ trifft
  eine asymmetrische Strafe.
- `f* ≈ 8×` — Kelly sagt *mehr* Risiko wäre möglich. Was bindet, ist nicht das
  Risiko, sondern die **Finanzierbarkeit** → der 10×-Cap aus v3. **Bruttonominal
  ist nicht Risiko.**

→ schreibt `kelly_curve.png`

## `risk_metrics.py` — wie schlimm der schlechte Fall?

**VaR = die Tür** (*wo* fängt der schlechte Bereich an), **CVaR = der Raum dahinter**
(*wie tief* im Schnitt). `CVaR = E[X | X ≤ VaR]`, immer `≥ VaR`.

| Niveau | VaR (z) | CVaR = φ(z)/(1−α) |
|---|---|---|
| 95% | 1,645 → ~0,80%/Tag | 2,063 → ~1,01%/Tag |
| 99% | 2,326 → ~1,14%/Tag | 2,665 → ~1,31%/Tag |

**Der eigentliche Test:** *parametrisch* (Glockenkurve) vs. *empirisch* (echte
schlechteste Tage). Klaffen sie auseinander, sind die Schwänze **fetter als
normal** → der parametrische VaR/CVaR **unterschätzt** das Crash-Risiko (der
2008-Fehler). Das Skript druckt beide plus Skew und Exzess-Kurtosis und fällt ein
Urteil.

**Ergebnis (gemessen):**

| | CVaR₉₅ | CVaR₉₉ |
|---|---|---|
| parametrisch (normal) | 1,00% | 1,29% |
| **empirisch (echt)** | 1,14% | **1,74%** |

Verhältnis empirisch/parametrisch (99%) = **1,34** → die Normalformel
**unterschätzt den echten schlimmen Tag um ~34%**. Exzess-Kurtosis **+3,08**
(fette Schwänze), Skew **−0,23** (leicht negativ — *nicht* das oft behauptete
positive Trend-Skew; das mostly-long-Portfolio erbt die Abwärts-Schiefe des
Marktes). **Für Kill-Switch/Sizing gilt der empirische CVaR, nicht der
parametrische.**

→ schreibt `risk_dist.png`

## Drawdown-Metriken

Calmar (0,27) und Ulcer (5,82) stecken schon in [`../tsmom_v3`](../tsmom_v3)
(`drawdown_metrics`). Merke: Calmars MaxDD-Nenner ist **n = 1** (wackelt); Ulcer
und CVaR nutzen **alle** schlechten Tage → stabiler.

## Reproduzieren

```bash
python kelly.py
python risk_metrics.py
```

Daten live von Yahoo Finance, kein API-Key. Braucht `../tsmom_v3/tsmom_v3.py`.

## Ehrliche offene Punkte

- **5 bp Kosten sind eine Annahme, keine Messung** (wie in v2/v3).
- **Empirischer CVaR** ist der ehrliche Tail — falls er den parametrischen deutlich
  übersteigt, ist die Normalverteilungs-Annahme in VaR/CVaR zu optimistisch.
- Portfolio-Cap (alle 24 long) und Finanzierungskosten des Hebels bleiben offen
  (siehe v3-README).
