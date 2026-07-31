"""
TSMOM-Exposure über die Zeit — der Portfolio-Cap, gemessen statt gebaut
======================================================================
KW31 · Portfolio-Konstruktion

Frage: Der 10x-Per-Asset-Cap (v3) verhindert NICHT, dass alle Assets gleichzeitig
long stehen. Wie einseitig steht das Buch — und braucht es einen Portfolio-Cap?

Ergebnis (25 J.): ~77% der Tage netto long, Median ~+17x, Ø 12 long / 7 short —
strukturell long-lastig, ABER es dreht netto short in Abschwüngen (self-correcting).

ENTSCHEIDUNG: KEIN harter Portfolio-Cap.
  1. Die 77% netto long SIND die Trend-Prämie -> cappen = Rendite bluten.
  2. Cap = neuer Parameter -> N rauf -> deflated t runter.
  3. Restgefahr (plötzlicher Crash while long) deckt Positionsgröße + Kill-Switch ab.
Also: Risiko-Bewusstseins-Punkt, keine neue Regel. Nicht über-engineeren.

Run:  python exposure_analysis.py   ->  druckt Statistik, schreibt exposure.png
(Daten live von Yahoo Finance, kein API-Key.)
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
    pos    = ((TARGET_VOL / vol) * signal).clip(-CAP, CAP)      # v3-Positionen (gecappt)

    gross   = pos.abs().sum(axis=1)
    net     = pos.sum(axis=1)
    n_long  = (pos > 0).sum(axis=1)
    n_short = (pos < 0).sum(axis=1)

    print(f"Netto-Exposure: Median {net.median():.1f} | Ø {net.mean():.1f} | "
          f"min {net.min():.1f} | max {net.max():.1f}")
    print(f"Anteil Tage netto LONG : {(net > 0).mean()*100:.0f}%")
    print(f"Ø long {n_long.mean():.1f}/24 | Ø short {n_short.mean():.1f}/24 | "
          f"Ø Brutto {gross.mean():.0f}x")
    print("\n-> strukturell long-lastig, aber self-correcting. KEIN harter Cap "
          "(siehe Docstring). Restgefahr via Sizing + Kill-Switch.")

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    ax[0].plot(net.index, net, color=PURPLE, lw=1)
    ax[0].axhline(0, color=GREY, lw=.8)
    ax[0].fill_between(net.index, net, 0, where=(net > 0), color=GREEN, alpha=.25)
    ax[0].fill_between(net.index, net, 0, where=(net < 0), color=RED, alpha=.25)
    for s, e in CRISES:
        ax[0].axvspan(pd.Timestamp(s), pd.Timestamp(e), color="k", alpha=.12)
    ax[0].set_title("Netto-Exposure (long − short) — grau = Krisen")
    ax[0].set_ylabel("Netto-Hebel")

    ax[1].plot(n_long.index, n_long, color=GREEN, lw=1, label="# long")
    ax[1].plot(n_short.index, n_short, color=RED, lw=1, label="# short")
    ax[1].set_title("Anzahl long vs. short (von 24)")
    ax[1].set_ylabel("Anzahl"); ax[1].legend()
    plt.tight_layout()
    plt.savefig("exposure.png", dpi=130, bbox_inches="tight")
    print("wrote exposure.png")


if __name__ == "__main__":
    main()
