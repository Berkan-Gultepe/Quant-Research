"""
Korrelationsbruch in Krisen — die zwei Lager
============================================
KW31 · Portfolio-Konstruktion

Naiv: "im Crash gehen alle Korrelationen auf 1". An einem MULTI-Asset-Buch stimmt
das so nicht — der Markt spaltet sich in ZWEI Lager, die sich im Durchschnitt
wegheben:
    Risiko-Assets (Aktien, Credit, Rohstoffe) -> Korrelation Richtung +1
    Sichere Häfen (Staatsanleihen, Yen)       -> entkoppeln, Richtung -1

Mechanismus: Zwangsverkäufe durch Hebel (Margin Calls) — "Bilanzen, nicht Assets".
Ein Liquiditäts-Event, kein Fundamental-Event.

Run:  python correlation_crisis.py   ->  druckt Zahlen + Listen, schreibt corr_crisis.png
(Daten live von Yahoo Finance, kein API-Key.)
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
    "Ruhig 2017"       : ("2017-01-01", "2017-12-31"),
    "Finanzkrise 2008" : ("2008-09-01", "2009-03-31"),
    "COVID-Crash 2020" : ("2020-02-20", "2020-04-15"),
}


def avg_corr(df):
    c = df.corr().values
    iu = np.triu_indices(c.shape[0], k=1)
    return c[iu].mean()


def main():
    close   = yf.download(UNIVERSE, start="2000-01-01", progress=False)["Close"]
    returns = close.pct_change(fill_method=None).dropna(how="any")

    print("Durchschnittliche paarweise Korrelation der 24 Assets:")
    for name, (a, b) in PERIODS.items():
        sub = returns.loc[a:b]
        print(f"  {name:<18} {avg_corr(sub):+.2f}   ({len(sub)} Tage)")
    print("  -> der Ø springt kaum: die zwei Lager heben sich weg. "
          "Trau keiner einzelnen Kennzahl.")

    # --- Korrelation jedes Assets zu SPY: ruhig vs. Crash ---
    def corr_to_spy(s, e):
        r = returns.loc[s:e]
        return r.corrwith(r["SPY"]).drop("SPY")

    calm  = corr_to_spy(*PERIODS["Ruhig 2017"])
    covid = corr_to_spy(*PERIODS["COVID-Crash 2020"])
    order = covid.sort_values().index
    calm, covid = calm[order], covid[order]

    print("\nAm stärksten ENTKOPPELT im Crash (echte sichere Häfen):")
    print(covid.sort_values().head(5).round(2).to_string())
    print("\nAm stärksten MIT dem Markt (Risiko-Cluster):")
    print(covid.sort_values().tail(5).round(2).to_string())

    y = np.arange(len(order))
    plt.rcParams.update({"font.size": 9})
    plt.figure(figsize=(9, 8))
    plt.barh(y - 0.2, calm.values,  height=0.4, color=GREY, label="Ruhig 2017")
    plt.barh(y + 0.2, covid.values, height=0.4, color=RED,  label="COVID-Crash 2020")
    plt.axvline(0, color="k", lw=.8)
    plt.yticks(y, order); plt.xlabel("Korrelation zu SPY"); plt.legend()
    plt.title("Korrelation jedes Assets zu SPY — ruhig vs. Crash (die zwei Lager)")
    plt.tight_layout()
    plt.savefig("corr_crisis.png", dpi=130, bbox_inches="tight")
    print("\nwrote corr_crisis.png")


if __name__ == "__main__":
    main()
