"""
Portfolio methods, out-of-sample — the ladder of distrust
=========================================================
KW31 · Portfolio construction

Five methods, estimated IN-SAMPLE, traded OUT-OF-SAMPLE:
    Markowitz max-Sharpe   (uses mu + vols + correlations — overfits)
    Minimum-Variance       (vols + correlations, NO mu)
    Risk Parity full       (vols + correlations, equal risk contributions)
    Risk Parity naive      (ONLY vols, inverse-vol)
    1/N                    (nothing)

Core lesson: the noisier the input you trust, the more fragile out-of-sample.
Ladder of distrust: mu >> correlations > vols.

Run:  python efficient_frontier.py   ->  prints comparison, writes frontier.png
(Data pulled live from Yahoo Finance; needs ../../strategies/tsmom_v3/tsmom_v3.py)
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
    returns = close.pct_change(fill_method=None).dropna(how="any")   # common sample
    n = returns.shape[1]
    split   = int(len(returns) * 0.70)
    IS, OOS = returns.iloc[:split], returns.iloc[split:]
    print(f"Assets: {n} | IS {IS.index[0].date()}-{IS.index[-1].date()} | "
          f"OOS {OOS.index[0].date()}-{OOS.index[-1].date()}")

    mu  = IS.mean().values * TD
    cov = IS.cov().values  * TD
    inv = np.linalg.inv(cov)
    one = np.ones(n)
    vol = np.sqrt(np.diag(cov))

    w_tan = inv @ mu;  w_tan /= w_tan.sum()          # Markowitz max-Sharpe
    w_mv  = inv @ one; w_mv  /= w_mv.sum()           # Minimum-Variance
    w_rpn = (1 / vol); w_rpn /= w_rpn.sum()          # Risk Parity naive (inverse vol)
    w_eq  = one / n                                   # 1/N

    def rp_obj(w):                                    # Risk Parity full: equal risk contributions
        sp = np.sqrt(w @ cov @ w)
        rc = w * (cov @ w) / sp
        return np.sum((rc - sp / n) ** 2)
    w_rpf = minimize(rp_obj, one / n, method="SLSQP",
                     bounds=[(0, 1)] * n,
                     constraints={"type": "eq", "fun": lambda w: w.sum() - 1}).x

    methods = [("Markowitz max-Sharpe", w_tan), ("Min-Variance", w_mv),
               ("Risk Parity full", w_rpf), ("Risk Parity naive", w_rpn), ("1/N", w_eq)]

    print("\n=== Markowitz weights (in-sample) — the error-maximizer signature ===")
    print(f"  max {w_tan.max()*100:+.0f}% ({returns.columns[w_tan.argmax()]}) | "
          f"min {w_tan.min()*100:+.0f}% ({returns.columns[w_tan.argmin()]}) | "
          f"gross {np.abs(w_tan).sum()*100:.0f}%")

    print("\n=== OUT-OF-SAMPLE (the honest verdict) ===")
    print(f"  {'Portfolio':<22}{'Return':>9}{'Vol':>8}{'Sharpe':>9}")
    res = {}
    for name, w in methods:
        m, s, sh = stats(w, OOS); res[name] = sh
        print(f"  {name:<22}{m*100:>8.1f}%{s*100:>7.1f}%{sh:>9.2f}")

    print("\n  Note: Sharpe is a RATIO — a high Sharpe from low vol (Min-Var) can be a "
          "cash fund. Always read the return alongside it.")

    # --- plot: OOS Sharpe bars ---
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(figsize=(9, 5))
    names = [k for k, _ in methods]
    vals  = [res[k] for k in names]
    cols  = [PURPLE, AMBER, GREY, GREEN2, GREEN]
    bars  = ax.bar([nm.replace(" ", "\n", 1) for nm in names], vals, color=cols)
    ax.axhline(0, color=GREY, lw=.8)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width()/2, v),
                    textcoords="offset points", xytext=(0, 6 if v >= 0 else -14),
                    ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Out-of-sample realised Sharpe by method")
    ax.set_ylabel("Sharpe (OOS)"); ax.grid(alpha=.2, axis="y")
    plt.tight_layout()
    plt.savefig("frontier.png", dpi=130, bbox_inches="tight")
    print("\nwrote frontier.png")


if __name__ == "__main__":
    main()
