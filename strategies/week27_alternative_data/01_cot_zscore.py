"""
COT Z-Score Signal — Commitment of Traders
==========================================
Quelle: CFTC Disaggregated COT Report
Logik:  Non-Commercial Net-Positioning mit 52-Wochen Z-Score
        Extremes Positioning → Contrarian Signal (Short/Long Squeeze)

KW27 Ergebnis:
  Yen  (6J)  Z-Score: −4.27σ  → Short Squeeze Potential
  VIX  (VX)  Z-Score: −3.0σ   → Long Vol als Hedge interessant
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request

# ── 1. COT-Daten laden (CFTC direkt) ────────────────────────────────────────

# CFTC veröffentlicht wöchentlich (Dienstag-Stand, Freitag-Publikation)
# Disaggregated Report: enthält Leveraged Money (Hedge Funds) getrennt

COT_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"

def load_cot_csv(filepath: str) -> pd.DataFrame:
    """Lädt eine lokal gespeicherte COT-CSV-Datei."""
    df = pd.read_csv(filepath, low_memory=False)
    df["As_of_Date_In_Form_YYMMDD"] = pd.to_datetime(
        df["As_of_Date_In_Form_YYMMDD"], format="%y%m%d"
    )
    df = df.set_index("As_of_Date_In_Form_YYMMDD").sort_index()
    return df


def get_net_position(df: pd.DataFrame, market_name: str) -> pd.Series:
    """
    Berechnet Net-Positioning der Non-Commercials (Leveraged Money).
    Net = Long − Short
    """
    mask = df["Market_and_Exchange_Names"].str.contains(market_name, case=False, na=False)
    subset = df[mask]
    net = (
        subset["Lev_Money_Positions_Long_All"].astype(float)
        - subset["Lev_Money_Positions_Short_All"].astype(float)
    )
    net.name = market_name
    return net


# ── 2. Z-Score Berechnung ────────────────────────────────────────────────────

def rolling_zscore(series: pd.Series, window: int = 52) -> pd.Series:
    """
    52-Wochen rollierender Z-Score auf dem Net-Positioning.
    Z = (aktuell − Mittelwert) / Standardabweichung
    """
    mean = series.rolling(window).mean()
    std  = series.rolling(window).std()
    return (series - mean) / std


# ── 3. Signal Interpretation ─────────────────────────────────────────────────

def interpret_signal(z: float, instrument: str) -> str:
    """
    Short Squeeze Potential:  Z < −2σ → alle Spekulanten BEREITS short
                               kein Verkäufer mehr → kleinster Trigger
                               → Zwangs-Covering → Kaskaden-Kauf

    Long Squeeze Potential:   Z > +2σ → alle Spekulanten BEREITS long
                               kein Käufer mehr → Cascade-Sell
    """
    if z < -3:
        return f"⚠️  {instrument}: EXTREMES Short Squeeze Risiko (Z={z:.2f}σ)"
    elif z < -2:
        return f"🟡 {instrument}: Short Squeeze Potential (Z={z:.2f}σ)"
    elif z > 3:
        return f"⚠️  {instrument}: EXTREMES Long Squeeze Risiko (Z={z:.2f}σ)"
    elif z > 2:
        return f"🟡 {instrument}: Long Squeeze Potential (Z={z:.2f}σ)"
    else:
        return f"✅ {instrument}: Neutral (Z={z:.2f}σ)"


# ── 4. Visualisierung ────────────────────────────────────────────────────────

def plot_zscore(z_series: pd.Series, title: str, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 4))

    BG, GRID = "#0d1117", "#21262d"
    ax.set_facecolor(BG)
    ax.figure.patch.set_facecolor(BG)

    colors = ["#da3633" if v < -2 else "#3fb950" if v > 2 else "#58a6ff"
              for v in z_series.values]

    ax.bar(z_series.index, z_series.values, color=colors, alpha=0.75, width=5)
    ax.axhline(y=2,  color="#3fb950", linestyle="--", linewidth=1, alpha=0.7, label="+2σ")
    ax.axhline(y=-2, color="#da3633", linestyle="--", linewidth=1, alpha=0.7, label="−2σ")
    ax.axhline(y=0,  color="#8b949e", linestyle="-",  linewidth=0.8)

    ax.set_title(f"COT Z-Score — {title}", color="#e6edf3", fontsize=11, pad=8)
    ax.tick_params(colors="#8b949e")
    ax.legend(facecolor="#161b22", labelcolor="#e6edf3", fontsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)

    return ax


# ── 5. Beispiel: Manuelle Daten (KW27 Ergebnis) ─────────────────────────────
# In der Praxis: echte COT-CSV von CFTC laden (s.o.)

if __name__ == "__main__":
    print("=" * 55)
    print("COT Z-Score Analyse — KW27 2026")
    print("=" * 55)

    # KW27 Ergebnisse (aus Session-Analyse)
    signals = {
        "Japanischer Yen (6J)": -4.27,
        "VIX Futures (VX)":     -3.00,
        "S&P 500 (ES)":          0.85,
        "Gold (GC)":             1.40,
        "Crude Oil (CL)":       -0.60,
    }

    print()
    for instrument, z in signals.items():
        print(interpret_signal(z, instrument))

    print()
    print("Mechanismus Short Squeeze:")
    print("  1. Non-Commercials massiv Short (Z << −2σ)")
    print("  2. Kein Verkäufer mehr übrig → Markt überdehnt")
    print("  3. Trigger → Zwangs-Covering → Kaskaden-Kauf")
    print("  4. Yen explodiert → Short Squeeze")
    print()
    print("Signal: Long Yen solange Makro-Regime es erlaubt")
    print("        (Yield Curve + HY-Spread prüfen zuerst!)")
