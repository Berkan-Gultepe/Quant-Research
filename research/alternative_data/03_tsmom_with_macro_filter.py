"""
TSMOM + Makro-Regime Filter
===========================
Erweitert das TSMOM-Framework (Moskowitz et al. 2012) um einen
makroökonomischen Regime-Filter basierend auf HY-Spread und Yield Curve.

Hypothese: TSMOM im Risk-Off Regime reduzieren → bessere risikobereinigte Rendite

Baseline (ohne Filter): Sharpe 1.86, Max DD −9.3%
Zu testen:              Sharpe mit Filter vs. ohne

Signal-Hierarchie:
  ① Yield Curve (T10Y2Y) — Leading Indicator, 6–18 Monate Vorlauf
  ② HY-Spread (BAMLH0A0HYM2) — Bestätigung, Coincident
  ③ COT Z-Score — Taktisches Timing
  → Widersprüchliche Signale = kein Trade
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader.data as web
import yfinance as yf
import datetime

# ── Konfiguration ────────────────────────────────────────────────────────────

TICKERS      = ["SPY", "GLD", "TLT", "USO", "UUP"]
START        = "2005-01-01"
END          = "2026-06-01"
TARGET_VOL   = 0.15        # Annualisierte Zielvolatilität
SIGNAL_WINDOW = 252        # Momentum-Lookback (Handelstage)
VOL_WINDOW   = 60          # Volatilitäts-Schätzfenster

HY_THRESHOLD = 4.0         # % — Risk-Off wenn HY-Spread > 4%
YC_THRESHOLD = 0.0         # % — Risk-Off wenn Yield Curve < 0%
FILTER_SCALE = 0.0         # Position in Risk-Off auf 0% skaliert (0.5 = halbiert)


# ── 1. Daten ─────────────────────────────────────────────────────────────────

def load_all_data():
    print("Lade Marktdaten...")
    price_data = yf.download(TICKERS, start=START, end=END,
                             auto_adjust=True, progress=False)["Close"]
    log_returns = np.log(price_data / price_data.shift(1)).dropna()

    print("Lade Makro-Daten (FRED)...")
    start_dt = datetime.datetime.strptime(START, "%Y-%m-%d")
    end_dt   = datetime.datetime.strptime(END,   "%Y-%m-%d")
    hy_spread   = web.DataReader("BAMLH0A0HYM2", "fred", start_dt, end_dt)
    yield_curve = web.DataReader("T10Y2Y",        "fred", start_dt, end_dt)

    macro = pd.concat([hy_spread, yield_curve], axis=1)
    macro.columns = ["HY_Spread", "Yield_2s10s"]
    macro = macro.ffill()

    return price_data, log_returns, macro


# ── 2. Regime ────────────────────────────────────────────────────────────────

def get_regime(macro: pd.DataFrame) -> pd.Series:
    """
    Risk-On = 1 (volle Position)
    Risk-Off = FILTER_SCALE (reduzierte Position)
    """
    risk_off = (
        (macro["HY_Spread"]   > HY_THRESHOLD) |
        (macro["Yield_2s10s"] < YC_THRESHOLD)
    )
    regime = pd.Series(1.0, index=macro.index)
    regime[risk_off] = FILTER_SCALE
    return regime


# ── 3. Strategie ─────────────────────────────────────────────────────────────

def run_tsmom(price_data, log_returns, macro):
    # Momentum-Signal: 12-Monats Return
    signal = np.sign(price_data.pct_change(SIGNAL_WINDOW)).shift(1)

    # Volatilitätsskalierung
    vol      = log_returns.rolling(VOL_WINDOW).std() * np.sqrt(252)
    position = (TARGET_VOL / vol) * signal

    # Portfolio (ohne Filter)
    returns_base = (position * log_returns.shift(1)).mean(axis=1).dropna()

    # Makro-Regime Filter anwenden
    regime = get_regime(macro).reindex(returns_base.index).ffill()
    returns_filtered = returns_base * regime

    return returns_base, returns_filtered


# ── 4. Auswertung ────────────────────────────────────────────────────────────

def evaluate(returns: pd.Series, label: str) -> dict:
    ar  = returns.mean() * 252
    av  = returns.std()  * np.sqrt(252)
    sr  = ar / av
    cum = np.exp(returns.cumsum())
    mdd = (cum / cum.cummax() - 1).min()

    result = {"Label": label, "Ann. Return": ar, "Ann. Vol": av,
              "Sharpe": sr, "Max DD": mdd}
    print(f"\n{label}:")
    print(f"  Ann. Return: {ar:.1%}")
    print(f"  Ann. Vol:    {av:.1%}")
    print(f"  Sharpe:      {sr:.2f}")
    print(f"  Max DD:      {mdd:.1%}")
    return result


# ── 5. Visualisierung ────────────────────────────────────────────────────────

def plot_comparison(returns_base, returns_filtered):
    BG   = "#0d1117"
    GRID = "#21262d"
    BLUE = "#58a6ff"
    PURP = "#bc8cff"
    TEXT = "#e6edf3"
    GREY = "#8b949e"

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=GREY)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.5)

    cum_base     = np.exp(returns_base.cumsum())
    cum_filtered = np.exp(returns_filtered.reindex(cum_base.index).cumsum())

    ax.plot(cum_base.index,     cum_base.values,     color=BLUE, linewidth=1.8,
            label=f"TSMOM (ohne Filter)  Sharpe: 1.86")
    ax.plot(cum_filtered.index, cum_filtered.values, color=PURP, linewidth=1.5,
            linestyle="--", label=f"TSMOM + Makro-Filter")

    ax.set_title("TSMOM — Baseline vs. Makro-Regime Filter", color=TEXT, fontsize=12, pad=10)
    ax.set_ylabel("Growth of $1", color=GREY)
    ax.legend(facecolor="#161b22", edgecolor=GRID, labelcolor=TEXT, fontsize=9)

    plt.tight_layout()
    plt.savefig("tsmom_macro_filter_comparison.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    print("\nGespeichert: tsmom_macro_filter_comparison.png")


# ── 6. Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("TSMOM + Makro-Regime Filter")
    print(f"HY Threshold:  {HY_THRESHOLD}%")
    print(f"YC Threshold:  {YC_THRESHOLD}%")
    print(f"Filter Scale:  {FILTER_SCALE}x (0=aus, 0.5=halbiert, 1=kein Filter)")
    print("=" * 55)

    price_data, log_returns, macro = load_all_data()
    returns_base, returns_filtered = run_tsmom(price_data, log_returns, macro)

    print("\nErgebnisse:")
    evaluate(returns_base,     "TSMOM ohne Filter (Baseline)")
    evaluate(returns_filtered, f"TSMOM mit Makro-Filter (Scale={FILTER_SCALE})")

    plot_comparison(returns_base, returns_filtered)

    print("\nNächste Schritte:")
    print("  → FILTER_SCALE = 0.5 testen (halbiert statt ausschaltet)")
    print("  → AND statt OR testen (strengerer Filter)")
    print("  → Verschiedene HY-Thresholds: 3%, 4%, 5%, 6%")
    print("  → COT als dritten Filter integrieren")
