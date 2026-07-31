"""
Correlation breakdown in crises — the two camps
===============================================
KW31 · Portfolio construction

The naive claim is "in a crash all correlations go to 1". For a MULTI-asset book
that is not quite true — the market splits into TWO camps that cancel in the average:
    risk assets (equities, credit, commodities) -> correlation toward +1
    safe havens (government bonds, yen)          -> decouple, toward -1

Mechanism: forced deleveraging (margin calls) — "balance sheets, not assets". A
liquidity event, not a fundamental one.

Run:  python correlation_crisis.py   ->  prints numbers + lists, writes corr_crisis.png
(Data pulled live from Yahoo Finance, no API key.)
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "FXI", "TLT", "IEF", "SHY",
            "LQD", "HYG", "EMB", "GLD", "SLV", "USO", "UNG", "DBA", "DBB", "UUP",
            "FXE", "FXY", "FXB", "FXA"]
GREY, RED = "#94a3b8", "#dc2626"

PERIODS = {
    "Calm 2017"        : ("2017-01-01", "2017-12-31"),
    "GFC 2008"         : ("2008-09-01", "2009-03-31"),
    "COVID crash 2020" : ("2020-02-20", "2020-04-15"),
}


def avg_corr(df):
    c = df.corr().values
    iu = np.triu_indices(c.shape[0], k=1)
    return c[iu].mean()


def main():
    close   = yf.download(UNIVERSE, start="2000-01-01", progress=False)["Close"]
    returns = close.pct_change(fill_method=None).dropna(how="any")

    print("Average pairwise correlation of the 24 assets:")
    for name, (a, b) in PERIODS.items():
        sub = returns.loc[a:b]
        print(f"  {name:<18} {avg_corr(sub):+.2f}   ({len(sub)} days)")
    print("  -> the average barely moves: the two camps cancel out. "
          "Don't trust a single summary number.")

    # --- correlation of each asset to SPY: calm vs crash ---
    def corr_to_spy(s, e):
        r = returns.loc[s:e]
        return r.corrwith(r["SPY"]).drop("SPY")

    calm  = corr_to_spy(*PERIODS["Calm 2017"])
    covid = corr_to_spy(*PERIODS["COVID crash 2020"])
    order = covid.sort_values().index
    calm, covid = calm[order], covid[order]

    print("\nMost DECOUPLED in the crash (real safe havens):")
    print(covid.sort_values().head(5).round(2).to_string())
    print("\nMost WITH the market (risk cluster):")
    print(covid.sort_values().tail(5).round(2).to_string())

    y = np.arange(len(order))
    plt.rcParams.update({"font.size": 9})
    plt.figure(figsize=(9, 8))
    plt.barh(y - 0.2, calm.values,  height=0.4, color=GREY, label="Calm 2017")
    plt.barh(y + 0.2, covid.values, height=0.4, color=RED,  label="COVID crash 2020")
    plt.axvline(0, color="k", lw=.8)
    plt.yticks(y, order); plt.xlabel("Correlation to SPY"); plt.legend()
    plt.title("Each asset's correlation to SPY — calm vs crash (the two camps)")
    plt.tight_layout()
    plt.savefig("corr_crisis.png", dpi=130, bbox_inches="tight")
    print("\nwrote corr_crisis.png")


if __name__ == "__main__":
    main()
