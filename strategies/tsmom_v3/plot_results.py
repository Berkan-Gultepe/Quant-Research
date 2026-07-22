"""
Generate results.png for the v3 README — a 4-panel view built around the ONE
thing that makes v3 different from v2: the per-asset leverage cap.

  (1) Equity          — SPY vs v3 gross vs v3 net (log scale, honest)
  (2) The cap in action — max per-asset leverage per day, uncapped vs capped
  (3) Where the cap bites — distribution of uncapped per-asset leverage,
                            with the 10x line: the noisy tail that gets clipped
  (4) Underwater        — v3 drawdown curve, with MaxDD / Calmar / Ulcer

Run:  python plot_results.py   ->  writes results.png
(Data pulled live from Yahoo Finance, no API key.)
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from tsmom_v3 import (
    load_data, tsmom_position, net_returns, drawdown_metrics,
    TARGET_VOL, LOOKBACK, VOL_WINDOW, LEVERAGE_CAP, COST_RATE,
)

PURPLE, GREY, GREEN, RED, INDIGO = "#7c3aed", "#64748b", "#16a34a", "#dc2626", "#4f46e5"


def sharpe(r):
    return r.mean() / r.std() * np.sqrt(252)


def uncapped_position(close, log_returns):
    """v2-style position: vol-scaled, WITHOUT the clip."""
    signal = np.sign(close.pct_change(LOOKBACK, fill_method=None))
    vol    = log_returns.rolling(VOL_WINDOW).std() * np.sqrt(252)
    return (TARGET_VOL / vol) * signal


def main():
    close, log_returns = load_data()

    # --- capped (v3) ---
    pos_cap = tsmom_position(close, log_returns)
    gross   = (pos_cap.shift(1) * log_returns).mean(axis=1).dropna()
    net, turn, maxlev = net_returns(close, log_returns)
    dm = drawdown_metrics(net)

    # --- uncapped (v2) for the cap panels + drawdown comparison ---
    pos_unc  = uncapped_position(close, log_returns)
    net_unc  = (pos_unc.shift(1) * log_returns - COST_RATE * pos_unc.diff().abs()).mean(axis=1).dropna()
    dm_unc   = drawdown_metrics(net_unc)

    # SPY buy & hold on the same window
    spy = yf.download("SPY", start="2001-01-01", progress=False)["Close"].dropna()
    spy_ret = np.log(spy / spy.shift(1)).dropna().squeeze()
    common = gross.index.intersection(net.index).intersection(spy_ret.index)
    g, nt, spy_ret = gross.loc[common], net.loc[common], spy_ret.loc[common]

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    # (1) Equity: SPY vs gross vs net -------------------------------------
    ax[0, 0].plot(np.exp(spy_ret.cumsum()), color=GREY,   lw=1.6, label=f"SPY buy & hold     (Sharpe {sharpe(spy_ret):.2f})")
    ax[0, 0].plot(np.exp(g.cumsum()),       color=PURPLE, lw=1.8, label=f"TSMOM v3 gross     (Sharpe {sharpe(g):.2f})")
    ax[0, 0].plot(np.exp(nt.cumsum()),      color=GREEN,  lw=1.8, label=f"TSMOM v3 net 5bp   (Sharpe {sharpe(nt):.2f})")
    ax[0, 0].set_yscale("log")
    ax[0, 0].set_title("Equity — TSMOM v3 (gross & net) vs SPY, log scale")
    ax[0, 0].set_ylabel("Capital (start = 1)"); ax[0, 0].legend(fontsize=8); ax[0, 0].grid(alpha=.2)

    # (2) The cap in action — max per-asset leverage per day --------------
    lev_unc = pos_unc.abs().max(axis=1).loc[common]
    lev_cap = pos_cap.abs().max(axis=1).loc[common]
    ax[0, 1].plot(lev_unc, color=RED,   lw=1.0, alpha=.8, label=f"uncapped (v2)  peak {lev_unc.max():.0f}x")
    ax[0, 1].plot(lev_cap, color=GREEN, lw=1.2,            label=f"capped (v3)    peak {lev_cap.max():.0f}x")
    ax[0, 1].axhline(LEVERAGE_CAP, color=GREY, ls="--", lw=1, label=f"{LEVERAGE_CAP:.0f}x cap")
    ax[0, 1].set_yscale("log")
    ax[0, 1].set_title("The cap in action — max per-asset leverage per day")
    ax[0, 1].set_ylabel("leverage (x, log)"); ax[0, 1].set_xlabel("date")
    ax[0, 1].legend(fontsize=8); ax[0, 1].grid(alpha=.2)

    # (3) Where the cap bites — distribution of uncapped leverage ---------
    vals = pos_unc.abs().values.flatten()
    vals = vals[np.isfinite(vals) & (vals > 0)]
    clipped_share = (vals > LEVERAGE_CAP).mean() * 100
    bins = np.logspace(np.log10(0.01), np.log10(vals.max()), 60)
    ax[1, 0].hist(vals, bins=bins, color=INDIGO, alpha=.85)
    ax[1, 0].axvline(LEVERAGE_CAP, color=RED, ls="--", lw=1.5,
                     label=f"{LEVERAGE_CAP:.0f}x cap  —  clips {clipped_share:.1f}% of position-days")
    ax[1, 0].set_xscale("log")
    ax[1, 0].set_title("Where the cap bites — uncapped per-asset leverage")
    ax[1, 0].set_xlabel("required leverage per asset (x, log)")
    ax[1, 0].set_ylabel("count (asset-days)"); ax[1, 0].legend(fontsize=8); ax[1, 0].grid(alpha=.2)

    # (4) Underwater — v3 drawdown ----------------------------------------
    equity = (1 + nt).cumprod()
    dd = (equity / equity.cummax() - 1) * 100
    ax[1, 1].fill_between(dd.index, dd.values, 0, color=RED, alpha=.35)
    ax[1, 1].plot(dd.index, dd.values, color=RED, lw=1)
    ax[1, 1].set_title("Underwater — TSMOM v3 net drawdown")
    ax[1, 1].set_ylabel("drawdown (%)"); ax[1, 1].set_xlabel("date"); ax[1, 1].grid(alpha=.2)
    txt = (f"max drawdown : {dm['maxdd']*100:.1f}%\n"
           f"Calmar       : {dm['calmar']:.2f}\n"
           f"Ulcer index  : {dm['ulcer']:.2f}")
    ax[1, 1].text(0.02, 0.06, txt, transform=ax[1, 1].transAxes, fontsize=9,
                  family="monospace", va="bottom",
                  bbox=dict(boxstyle="round", fc="white", ec=GREY, alpha=.9))

    plt.tight_layout()
    plt.savefig("results.png", dpi=130, bbox_inches="tight")
    print("wrote results.png")
    print(f"  net Sharpe {sharpe(nt):.3f} | max lev {maxlev:.1f}x | "
          f"turnover {turn:.2f} | Calmar {dm['calmar']:.2f} | Ulcer {dm['ulcer']:.2f}")
    print(f"  cap clips {clipped_share:.1f}% of position-days")
    print("  --- v2 (uncapped) for the README table ---")
    print(f"  v2 CAGR {dm_unc['cagr']*100:.1f}% | MaxDD {dm_unc['maxdd']*100:.1f}% | "
          f"Calmar {dm_unc['calmar']:.2f} | Ulcer {dm_unc['ulcer']:.2f}")


if __name__ == "__main__":
    main()
