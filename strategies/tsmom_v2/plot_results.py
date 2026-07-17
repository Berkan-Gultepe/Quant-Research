"""
Generate results.png for the README — a 4-panel validation overview:
  (1) Equity      — SPY vs TSMOM v2 gross vs net (log scale, honest)
  (2) Monte Carlo — block-bootstrapped equity paths + the real (net) backtest
  (3) Cost-sensitivity — net Sharpe across transaction-cost assumptions
  (4) Parameter sensitivity heatmap — Sharpe across the lookback x vol-window grid

Run:  python plot_results.py   ->  writes results.png
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from tsmom_v2 import load_data, tsmom_returns
from validation import net_of_costs, sensitivity

BLOCK, N_SIMS, N_PLOT = 20, 10_000, 300
PURPLE, GREY, GREEN, RED, INDIGO = "#7c3aed", "#64748b", "#16a34a", "#dc2626", "#4f46e5"


def sharpe(r):
    return r.mean() / r.std() * np.sqrt(252)


def bootstrap_path(x, n, block, rng):
    path = []
    while len(path) < n:
        s = rng.integers(0, n - block)
        path.extend(x[s:s + block])
    return np.array(path[:n])


def main():
    close, log_returns = load_data()
    gross = tsmom_returns(close, log_returns)
    net, _ = net_of_costs(close, log_returns, cost_rate=0.0005)

    # SPY buy & hold on the same window
    spy = yf.download("SPY", start="2001-01-01", progress=False)["Close"].dropna()
    spy_ret = np.log(spy / spy.shift(1)).dropna().squeeze()
    common = gross.index.intersection(net.index).intersection(spy_ret.index)
    g, nt, spy_ret = gross.loc[common], net.loc[common], spy_ret.loc[common]

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    # (1) Equity: SPY vs gross vs net -------------------------------------
    ax[0, 0].plot(np.exp(spy_ret.cumsum()), color=GREY,   lw=1.6, label=f"SPY buy & hold   (Sharpe {sharpe(spy_ret):.2f})")
    ax[0, 0].plot(np.exp(g.cumsum()),       color=PURPLE, lw=1.8, label=f"TSMOM v2 gross    (Sharpe {sharpe(g):.2f})")
    ax[0, 0].plot(np.exp(nt.cumsum()),      color=GREEN,  lw=1.8, label=f"TSMOM v2 net 5bp  (Sharpe {sharpe(nt):.2f})")
    ax[0, 0].set_yscale("log")
    ax[0, 0].set_title("Equity — TSMOM v2 (gross & net) vs SPY, log scale")
    ax[0, 0].set_ylabel("Capital (start = 1)"); ax[0, 0].legend(fontsize=8); ax[0, 0].grid(alpha=.2)

    # (2) Monte Carlo cone (net) ------------------------------------------
    x = nt.values; n = len(x); rng = np.random.default_rng(7)
    for _ in range(N_PLOT):
        ax[0, 1].plot(np.exp(np.cumsum(bootstrap_path(x, n, BLOCK, rng))), color=INDIGO, alpha=0.04)
    ax[0, 1].plot(np.exp(np.cumsum(x)), color=RED, lw=2, label="real backtest (net)")
    ax[0, 1].set_yscale("log")
    ax[0, 1].set_title(f"Monte Carlo — {N_PLOT} of {N_SIMS:,} block-bootstrapped paths")
    ax[0, 1].set_xlabel("trading days"); ax[0, 1].legend(fontsize=8); ax[0, 1].grid(alpha=.2)

    # (3) Cost-sensitivity ------------------------------------------------
    bps = [0, 3, 5, 10, 15, 20]
    sh  = [sharpe(net_of_costs(close, log_returns, cost_rate=b / 1e4)[0]) for b in bps]
    ax[1, 0].plot(bps, sh, "-o", color=GREEN, lw=1.8)
    ax[1, 0].axhline(0, color=GREY, lw=.8)
    ax[1, 0].axvline(5, color=RED, ls="--", lw=1, alpha=.7)
    for b, s in zip(bps, sh):
        ax[1, 0].annotate(f"{s:.2f}", (b, s), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax[1, 0].set_title("Cost-sensitivity — net Sharpe vs transaction cost")
    ax[1, 0].set_xlabel("cost per trade (bp)"); ax[1, 0].set_ylabel("net Sharpe"); ax[1, 0].grid(alpha=.2)

    # (4) Parameter sensitivity heatmap -----------------------------------
    grid = sensitivity(close, log_returns).astype(float)   # index=lookbacks, cols=vol_windows
    im = ax[1, 1].imshow(grid.values, cmap="YlGn", aspect="auto")
    ax[1, 1].set_xticks(range(len(grid.columns))); ax[1, 1].set_xticklabels(grid.columns)
    ax[1, 1].set_yticks(range(len(grid.index)));   ax[1, 1].set_yticklabels(grid.index)
    ax[1, 1].set_xlabel("vol window (days)"); ax[1, 1].set_ylabel("lookback (days)")
    ax[1, 1].set_title("Parameter sensitivity — Sharpe across the grid")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax[1, 1].text(j, i, f"{grid.values[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax[1, 1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig("results.png", dpi=130, bbox_inches="tight")
    print("wrote results.png")


if __name__ == "__main__":
    main()
