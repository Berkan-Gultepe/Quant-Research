"""
Generate results.png for the README:
  Left  — TSMOM v2 equity vs SPY buy-and-hold (log scale, same period)
  Right — Monte Carlo cone: 10k block-bootstrapped equity paths + real backtest

Run:  python plot_results.py   ->  writes results.png
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

from tsmom_v2 import load_data, tsmom_returns

BLOCK, N_SIMS, N_PLOT = 20, 10_000, 300


def bootstrap_path(x, n, block, rng):
    path = []
    while len(path) < n:
        s = rng.integers(0, n - block)
        path.extend(x[s:s + block])
    return np.array(path[:n])


def main():
    close, log_returns = load_data()
    r = tsmom_returns(close, log_returns)

    # SPY buy & hold on the same window
    spy = yf.download("SPY", start="2001-01-01", progress=False)["Close"].dropna()
    spy_ret = np.log(spy / spy.shift(1)).dropna().squeeze()
    common = r.index.intersection(spy_ret.index)
    r, spy_ret = r.loc[common], spy_ret.loc[common]

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))

    # --- Left: equity vs SPY ---
    ax[0].plot(np.exp(r.cumsum()), label="TSMOM v2", color="#7c3aed", lw=2)
    ax[0].plot(np.exp(spy_ret.cumsum()), label="SPY buy & hold", color="#64748b", lw=2)
    ax[0].set_yscale("log"); ax[0].set_title("Equity — TSMOM v2 vs SPY (log scale)")
    ax[0].set_ylabel("Capital (start = 1)"); ax[0].legend(); ax[0].grid(alpha=.2)

    # --- Right: Monte Carlo cone ---
    x = r.dropna().values; n = len(x); rng = np.random.default_rng(7)
    for _ in range(N_PLOT):
        ax[1].plot(np.exp(np.cumsum(bootstrap_path(x, n, BLOCK, rng))),
                   color="#4f46e5", alpha=0.04)
    ax[1].plot(np.exp(np.cumsum(x)), color="red", lw=2, label="real backtest")
    ax[1].set_yscale("log"); ax[1].set_title(f"Monte Carlo — {N_PLOT} of {N_SIMS:,} bootstrapped paths")
    ax[1].set_xlabel("trading days"); ax[1].legend(); ax[1].grid(alpha=.2)

    plt.tight_layout()
    plt.savefig("results.png", dpi=130, bbox_inches="tight")
    print("wrote results.png")


if __name__ == "__main__":
    main()
