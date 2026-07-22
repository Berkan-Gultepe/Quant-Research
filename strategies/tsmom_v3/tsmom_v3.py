"""
Time-Series Momentum (TSMOM) v3 — tradable, per-asset leverage cap
==================================================================
Paper : Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", JFE 104(2).
Author: Berkan Gültepe

Why v3 exists
-------------
v2 cleared every statistical hurdle but FAILED implementability (hurdle 6):
vol-scaling on a quiet asset (SHY) asked for up to ~58x leverage on a single
position (~45x gross notional) — not fundable with any broker or futures
account.

v3 adds ONE line: a per-asset leverage cap. The cap is NOT optimised — it is
derived from the outside constraint that actually binds: broker/futures margin
(~5-10% initial margin -> ~10-20x max per asset). We take 10x as a hard cap.

The result (KW30, 2026-07-22, net of 5 bp):
    max leverage      58.4x  ->  10.0x
    net Sharpe        0.610  ->  0.618   (t = 3.12; unchanged — slightly better)
    turnover / yr     19.55  ->  16.11   (LOWER — the capped SHY churn was noise)
    Calmar            0.27   (SPY 0.16)
    Ulcer index       5.82   (very calm)

Key lesson: the extreme leverage on quiet assets was never the source of
return — huge notional, tiny risk contribution. Capping it costs nothing and
even lowers turnover, because the most expensive, most illiquid churn
disappears. "Gross notional is not risk."

The cap is a CONSTRAINT you must respect, not a parameter you optimise — so it
does not add to the multiple-testing count N (deflated t stays 1.83).
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "FXI",
            "TLT", "IEF", "SHY", "LQD", "HYG", "EMB",
            "GLD", "SLV", "USO", "UNG", "DBA", "DBB",
            "UUP", "FXE", "FXY", "FXB", "FXA"]

TARGET_VOL   = 0.15
LOOKBACK     = 252      # 12 months
VOL_WINDOW   = 60       # ~3 months
LEVERAGE_CAP = 10.0     # per-asset, from broker/futures margin — NOT optimised
COST_RATE    = 0.0005   # 5 bp per unit traded (assumption, not a measurement)


def load_data(start="2000-01-01"):
    data = yf.download(UNIVERSE, start=start, progress=False)
    close = data["Close"]
    log_returns = np.log(close / close.shift(1)).dropna(how="all")
    return close, log_returns


def tsmom_position(close, log_returns):
    """Vol-scaled position WITH the per-asset leverage cap — the only change vs v2."""
    signal   = np.sign(close.pct_change(LOOKBACK, fill_method=None))
    vol      = log_returns.rolling(VOL_WINDOW).std() * np.sqrt(252)
    position = (TARGET_VOL / vol) * signal
    return position.clip(-LEVERAGE_CAP, LEVERAGE_CAP)          # <- the cap


def net_returns(close, log_returns, cost_rate=COST_RATE):
    pos      = tsmom_position(close, log_returns)
    turnover = pos.diff().abs()
    gross    = pos.shift(1) * log_returns                       # shift the POSITION
    net      = (gross - cost_rate * turnover).mean(axis=1).dropna()
    ann_turn = (turnover.sum(axis=1) / pos.shape[1]).mean() * 252
    return net, float(ann_turn), float(pos.abs().max().max())


def drawdown_metrics(net):
    equity = (1 + net).cumprod()
    cagr   = equity.iloc[-1] ** (252 / len(net)) - 1
    dd     = equity / equity.cummax() - 1
    maxdd  = dd.min()
    calmar = cagr / abs(maxdd)
    ulcer  = np.sqrt((dd ** 2).mean()) * 100
    return dict(cagr=cagr, maxdd=maxdd, calmar=calmar, ulcer=ulcer)


def main():
    close, log_returns = load_data()
    net, turn, maxlev = net_returns(close, log_returns)
    sharpe = net.mean() / net.std() * np.sqrt(252)
    t      = sharpe * np.sqrt(len(net) / 252)
    dm     = drawdown_metrics(net)

    print(f"max leverage per asset : {maxlev:.1f}x  (cap = {LEVERAGE_CAP:.0f}x)")
    print(f"net Sharpe (5 bp)      : {sharpe:.3f}   t = {t:.2f}")
    print(f"turnover / year        : {turn:.2f}")
    print(f"CAGR                   : {dm['cagr']*100:.1f}%")
    print(f"max drawdown           : {dm['maxdd']*100:.1f}%")
    print(f"Calmar                 : {dm['calmar']:.2f}")
    print(f"Ulcer index            : {dm['ulcer']:.2f}")


if __name__ == "__main__":
    main()
