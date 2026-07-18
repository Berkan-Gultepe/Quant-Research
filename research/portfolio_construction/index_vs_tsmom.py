"""
Portfolio construction — does adding TSMOM to an equity core actually help?
===========================================================================
Compares an S&P 500 (SPY) buy-and-hold core against blends with TSMOM v2 at
several capital weightings — and, crucially, at equal RISK weighting.

The point of the exercise:
    Diversification is a RISK allocation, not a CAPITAL allocation.
    30% of capital in a low-volatility strategy contributes ~2.5% of portfolio
    risk — i.e. almost nothing. Only risk-weighting unlocks the benefit.

Honest caveat (read the README): the risk-parity result requires ~2.5x leverage
on a strategy that already runs ~45x gross notional. It is the theoretical
ceiling, NOT something implementable as-is.

Run:  python index_vs_tsmom.py   ->  writes index_vs_tsmom.png + .csv
"""

import os
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "FXI",
            "TLT", "IEF", "SHY", "LQD", "HYG", "EMB",
            "GLD", "SLV", "USO", "UNG", "DBA", "DBB",
            "UUP", "FXE", "FXY", "FXB", "FXA"]

LOOKBACK, VOL_WINDOW, TARGET_VOL, COST = 252, 60, 0.15, 0.0005   # 5 bp per unit traded
START_CAPITAL = 10_000


def tsmom_net(px, logret):
    """TSMOM v2, net of transaction costs. Same logic as strategies/tsmom_v2."""
    signal   = np.sign(px.pct_change(LOOKBACK, fill_method=None))
    vol      = logret.rolling(VOL_WINDOW).std() * np.sqrt(252)
    position = (TARGET_VOL / vol) * signal
    turnover = position.diff().abs()
    return ((position.shift(1) * logret) - COST * turnover).mean(axis=1).dropna()


def stats(r, start=START_CAPITAL):
    eq   = start * (1 + r).cumprod()
    yrs  = (r.index[-1] - r.index[0]).days / 365.25
    cagr = (eq.iloc[-1] / start) ** (1 / yrs) - 1
    return {
        "Final":  f"{eq.iloc[-1]:,.0f}",
        "CAGR":   f"{cagr:.2%}",
        "Vol":    f"{r.std() * np.sqrt(252):.2%}",
        "Sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
        "MaxDD":  f"{(eq / eq.cummax() - 1).min():.1%}",
        "MaxDD_abs": f"{(eq - eq.cummax()).min():,.0f}",
        "Calmar": round(float(cagr / abs((eq / eq.cummax() - 1).min())), 2),
    }


def main():
    px     = yf.download(UNIVERSE, start="2000-01-01", progress=False)["Close"]
    logret = np.log(px / px.shift(1)).dropna(how="all")

    tsmom_l = tsmom_net(px, logret)
    spy_l   = logret["SPY"].dropna()
    idx     = tsmom_l.index.intersection(spy_l.index)

    # simple returns — correct for blending
    spy   = np.exp(spy_l.loc[idx])   - 1
    tsmom = np.exp(tsmom_l.loc[idx]) - 1

    lev = spy.std() / tsmom.std()      # scale TSMOM to SPY's risk level
    ports = {
        "SPY 100%":                      spy,
        "70% SPY / 30% TSMOM":           0.7 * spy + 0.3 * tsmom,
        "50% SPY / 50% TSMOM":           0.5 * spy + 0.5 * tsmom,
        f"Risk parity (TSMOM x{lev:.1f})": 0.5 * spy + 0.5 * lev * tsmom,
        "TSMOM 100%":                    tsmom,
    }

    tab = pd.DataFrame({k: stats(v) for k, v in ports.items()}).T
    print(f"Start capital: {START_CAPITAL:,} | Period: {idx[0].date()} - {idx[-1].date()}\n")
    print(tab.to_string())
    print(f"\nCorrelation SPY vs TSMOM: {spy.corr(tsmom):.3f}")

    # ---------- plot ----------
    fig, ax = plt.subplots(2, 1, figsize=(12, 9), sharex=True,
                           gridspec_kw={"height_ratios": [2, 1]})
    colors = ["#64748b", "#16a34a", "#0ea5e9", "#7c3aed", "#f59e0b"]
    for (name, r), c in zip(ports.items(), colors):
        eq = START_CAPITAL * (1 + r).cumprod()
        ax[0].plot(eq, label=f"{name}  ->  {eq.iloc[-1]:,.0f}", color=c, lw=1.6)
        ax[1].plot((eq / eq.cummax() - 1) * 100, color=c, lw=1.1)

    ax[0].set_yscale("log"); ax[0].set_ylabel("Portfolio value")
    ax[0].set_title(f"Equity core alone vs. core + TSMOM — start {START_CAPITAL:,} (log scale)")
    ax[0].legend(fontsize=9); ax[0].grid(alpha=.25)
    ax[1].set_ylabel("Drawdown (%)"); ax[1].set_title("Drawdowns"); ax[1].grid(alpha=.25)
    plt.tight_layout()

    here = os.path.dirname(os.path.abspath(__file__))
    plt.savefig(os.path.join(here, "index_vs_tsmom.png"), dpi=150, bbox_inches="tight")
    tab.to_csv(os.path.join(here, "index_vs_tsmom.csv"))
    print("\nwrote index_vs_tsmom.png + index_vs_tsmom.csv")


if __name__ == "__main__":
    main()
