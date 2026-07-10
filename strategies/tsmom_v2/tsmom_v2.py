"""
Time-Series Momentum (TSMOM) v2 — honest re-validation
======================================================
Paper : Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", JFE 104(2).
Author: Berkan Gültepe

Context
-------
The original TSMOM implementation carried a look-ahead bug (the return was
shifted instead of the position), inflating the Sharpe to 1.86. This v2 is the
corrected, honest rebuild on a broadened, growing 24-asset universe.

Validation status (KW28, 2026-07-09/10, all GROSS of costs):
    Hurdle 1  Significance : Sharpe 0.76 | t 3.83 | p 1.3e-4 | CI [+2.9%, +8.9%]  PASS
    Hurdle 2  Robustness   : IS 0.80 / OOS 0.69 (14% decay) | 5x5 sensitivity plateau  PASS
    Monte Carlo (10k block-bootstrap): P(Sharpe>0)=100%, backtest = median,
                                       worst-5% drawdown -26% (<- kill-switch calibration)
    Hurdle 3  Costs (KW29) : OPEN — the decisive test.

The single most important fix (never forget):
    Strategy_Returns = position.shift(1) * log_returns     # decide today, earn tomorrow
    # NOT: position * log_returns.shift(1)                  # <- look-ahead bug
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats

# --- 1. Data: broad, growing universe -------------------------------------
UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "FXI",
            "TLT", "IEF", "SHY", "LQD", "HYG", "EMB",
            "GLD", "SLV", "USO", "UNG", "DBA", "DBB",
            "UUP", "FXE", "FXY", "FXB", "FXA"]

TARGET_VOL = 0.15
LOOKBACK   = 252     # 12 months
VOL_WINDOW = 60      # ~3 months


def load_data(start="2000-01-01"):
    data = yf.download(UNIVERSE, start=start, progress=False)
    close = data["Close"]                                       # already adjusted
    log_returns = np.log(close / close.shift(1)).dropna(how="all")   # NOT dropna() — would behead history
    return close, log_returns


def tsmom_returns(close, log_returns, lookback=LOOKBACK, vol_window=VOL_WINDOW, target_vol=TARGET_VOL):
    """Return the daily equal-weighted portfolio return series (one number per day)."""
    signal   = np.sign(close.pct_change(lookback))
    vol      = log_returns.rolling(vol_window).std() * np.sqrt(252)
    position = (target_vol / vol) * signal
    strat    = position.shift(1) * log_returns                  # <- the shift-rule
    return strat.mean(axis=1).dropna()


def metrics(r):
    r = r.dropna()
    sharpe = r.mean() / r.std() * np.sqrt(252)
    t, p   = stats.ttest_1samp(r, 0)
    eq     = np.exp(r.cumsum())
    maxdd  = (eq / eq.cummax() - 1).min()
    return dict(sharpe=round(float(sharpe), 2), t=round(float(t), 2),
                p=float(p), max_dd=round(float(maxdd), 3), n=len(r))


if __name__ == "__main__":
    close, log_returns = load_data()
    r = tsmom_returns(close, log_returns)

    # sanity check BEFORE metrics (start date, length)
    print("Start:", r.index[0].date(), "| Ende:", r.index[-1].date(), "| Tage:", len(r))
    print("Kennzahlen (brutto):", metrics(r))
