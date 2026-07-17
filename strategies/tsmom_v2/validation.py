"""
TSMOM v2 — validation suite
===========================
Three tests that separate a real edge from luck/overfitting:

  1. IS/OOS split         — does the edge survive on data never used to develop it?
  2. Parameter sensitivity— does it hold across a grid, or only at one lucky setting?
  3. Monte Carlo bootstrap— how much does the result depend on the lucky ORDER of days?
  4. Transaction costs     — does the edge survive turnover * cost (KW29)?
  5. Deflated Sharpe       — does it survive the multiple-testing correction (KW29)?

Run after tsmom_v2.py.

Key results (KW28):
  IS 2001-2015 : Sharpe 0.80 | t 3.11 | p 0.0019
  OOS 2016-2026: Sharpe 0.69 | t 2.25 | p 0.0247   (14% decay — healthy)
  Sensitivity  : all 25 cells positive (0.42-0.80), plateau at lookback 126-252,
                 vol-window nearly irrelevant, chosen 252/60 sits inside the plateau.
  Monte Carlo  : Sharpe median 0.77 (backtest 0.76 = typical, not lucky),
                 P(Sharpe>0)=100%, worst-5% max-drawdown -26%  <- kill-switch level.
  Costs (KW29) : net Sharpe 0.61 (5 bp) | t 3.08 | turnover 19.55/yr — survives (conditional).
  Deflated (KW29): DSR 96.6% | deflated t 1.83 (N=25, s_a 0.124) — passes multiple-testing.

Cardinal rule: OOS is used ONCE. If you peek, tweak, and re-test on the same OOS,
it becomes in-sample. (Lopez de Prado, Ch. 11-12.)
"""

import numpy as np
import pandas as pd
from scipy import stats

from tsmom_v2 import (load_data, tsmom_returns, metrics,
                      LOOKBACK, VOL_WINDOW, TARGET_VOL)


# --- 1. IS / OOS split -----------------------------------------------------
def is_oos_split(r, split="2016-01-01"):
    r_is  = r[r.index <  split]
    r_oos = r[r.index >= split]
    return {"IS": metrics(r_is), "OOS": metrics(r_oos)}


# --- 2. Parameter sensitivity ---------------------------------------------
def sensitivity(close, log_returns,
                lookbacks=(126, 189, 252, 315, 378),
                vol_windows=(20, 40, 60, 90, 120)):
    grid = pd.DataFrame(index=lookbacks, columns=vol_windows, dtype=float)
    for lb in lookbacks:
        for vw in vol_windows:
            r = tsmom_returns(close, log_returns, lookback=lb, vol_window=vw)
            grid.loc[lb, vw] = r.mean() / r.std() * np.sqrt(252)
    return grid.round(2)


# --- 3. Monte Carlo (block bootstrap) -------------------------------------
def monte_carlo(r, block=20, n_sims=10_000, seed=7):
    rng = np.random.default_rng(seed)
    x = r.dropna().values
    n = len(x)
    sharpes, maxdds = [], []
    for _ in range(n_sims):
        path = []
        while len(path) < n:
            s = rng.integers(0, n - block)
            path.extend(x[s:s + block])
        p = np.array(path[:n])
        sharpes.append(p.mean() / p.std() * np.sqrt(252))
        eq = np.exp(np.cumsum(p))
        maxdds.append((eq / np.maximum.accumulate(eq) - 1).min())
    sharpes, maxdds = np.array(sharpes), np.array(maxdds)
    return {
        "sharpe_median": round(float(np.median(sharpes)), 2),
        "sharpe_p5":     round(float(np.percentile(sharpes, 5)), 2),
        "sharpe_p95":    round(float(np.percentile(sharpes, 95)), 2),
        "p_sharpe_gt0":  round(float((sharpes > 0).mean()), 3),
        "maxdd_median":  round(float(np.median(maxdds)), 3),
        "maxdd_worst5":  round(float(np.percentile(maxdds, 5)), 3),   # kill-switch input
    }


# --- 4. Transaction costs (KW29) ------------------------------------------
def net_of_costs(close, log_returns, cost_rate=0.0005,
                 lookback=LOOKBACK, vol_window=VOL_WINDOW, target_vol=TARGET_VOL):
    """
    Net-of-cost portfolio returns + annualised turnover.
    Not the cost rate kills an edge, the TURNOVER does: cost = turnover * rate.
    cost_rate = per unit traded (0.0005 = 5 bp).
    """
    signal   = np.sign(close.pct_change(lookback, fill_method=None))
    vol      = log_returns.rolling(vol_window).std() * np.sqrt(252)
    position = (target_vol / vol) * signal
    turnover = position.diff().abs()
    gross    = position.shift(1) * log_returns
    net      = (gross - cost_rate * turnover).mean(axis=1).dropna()
    annual_turnover = (turnover.sum(axis=1) / position.shape[1]).mean() * 252
    return net, float(annual_turnover)


# --- 5. Deflated Sharpe Ratio (KW29) --------------------------------------
def deflated_sharpe(net_sharpe, grid_sharpe_std, n_trials, n_days):
    """
    Bailey & Lopez de Prado (2014). Corrects the Sharpe for MULTIPLE TESTING:
    the best of N searched settings beats zero partly by luck. Instead of testing
    against 0, test against SR* = the best Sharpe expected by luck across n_trials.
    Returns (deflated_t, DSR). DSR > 0.95 => passes.
    """
    gamma = 0.5772156649
    sr_p  = net_sharpe    / np.sqrt(252)       # per-day units
    s_p   = grid_sharpe_std / np.sqrt(252)
    z = (1 - gamma) * stats.norm.ppf(1 - 1/n_trials) + gamma * stats.norm.ppf(1 - 1/(n_trials*np.e))
    sr_star = s_p * z                          # expected max Sharpe under H0
    dt  = (sr_p - sr_star) * np.sqrt(n_days - 1)
    return round(float(dt), 2), round(float(stats.norm.cdf(dt)), 3)


if __name__ == "__main__":
    close, log_returns = load_data()
    r = tsmom_returns(close, log_returns)

    print("== IS/OOS ==")
    for k, v in is_oos_split(r).items():
        print(f"  {k}: {v}")

    print("\n== Sensitivity (Sharpe) ==")
    print(sensitivity(close, log_returns))

    print("\n== Monte Carlo (10k block-bootstrap) ==")
    print(monte_carlo(r))

    print("\n== Transaction costs (KW29) ==")
    net, turnover = net_of_costs(close, log_returns, cost_rate=0.0005)
    print(f"  Turnover/yr: {turnover:.2f} | Net (5 bp): {metrics(net)}")

    print("\n== Deflated Sharpe (KW29, multiple-testing correction) ==")
    grid = sensitivity(close, log_returns)
    s_a  = float(grid.values.std(ddof=1))
    dt, dsr = deflated_sharpe(metrics(net)["sharpe"], s_a, n_trials=grid.size, n_days=len(net))
    print(f"  grid s_a: {s_a:.3f} | deflated t: {dt} | DSR: {dsr}  (>0.95 = passes)")

    print("\nKill-switch -> worst-5% drawdown (~-26%), NOT the -16.5% backtest.")
