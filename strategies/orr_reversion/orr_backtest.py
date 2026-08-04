"""
ORR — Opening Range Reversion (False-Breakout Fade) on ES futures.

STATUS: DEAD — the signal has no directional edge.
        Stripped to symmetric risk/reward (neutral skew), win rate = 48.6% over 3411 trades
        (SE ~0.86%) -> not distinguishable from a coin flip. No exit/filter tuning fixes that.

Hypothesis: opening-range breakouts are mostly false (stop-runs with no real order flow behind
them). Fade the break, expecting reversion back into the range. This is the mirror of ORB, which
*followed* the breakout and also had no edge (gross Sharpe ~0.15).

Data: Databento GLBX.MDP3, ES 1-min OHLCV, front-month by volume, RTH 09:30-16:00 ET.
      (Not shipped in the repo -- point DATA_PATH at your cleaned front-month parquet.)

The four config flags below reproduce the four diagnostic stages we walked through:
  v1   VWAP target + volume filter        -> gross -1.95 t | real WR 37% | skew -0.80
  v1.5 fixed half-range target            -> gross -0.70 t | WR 42%      | skew -0.41
  v1.6 + symmetric half-range stop        -> gross -0.77 t | WR 48.1%    | skew +0.02
  v1.7 + volume filter removed (3411 tr.) -> gross -0.26 t | WR 48.6%    | skew +0.03  <-- decisive

Key technique: to test whether a SIGNAL has an edge, strip it to symmetric R:R and read the
win rate against 50%. This isolates the signal from exit curve-fitting.

Documented and abandoned KW32, August 2026. Archived for reference — not for live trading.
"""
import datetime as dt
import numpy as np
import pandas as pd
from scipy.stats import skew

# ---------------- Config ----------------
DATA_PATH      = r"es_nq_frontmonth_1min.parquet"  # cleaned Databento ES front-month (1-min)
N_RETURN       = 5           # bars (minutes) allowed for price to return into the range
TICK           = 0.25        # ES tick size
COST_TICKS     = 1.3         # round-turn cost in ticks (spread + slippage + commission)

VOLUME_FILTER  = False       # require return-bar volume > VOL_MULT * OR-median volume
VOL_MULT       = 1.5
TARGET_MODE    = "half_range"  # "half_range" (fixed distance) or "vwap" (dynamic)
SYMMETRIC_STOP = True          # True: stop = half range (symmetric); False: stop = breakout extreme


def load_es(path):
    """Load ES front-month, build RTH bars, running session VWAP, opening range & volume baseline."""
    df = pd.read_parquet(path)
    es = df[df["instrument"] == "ES"].copy()
    es["et"]   = es["ts_event"].dt.tz_convert("America/New_York")
    es["date"] = es["et"].dt.date
    es["time"] = es["et"].dt.time
    rth = es[(es["time"] >= dt.time(9, 30)) & (es["time"] < dt.time(16, 0))].sort_values(["date", "ts_event"]).copy()

    tp = (rth["high"] + rth["low"] + rth["close"]) / 3
    rth["vwap"] = (tp * rth["volume"]).groupby(rth["date"]).cumsum() / rth["volume"].groupby(rth["date"]).cumsum()

    or_win = rth[rth["time"] < dt.time(10, 0)]
    or_lvl = or_win.groupby("date").agg(or_high=("high", "max"), or_low=("low", "min"))
    or_vol = or_win.groupby("date")["volume"].median().rename("or_vol_med")
    rth = rth.merge(or_vol, on="date", how="left")
    return rth, or_lvl


def run_day(day, oh, ol):
    """One trading day: find first false breakout that returns into the range, fade it, exit."""
    rng, vbase = oh - ol, day["or_vol_med"].iloc[0]
    win = day[(day["time"] >= dt.time(10, 0)) & (day["time"] < dt.time(11, 0))].reset_index(drop=True)

    setup = None
    for i in range(len(win)):
        b = win.iloc[i]
        brk = "up" if b["high"] > oh else "down" if b["low"] < ol else None
        if brk is None:
            continue
        for j in range(1, N_RETURN + 1):
            if i + j >= len(win):
                break
            rb = win.iloc[i + j]
            back_in = ol <= rb["close"] <= oh
            vol_ok  = (not VOLUME_FILTER) or (rb["volume"] > VOL_MULT * vbase)
            if back_in and vol_ok:
                side  = "short" if brk == "up" else "long"      # FADE = opposite direction
                entry = rb["close"]
                if TARGET_MODE == "half_range":
                    target = entry - 0.5 * rng if side == "short" else entry + 0.5 * rng
                else:
                    target = None  # dynamic VWAP, resolved in the exit loop
                if SYMMETRIC_STOP:
                    stop = entry + 0.5 * rng if side == "short" else entry - 0.5 * rng
                else:
                    seg  = win.iloc[i:i + j + 1]
                    stop = seg["high"].max() if side == "short" else seg["low"].min()  # breakout extreme
                setup = dict(rev_time=rb["time"], side=side, entry=entry, stop=stop, target=target)
                break
        if setup:
            break
    if setup is None:
        return None

    nach = day[(day["time"] > setup["rev_time"]) & (day["time"] < dt.time(12, 0))]
    if len(nach) == 0:
        return None
    ex, why = None, None
    for _, bar in nach.iterrows():
        tgt = setup["target"] if setup["target"] is not None else bar["vwap"]  # dynamic VWAP if half_range off
        if setup["side"] == "short":
            if bar["high"] >= setup["stop"]: ex, why = setup["stop"], "stop";   break
            if bar["low"]  <= tgt:           ex, why = tgt,           "target"; break
        else:
            if bar["low"]  <= setup["stop"]: ex, why = setup["stop"], "stop";   break
            if bar["high"] >= tgt:           ex, why = tgt,           "target"; break
    if ex is None:
        ex, why = nach.iloc[-1]["close"], "timestop"

    pnl = (setup["entry"] - ex) if setup["side"] == "short" else (ex - setup["entry"])
    return dict(date=day["date"].iloc[0], side=setup["side"], why=why, pnl_ticks=pnl / TICK)


def main():
    rth, or_lvl = load_es(DATA_PATH)
    bars = dict(tuple(rth.groupby("date")))
    trades = pd.DataFrame([r for r in (run_day(bars[d], or_lvl.loc[d, "or_high"], or_lvl.loc[d, "or_low"])
                                       for d in or_lvl.index) if r])
    net = trades["pnl_ticks"] - COST_TICKS
    yrs = (pd.Timestamp(trades["date"].max()) - pd.Timestamp(trades["date"].min())).days / 365
    sharpe = (net.mean() / net.std()) * np.sqrt(len(trades) / yrs)

    print(f"Trades:        {len(trades)}  {trades['why'].value_counts().to_dict()}")
    print(f"Gross avg:     {trades['pnl_ticks'].mean():+.2f} ticks")
    print(f"Net avg:       {net.mean():+.2f} ticks")
    print(f"Win rate:      {(net > 0).mean():.1%}   (SE ~{100 * np.sqrt(0.25 / len(trades)):.2f}%)")
    print(f"Skew:          {skew(net):+.2f}")
    print(f"Sharpe (ann.): {sharpe:+.2f}")


if __name__ == "__main__":
    main()
