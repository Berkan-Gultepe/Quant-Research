"""
Late-Day Continuation from Leveraged-ETF Rebalancing — on ES futures.
=====================================================================
Author: Berkan Gültepe

STATUS: DEAD (arbitraged away). A REAL, significant edge from 2010-2018
        (short side, t = 3.17, Sharpe 1.16), gone after ~2019 (t = 0.11).
        A documented McLean-Pontiff decay, measured in my own data — not a
        signal that was noise from the start (that was ORB/ORR), but one
        that worked and got competed away once it became a known trade.

Hypothesis (structural / forced flow)
-------------------------------------
Leveraged AND inverse ETFs must reset their leverage to the daily target
every day. The re-balancing is ALWAYS in the same direction as the day's
move: on an up day they add exposure (buy), on a down day they cut it
(sell). This forced flow concentrates near the close and, on large-move
days, is a big fraction of market-on-close volume (Cheng & Madhavan 2009
report 16-75% of MOC volume for a 1-15% move). => on big-move days the
last half hour should CONTINUE the day's direction.

Design
------
  Signal window : 09:30 -> 15:30 ET  (how the day moved)
  Trade window  : 15:30 -> 16:00 ET  (the last half hour we try to capture)
  Universe      : big-move days only (day's move in the extreme 10% tails)
  Direction     : continuation -> long big up-days, short big down-days
  Cost          : 1.3 ticks round-turn (same assumption as ORB/ORR)

No look-ahead: the 10%/90% signal threshold is an EXPANDING-window quantile
computed from PAST days only (252-day burn-in, shifted by one day). Today's
trade decision never uses today's or future distribution.

Key results (ES, Databento 1-min, 2010-2026, 4021 days)
-------------------------------------------------------
  Short side, 2010-2018 : net +9.54 ticks | t +3.17 | p 0.002 | Sharpe 1.16   REAL
  Short side, 2019-2026 : net +0.57 ticks | t +0.11 | p 0.912 | Sharpe 0.04   DEAD
  Long side (all)       : net -0.97 ticks | t -0.39                            never worked
The edge lived only on the SHORT side (big down days = biggest, most violent
re-balancing) and only until ~2018. It briefly reappeared in the 2022 high-vol
bear (big down days were frequent again) but is not a reliable, tradeable edge.

Documented and archived KW32, August 2026 — reference, not for live trading.
"""
import datetime as dt
import numpy as np
import pandas as pd
from scipy import stats

# ---------------- Config ----------------
DATA_PATH  = r"es_nq_frontmonth_1min.parquet"   # cleaned Databento ES/NQ front-month (1-min)
INSTRUMENT = "ES"
TICK       = 0.25
COST_TICKS = 1.3        # round-turn: spread + slippage + commission
CUT        = dt.time(15, 30)   # entry time (last half hour = CUT -> 16:00)
TAIL       = 0.10       # trade only the extreme 10% tails of the day's move
BURN_IN    = 252        # days used to seed the expanding threshold before trading
SPLIT_YEAR = 2019       # recency split: < SPLIT_YEAR vs >= SPLIT_YEAR


def build_daily(path, instrument=INSTRUMENT):
    """Per-day table: open (09:30), cut (15:30 entry), close (16:00 exit) + returns."""
    df = pd.read_parquet(path, columns=["ts_event", "open", "close", "volume", "instrument"])
    x  = df[df["instrument"] == instrument].copy()
    x["et"]   = x["ts_event"].dt.tz_convert("America/New_York")
    x["date"] = x["et"].dt.date
    x["time"] = x["et"].dt.time
    rth = x[(x["time"] >= dt.time(9, 30)) & (x["time"] < dt.time(16, 0))].sort_values("ts_event")

    rows = []
    for d, day in rth.groupby("date"):
        day = day.sort_values("ts_event")
        cut = day[day["time"] == CUT]
        if len(cut) == 0 or len(day) < 30:
            continue
        p_open, p_cut, p_close = day.iloc[0]["open"], cut.iloc[0]["open"], day.iloc[-1]["close"]
        rows.append({"date": d,
                     "signal_ret": p_cut / p_open - 1,     # day up to 15:30
                     "trade_ret":  p_close / p_cut - 1,     # last half hour
                     "p_cut": p_cut, "p_close": p_close})
    daily = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    daily["dt"]   = pd.to_datetime(daily["date"])
    daily["jahr"] = daily["dt"].dt.year
    return daily


def run(daily):
    """Expanding-window threshold (no look-ahead), continuation trade, P&L in ticks."""
    lo = daily["signal_ret"].expanding(min_periods=BURN_IN).quantile(TAIL).shift(1)
    hi = daily["signal_ret"].expanding(min_periods=BURN_IN).quantile(1 - TAIL).shift(1)
    daily = daily.assign(lo=lo, hi=hi)
    daily["trade"] = (daily["signal_ret"] <= daily["lo"]) | (daily["signal_ret"] >= daily["hi"])

    tr = daily[daily["trade"]].copy()
    tr["side"]      = np.sign(tr["signal_ret"])                       # +1 long, -1 short
    tr["pnl_ticks"] = tr["side"] * (tr["p_close"] - tr["p_cut"]) / TICK
    tr["net"]       = tr["pnl_ticks"] - COST_TICKS
    return tr


def report(g, label):
    if len(g) < 5:
        print(f"{label:32} n={len(g)}  (too few)"); return
    t, p = stats.ttest_1samp(g["net"], 0)
    yrs  = max((g["dt"].max() - g["dt"].min()).days / 365, 1e-9)
    shp  = g["net"].mean() / g["net"].std() * np.sqrt(len(g) / yrs)
    print(f"{label:32} n={len(g):4}  gross {g['pnl_ticks'].mean():+6.2f}  "
          f"net {g['net'].mean():+6.2f}  t={t:+.2f}  p={p:.3f}  Sharpe={shp:+.2f}")


def main():
    daily = build_daily(DATA_PATH)
    print(f"Days: {len(daily)}\n")
    tr = run(daily)
    short = tr[tr["side"] == -1]
    long_ = tr[tr["side"] == 1]

    print("=== Full sample ===")
    report(tr,   "Both sides")
    report(short, "SHORT (big down days)")
    report(long_, "LONG  (big up days)")

    print(f"\n=== Recency split (short side, cut {SPLIT_YEAR}) ===")
    report(short[short["jahr"] <  SPLIT_YEAR], f"SHORT < {SPLIT_YEAR}")
    report(short[short["jahr"] >= SPLIT_YEAR], f"SHORT >= {SPLIT_YEAR}")


if __name__ == "__main__":
    main()
