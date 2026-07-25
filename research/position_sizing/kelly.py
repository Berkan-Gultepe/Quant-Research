"""
Kelly-Positionsgröße für TSMOM v3
=================================
KW30 · Positionsgröße & Risiko

f* = μ / σ² = Sharpe / σ      (optimaler Hebel für maximales log-Wachstum)

Kernpunkt (am Münzspiel hergeleitet): Vorteil skaliert LINEAR mit f, Volatilität
QUADRATISCH mit f² → die Wachstumskurve ist unsymmetrisch:
    links vom Optimum ein sanfter Hang, rechts eine Klippe.
Doppelt so viel setzen wie f* löscht den GESAMTEN Vorteil (g = 0).
Deshalb ist Half-Kelly Logik, nicht Vorsicht: symmetrisch unsicheres μ trifft
eine asymmetrische Strafe.

WICHTIG — Bruttonominal ist nicht Risiko: f* rechnet auf das GESAMTRISIKO des
Portfolios (Vol 7,74%), nicht auf das Bruttonominal einzelner Assets (bis 58×).
Kelly sagt "mehr Risiko möglich"; was bindet, ist die Finanzierbarkeit → der
10×-Cap aus v3 (siehe ../../strategies/tsmom_v3). Cap ist eine Nebenbedingung,
kein Kelly-Wert.

Run:  python kelly.py     ->  druckt f*, schreibt kelly_curve.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# geteilte Strategie-Logik aus v3 wiederverwenden (nicht duplizieren)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "strategies", "tsmom_v3"))
from tsmom_v3 import load_data, net_returns

PURPLE, GREEN, RED, GREY = "#7c3aed", "#16a34a", "#dc2626", "#64748b"


def kelly_fraction(net):
    """f* = Sharpe / sigma  (alles annualisiert)."""
    mu_ann    = net.mean() * 252
    sigma_ann = net.std()  * np.sqrt(252)
    sharpe    = mu_ann / sigma_ann
    f_star    = mu_ann / sigma_ann**2          # = Sharpe / sigma
    return sharpe, sigma_ann, mu_ann, f_star


def growth(f, mu, sigma):
    """log-Wachstum pro Jahr bei Hebel f:  g(f) = f*mu - 0.5 * f^2 * sigma^2."""
    return f * mu - 0.5 * f**2 * sigma**2


def main():
    close, log_returns = load_data()
    net, _, _ = net_returns(close, log_returns)
    sharpe, sigma, mu, f_star = kelly_fraction(net)

    print(f"annualisierte Rendite mu : {mu*100:6.2f} %")
    print(f"annualisierte Vol sigma  : {sigma*100:6.2f} %")
    print(f"Sharpe                   : {sharpe:6.3f}")
    print(f"Kelly f* = Sharpe/sigma  : {f_star:6.2f}x")
    print(f"Half-Kelly               : {f_star/2:6.2f}x")
    print(f"g(f*)  (max Wachstum)    : {growth(f_star, mu, sigma)*100:6.2f} % / Jahr")
    print(f"g(2*f*) (= 0, die Klippe) : {growth(2*f_star, mu, sigma)*100:6.2f} % / Jahr")

    # --- Kurve zeichnen ---
    f = np.linspace(0, 2.4 * f_star, 400)
    g = growth(f, mu, sigma)

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(f, g * 100, color=PURPLE, lw=2)
    ax.axhline(0, color=GREY, lw=.8)
    ax.axvline(f_star,     color=GREEN, ls="--", lw=1.2, label=f"f* = {f_star:.1f}× (Optimum)")
    ax.axvline(f_star / 2, color="#f59e0b", ls="--", lw=1.2, label=f"Half-Kelly = {f_star/2:.1f}×")
    ax.axvline(2 * f_star, color=RED, ls="--", lw=1.2, label=f"2·f* = {2*f_star:.1f}× (g = 0)")
    ax.axvline(1.0, color=GREY, ls=":", lw=1, label="1× (was ich fahre)")
    ax.fill_between(f, g * 100, 0, where=(g > 0), color=PURPLE, alpha=.08)

    ax.annotate("sanfter Hang\n(zu wenig kostet wenig)", xy=(f_star*0.45, growth(f_star*0.45, mu, sigma)*100),
                xytext=(f_star*0.15, growth(f_star, mu, sigma)*100*0.35), color=GREY, fontsize=9)
    ax.annotate("Klippe\n(zu viel ruiniert)", xy=(f_star*1.7, growth(f_star*1.7, mu, sigma)*100),
                xytext=(f_star*1.55, growth(f_star, mu, sigma)*100*0.15), color=RED, fontsize=9)

    ax.set_title("Kelly — Wachstum je Hebel: links Hang, rechts Klippe (unsymmetrisch)")
    ax.set_xlabel("Hebel f (× Portfolio)"); ax.set_ylabel("log-Wachstum % / Jahr")
    ax.legend(fontsize=8, loc="lower left"); ax.grid(alpha=.2)
    plt.tight_layout()
    plt.savefig("kelly_curve.png", dpi=130, bbox_inches="tight")
    print("wrote kelly_curve.png")


if __name__ == "__main__":
    main()
