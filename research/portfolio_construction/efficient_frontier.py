"""
Portfolio-Methoden im OOS-Vergleich — die Leiter des Misstrauens
================================================================
KW31 · Portfolio-Konstruktion

Fünf Methoden, IN-SAMPLE geschätzt, OUT-OF-SAMPLE gehandelt:
    Markowitz Max-Sharpe   (nutzt mu + Vols + Korrelationen — überfittet)
    Min-Variance           (Vols + Korrelationen, KEIN mu)
    Risk Parity voll       (Vols + Korrelationen, gleiche Risikobeiträge)
    Risk Parity naiv       (NUR Vols, inverse-vol)
    1/N                    (nichts)

Kernlektion: je noisiger die Zutat, der du traust, desto fragiler OOS.
Rangfolge des Misstrauens: mu >> Korrelationen > Vols.

Run:  python efficient_frontier.py   ->  druckt Vergleich, schreibt frontier.png
(Daten live von Yahoo Finance; braucht ../../strategies/tsmom_v3/tsmom_v3.py)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "strategies", "tsmom_v3"))
from tsmom_v3 import load_data

TD = 252
PURPLE, AMBER, GREEN2, GREEN, GREY = "#7c3aed", "#f59e0b", "#22c55e", "#16a34a", "#64748b"


def stats(w, r):
    p = r.values @ w
    mu, sig = p.mean() * TD, p.std() * np.sqrt(TD)
    return mu, sig, mu / sig


def main():
    close, _ = load_data()
    returns = close.pct_change(fill_method=None).dropna(how="any")   # gemeinsame Stichprobe
    n = returns.shape[1]
    split   = int(len(returns) * 0.70)
    IS, OOS = returns.iloc[:split], returns.iloc[split:]
    print(f"Assets: {n} | IS {IS.index[0].date()}–{IS.index[-1].date()} | "
          f"OOS {OOS.index[0].date()}–{OOS.index[-1].date()}")

    mu  = IS.mean().values * TD
    cov = IS.cov().values  * TD
    inv = np.linalg.inv(cov)
    one = np.ones(n)
    vol = np.sqrt(np.diag(cov))

    w_tan = inv @ mu;  w_tan /= w_tan.sum()          # Markowitz Max-Sharpe
    w_mv  = inv @ one; w_mv  /= w_mv.sum()           # Min-Variance
    w_rpn = (1 / vol); w_rpn /= w_rpn.sum()          # Risk Parity naiv (inverse vol)
    w_eq  = one / n                                   # 1/N

    def rp_obj(w):                                    # Risk Parity voll: gleiche Risikobeiträge
        sp = np.sqrt(w @ cov @ w)
        rc = w * (cov @ w) / sp
        return np.sum((rc - sp / n) ** 2)
    w_rpf = minimize(rp_obj, one / n, method="SLSQP",
                     bounds=[(0, 1)] * n,
                     constraints={"type": "eq", "fun": lambda w: w.sum() - 1}).x

    methods = [("Markowitz Max-Sharpe", w_tan), ("Min-Variance", w_mv),
               ("Risk Parity voll", w_rpf), ("Risk Parity naiv", w_rpn), ("1/N", w_eq)]

    print("\n=== Markowitz-Gewichte (in-sample) — Error-Maximizer-Signatur ===")
    print(f"  max {w_tan.max()*100:+.0f}% ({returns.columns[w_tan.argmax()]}) | "
          f"min {w_tan.min()*100:+.0f}% ({returns.columns[w_tan.argmin()]}) | "
          f"Brutto {np.abs(w_tan).sum()*100:.0f}%")

    print("\n=== OUT-OF-SAMPLE (das ehrliche Urteil) ===")
    print(f"  {'Portfolio':<22}{'Rendite':>9}{'Vol':>8}{'Sharpe':>9}")
    res = {}
    for name, w in methods:
        m, s, sh = stats(w, OOS); res[name] = sh
        print(f"  {name:<22}{m*100:>8.1f}%{s*100:>7.1f}%{sh:>9.2f}")

    print("\n  Merke: Sharpe ist ein VERHAELTNIS — hoher Sharpe aus niedriger Vol "
          "(Min-Var) kann ein Cash-Fonds sein. Immer die Rendite dazu lesen.")

    # --- Plot: OOS-Sharpe-Balken ---
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(figsize=(9, 5))
    names = [k for k, _ in methods]
    vals  = [res[k] for k in names]
    cols  = [PURPLE, AMBER, GREY, GREEN2, GREEN]
    bars  = ax.bar([n.replace(" ", "\n", 1) for n in names], vals, color=cols)
    ax.axhline(0, color=GREY, lw=.8)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width()/2, v),
                    textcoords="offset points", xytext=(0, 6 if v >= 0 else -14),
                    ha="center", fontsize=10, fontweight="bold")
    ax.set_title("OOS — realisierter Sharpe je Methode")
    ax.set_ylabel("Sharpe (OOS)"); ax.grid(alpha=.2, axis="y")
    plt.tight_layout()
    plt.savefig("frontier.png", dpi=130, bbox_inches="tight")
    print("\nwrote frontier.png")


if __name__ == "__main__":
    main()
