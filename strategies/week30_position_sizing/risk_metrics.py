"""
VaR & CVaR für TSMOM v3  —  parametrisch vs. empirisch
======================================================
KW30 · Positionsgröße & Risiko

VaR  = die TÜR:  "an X% der Tage verliere ich nicht mehr als Y%."   z * sigma_Tag
CVaR = der RAUM dahinter:  der DURCHSCHNITT der Verluste JENSEITS der Tür.
       CVaR = E[X | X <= VaR].  Immer >= VaR.

Warum der Durchschnitt und nicht der eine schlimmste Tag? Der einzelne Worst-Case
hat die n=1-Schwäche wie Calmars MaxDD-Nenner — ein Ausreißer kippt ihn. CVaR
nutzt ALLE Tail-Tage → stabil und misst die Tiefe.

Der ehrliche Test (der eigentliche Punkt dieser Datei):
    PARAMETRISCH  nimmt eine Glockenkurve an (Multiplikatoren unten).
    EMPIRISCH     nimmt die ECHTEN schlechtesten Tage — keine Annahme.
Klaffen sie auseinander, sind meine Schwänze FETTER als normal → der
parametrische VaR/CVaR UNTERSCHÄTZT mein echtes Crash-Risiko (der 2008-Fehler).

Normal-Multiplikatoren:
    Niveau   VaR (z)   CVaR = phi(z)/(1-alpha)
    95%      1.645     2.063
    99%      2.326     2.665

Run:  python risk_metrics.py   ->  druckt Vergleich, schreibt risk_dist.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tsmom_v3"))
from tsmom_v3 import load_data, net_returns

PURPLE, GREEN, RED, GREY = "#7c3aed", "#16a34a", "#dc2626", "#64748b"

# Normal-Multiplikatoren: (z fuer VaR, phi(z)/(1-alpha) fuer CVaR)
MULT = {0.95: (1.645, 2.063), 0.99: (2.326, 2.665)}


def parametric(sigma_d, alpha):
    z, c = MULT[alpha]
    return z * sigma_d, c * sigma_d          # VaR, CVaR (als positive Verluste)


def empirical(net, alpha):
    q    = np.quantile(net, 1 - alpha)        # z.B. 5%-Quantil (negativ)
    var  = -q
    tail = net[net <= q]                      # die schlechtesten (1-alpha) Tage
    cvar = -tail.mean()
    return var, cvar


def main():
    close, log_returns = load_data()
    net, _, _ = net_returns(close, log_returns)
    sigma_d = net.std()

    print(f"Tages-Vol sigma_Tag : {sigma_d*100:.3f} %   "
          f"(= {sigma_d*np.sqrt(252)*100:.2f} % p.a. / sqrt(252))")
    print(f"Schiefe (Skew)      : {stats.skew(net):+.2f}   "
          f"(> 0 = positiv, trendtypisch)")
    print(f"Exzess-Kurtosis     : {stats.kurtosis(net):+.2f}   "
          f"(0 = normal; > 0 = fette Schwänze)")
    print("-" * 64)
    print(f"{'Niveau':>7} | {'VaR param':>9} {'VaR emp':>9} | {'CVaR param':>10} {'CVaR emp':>9}")
    print("-" * 64)
    for a in (0.95, 0.99):
        vp, cp = parametric(sigma_d, a)
        ve, ce = empirical(net, a)
        print(f"{a*100:6.0f}% | {vp*100:8.2f}% {ve*100:8.2f}% | "
              f"{cp*100:9.2f}% {ce*100:8.2f}%")
    print("-" * 64)

    # Diagnose Fatter-Tails am 99%-CVaR
    _, cp99 = parametric(sigma_d, 0.99)
    _, ce99 = empirical(net, 0.99)
    ratio = ce99 / cp99
    verdict = ("FETTE SCHWÄNZE — Normal unterschätzt den Tail"
               if ratio > 1.15 else
               "grob normal — die Glocke taugt hier")
    print(f"empirischer / parametrischer CVaR₉₉ = {ratio:.2f}  ->  {verdict}")

    # --- Verteilung zeichnen mit VaR/CVaR-Linien (95%) ---
    vp, cp = parametric(sigma_d, 0.95)
    ve, ce = empirical(net, 0.95)
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(net * 100, bins=120, color=PURPLE, alpha=.55, density=True)
    ax.axvline(-ve * 100, color=RED,   ls="--", lw=1.5, label=f"VaR₉₅ (emp) = {ve*100:.2f}%")
    ax.axvline(-ce * 100, color="#7f1d1d", ls="-", lw=1.8, label=f"CVaR₉₅ (emp) = {ce*100:.2f}%")
    ax.axvline(-vp * 100, color=GREY,  ls=":",  lw=1.2, label=f"VaR₉₅ (normal) = {vp*100:.2f}%")
    ax.set_xlim(net.quantile(0.002) * 100, net.quantile(0.998) * 100)
    ax.set_title("TSMOM v3 — Tagesrenditen mit VaR/CVaR (95%)")
    ax.set_xlabel("Tagesrendite %"); ax.set_ylabel("Dichte")
    ax.legend(fontsize=8); ax.grid(alpha=.2)
    plt.tight_layout()
    plt.savefig("risk_dist.png", dpi=130, bbox_inches="tight")
    print("wrote risk_dist.png")


if __name__ == "__main__":
    main()
