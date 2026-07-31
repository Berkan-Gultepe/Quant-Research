"""
TSMOM exposure over time — the portfolio cap, measured not built
================================================================
KW31 · Portfolio construction

Question: the 10x per-asset cap (v3) does NOT stop all assets from being long at
once. How one-sided is the book — and does it need a portfolio-level cap?

Result (25y): ~77% of days net long, median ~+17x, avg 12 long / 7 short —
structurally long-tilted, BUT it flips net short in downturns (self-correcting).

DECISION: NO hard portfolio cap.
  1. The 77% net long IS the trend premium -> capping it bleeds return.
  2. A cap is a new parameter -> raises N -> worsens the deflated t.
  3. The residual risk (a sudden crash while long) is covered by position sizing
     + kill-switch.
So it's a risk-*awareness* item, not a new rule. Don't over-engineer.

Run:  python exposure_analysis.py   ->  prints stats, writes exposure.png
(Data pulled live from Yahoo Finance, no API key.)
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "FXI", "TLT", "IEF", "SHY",
            "LQD", "HYG", "EMB", "GLD", "SLV", "USO", "UNG", "DBA", "DBB", "UUP",
            "FXE", "FXY", "FXB", "FXA"]
TARGET_VOL, LOOKBACK, VOL_WINDOW, CAP = 0.15, 252, 60, 10.0
PURPLE, GREEN, RED, GREY = "#7c3aed", "#16a34a", "#dc2626", "#64748b"
CRISES = [("2008-09-01", "2009-03-31"), ("2020-02-20", "2020-04-15")]


def main():
    close  = yf.download(UNIVERSE, start="2000-01-01", progress=False)["Close"]
    logret = np.log(close / close.shift(1)).dropna(how="all")
    signal = np.sign(close.pct_change(LOOKBACK, fill_method=None))
    vol    = logret.rolling(VOL_WINDOW, min_periods=VOL_WINDOW // 2).std() * np.sqrt(252)
    pos    = ((TARGET_VOL / vol) * signal).clip(-CAP, CAP)      # v3 positions (capped)

    gross   = pos.abs().sum(axis=1)
    net     = pos.sum(axis=1)
    n_long  = (pos > 0).sum(axis=1)
    n_short = (pos < 0).sum(axis=1)

    print(f"Net exposure: median {net.median():.1f} | avg {net.mean():.1f} | "
          f"min {net.min():.1f} | max {net.max():.1f}")
    print(f"Share of days net LONG : {(net > 0).mean()*100:.0f}%")
    print(f"Avg long {n_long.mean():.1f}/24 | avg short {n_short.mean():.1f}/24 | "
          f"avg gross {gross.mean():.0f}x")
    print("\n-> structurally long-tilted but self-correcting. NO hard cap "
          "(see docstring). Residual risk handled by sizing + kill-switch.")

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax[0].plot(net.index, net, color=PURPLE, lw=1)
    ax[0].axhline(0, color=GREY, lw=.8)
    ax[0].fill_between(net.index, net, 0, where=(net > 0), color=GREEN, alpha=.25)
    ax[0].fill_between(net.index, net, 0, where=(net < 0), color=RED, alpha=.25)
    for s, e in CRISES:
        ax[0].axvspan(pd.Timestamp(s), pd.Timestamp(e), color="k", alpha=.12)
    ax[0].set_title("Net exposure (long - short) — grey = crises")
    ax[0].set_ylabel("Net leverage")

    ax[1].plot(n_long.index, n_long, color=GREEN, lw=1, label="# long")
    ax[1].plot(n_short.index, n_short, color=RED, lw=1, label="# short")
    ax[1].set_title("Number long vs short (of 24)")
    ax[1].set_ylabel("Count"); ax[1].legend()
    plt.tight_layout()
    plt.savefig("exposure.png", dpi=130, bbox_inches="tight")
    print("wrote exposure.png")


if __name__ == "__main__":
    main()
