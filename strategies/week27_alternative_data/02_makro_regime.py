"""
Makro-Regime Filter — HY-Spread & Yield Curve
==============================================
Datenquellen: FRED (Federal Reserve Economic Data)
  BAMLH0A0HYM2 — ICE BofA High Yield Index (HY-Spread)
  T10Y2Y        — 10-Year minus 2-Year Treasury Spread

Logik:
  Risk-Off = HY_Spread > 4%  ODER  Yield_2s10s < 0
  → S&P 500 Rendite im Risk-Off Regime statistisch signifikant schlechter

KW27 Ergebnis (2005–2026, 773 Handelstage):
  Risk-On:  Mean +0.096%/Tag | Std 0.80% | Min −2.95%
  Risk-Off: Mean +0.041%/Tag | Std 1.06% | Min −5.98%
  → Risk-Off = 57% niedrigere Rendite + 32% höhere Volatilität
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas_datareader.data as web
import yfinance as yf
import datetime

# ── 1. Daten laden ───────────────────────────────────────────────────────────

START = datetime.datetime(2005, 1, 1)
END   = datetime.datetime(2026, 6, 1)


def load_data() -> pd.DataFrame:
    """Lädt HY-Spread, Yield Curve und S&P 500 von FRED/Yahoo."""
    print("Lade FRED-Daten...")
    hy_spread   = web.DataReader("BAMLH0A0HYM2", "fred", START, END)
    yield_curve = web.DataReader("T10Y2Y",        "fred", START, END)

    print("Lade S&P 500...")
    sp500 = yf.download("^GSPC", start=START, end=END, progress=False)["Close"]

    macro = pd.concat([hy_spread, yield_curve, sp500], axis=1)
    macro.columns = ["HY_Spread", "Yield_2s10s", "SP500"]
    macro = macro.ffill().dropna()
    return macro


# ── 2. Regime-Klassifikation ─────────────────────────────────────────────────

def classify_regime(
    macro: pd.DataFrame,
    hy_threshold: float = 4.0,
    yc_threshold: float = 0.0,
) -> pd.DataFrame:
    """
    Risk-Off Definition:
      HY_Spread  > hy_threshold  → Kreditstress (Panik, Flucht aus Risiko)
      Yield_2s10s < yc_threshold → Yield Curve invertiert (Rezessionswarnung)

    OR-Bedingung: reicht wenn EINE Bedingung erfüllt ist.
    AND wäre strenger (weniger False Positives, aber mehr Missed Events).
    """
    macro = macro.copy()
    macro["Risk_Off"] = (
        (macro["HY_Spread"]    > hy_threshold) |
        (macro["Yield_2s10s"]  < yc_threshold)
    )
    macro["SP500_Return"] = macro["SP500"].pct_change()
    return macro


# ── 3. Regime-Analyse ────────────────────────────────────────────────────────

def analyze_regime(macro: pd.DataFrame) -> pd.DataFrame:
    """Vergleicht S&P 500 Renditen in Risk-On vs. Risk-Off."""
    stats = macro.groupby("Risk_Off")["SP500_Return"].describe()
    stats.index = stats.index.map({False: "Risk-On", True: "Risk-Off"})

    print("\n" + "=" * 55)
    print("Makro-Regime Analyse — S&P 500 Tagesrenditen")
    print("=" * 55)
    print(stats[["count", "mean", "std", "min", "max"]].round(5).to_string())

    on  = macro[~macro["Risk_Off"]]["SP500_Return"]
    off = macro[ macro["Risk_Off"]]["SP500_Return"]

    mean_diff = (on.mean() - off.mean()) / on.mean() * 100
    vol_diff  = (off.std()  - on.std())  / on.std()  * 100

    print(f"\nRisk-Off vs. Risk-On:")
    print(f"  Rendite:    {mean_diff:+.1f}% schlechter im Risk-Off Regime")
    print(f"  Volatilität:{vol_diff:+.1f}% höher im Risk-Off Regime")
    print(f"\nAktuell (letzter Datenpunkt):")

    last = macro.iloc[-1]
    regime = "Risk-Off ⚠️" if last["Risk_Off"] else "Risk-On ✅"
    print(f"  HY-Spread:   {last['HY_Spread']:.2f}%  (Schwelle: 4.0%)")
    print(f"  Yield Curve: {last['Yield_2s10s']:.2f}%  (Schwelle: 0.0%)")
    print(f"  Regime:      {regime}")

    return stats


# ── 4. Visualisierung ────────────────────────────────────────────────────────

def plot_regime(macro: pd.DataFrame, save_path: str = None):
    BG, GRID  = "#0d1117", "#21262d"
    BLUE, RED = "#58a6ff", "#da3633"
    GREEN     = "#3fb950"
    TEXT, GREY = "#e6edf3", "#8b949e"

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1, 1]})
    fig.patch.set_facecolor(BG)

    for ax in axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors=GREY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.grid(axis="y", color=GRID, linewidth=0.5)

    # Hintergrund: Risk-Off Perioden schattieren
    risk_off = macro["Risk_Off"]
    for ax in axes:
        ax.fill_between(macro.index, 0, 1,
                        where=risk_off, transform=ax.get_xaxis_transform(),
                        color=RED, alpha=0.08)

    # Panel 1: S&P 500
    cum = (1 + macro["SP500_Return"]).cumprod()
    axes[0].plot(cum.index, cum.values, color=BLUE, linewidth=1.5)
    axes[0].set_ylabel("S&P 500 (kum.)", color=GREY, fontsize=9)
    axes[0].set_title("Makro-Regime Filter — HY-Spread & Yield Curve (2005–2026)",
                      color=TEXT, fontsize=12, pad=10)

    # Panel 2: HY-Spread
    axes[1].plot(macro.index, macro["HY_Spread"], color="#f0883e", linewidth=1.2)
    axes[1].axhline(4.0, color=RED, linestyle="--", linewidth=1, alpha=0.8, label="Schwelle 4%")
    axes[1].set_ylabel("HY-Spread (%)", color=GREY, fontsize=9)
    axes[1].legend(facecolor="#161b22", labelcolor=TEXT, fontsize=8)

    # Panel 3: Yield Curve
    yc = macro["Yield_2s10s"]
    axes[2].fill_between(yc.index, yc.values, 0,
                         where=(yc >= 0), color=GREEN, alpha=0.4, label="Normal")
    axes[2].fill_between(yc.index, yc.values, 0,
                         where=(yc < 0),  color=RED,   alpha=0.5, label="Invertiert")
    axes[2].axhline(0, color=GREY, linewidth=0.8)
    axes[2].set_ylabel("2s10s Spread (%)", color=GREY, fontsize=9)
    axes[2].legend(facecolor="#161b22", labelcolor=TEXT, fontsize=8)

    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.tight_layout(h_pad=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
        print(f"\nGespeichert: {save_path}")
    else:
        plt.show()


# ── 5. Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    macro = load_data()
    macro = classify_regime(macro, hy_threshold=4.0, yc_threshold=0.0)
    analyze_regime(macro)
    plot_regime(macro, save_path="makro_regime.png")
