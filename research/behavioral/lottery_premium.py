# 0DTE lottery premium: implied vs realized ITM rates, 1068 days (2022-2026)
# Paste the day-loop + aggregation here (from KW34 Tue notebook).
import pandas as pd, numpy as np, glob, os, re
from collections import defaultdict

A   = r"D:\Theta-raw\SPXW\trade_quote"
SPX = r"D:\Theta-raw\underlying\spx"
OUT = r"C:\Users\Berkan\Documents\Quant_data\data\features\lottery\lottery_daily.csv"
MULTI   = {130, 131, 134, 137}
BUCKETS = [(0.5, 1.0), (1.0, 2.0), (2.0, 5.0)]
COLS    = ["trade_timestamp", "condition", "bid", "ask", "strike", "right"]
os.makedirs(os.path.dirname(OUT), exist_ok=True)

by_day = defaultdict(list)
for f in glob.glob(os.path.join(A, "*")):
    m = re.search(r"(20\d{6})", os.path.basename(f))
    if m: by_day[m.group(1)].append(f)
days = sorted(by_day)

rows = []
for i, day in enumerate(days):
    try:
        spx_f = glob.glob(os.path.join(SPX, f"*{day}*"))
        if not spx_f: continue
        spx  = pd.read_parquet(spx_f[0])
        tcol = [c for c in spx.columns if "time" in c.lower()][0]
        pcol = [c for c in spx.columns if c.lower() in ("price","close","last")][0]
        spx[tcol] = pd.to_datetime(spx[tcol])
        ref   = spx.loc[spx[tcol].dt.time <= pd.Timestamp("13:00:00").time(), pcol].iloc[-1]
        close = spx[pcol].iloc[-1]

        df = pd.concat([pd.read_parquet(f, columns=COLS) for f in by_day[day]])
        df["trade_timestamp"] = pd.to_datetime(df["trade_timestamp"])
        df = df[df["trade_timestamp"].dt.time <= pd.Timestamp("13:00:00").time()]
        df = df[~df["condition"].isin(MULTI)]
        df["mid"] = (df["bid"] + df["ask"]) / 2
        snap = df.sort_values("trade_timestamp").groupby(["strike","right"]).tail(1)

        for side in ("PUT", "CALL"):
            sub = snap[snap["right"] == side].copy()
            if side == "PUT":
                sub = sub[sub["strike"] < ref]
                sub["otm_pct"] = (ref - sub["strike"]) / ref * 100
                sub["payout"]  = np.maximum(sub["strike"] - close, 0)
            else:
                sub = sub[sub["strike"] > ref]
                sub["otm_pct"] = (sub["strike"] - ref) / ref * 100
                sub["payout"]  = np.maximum(close - sub["strike"], 0)
            for lo, hi in BUCKETS:
                b = sub[(sub["otm_pct"] >= lo) & (sub["otm_pct"] < hi)]
                if len(b) == 0: continue
                rows.append(dict(date=day, side=side, bucket=f"{lo}-{hi}%",
                                 n=len(b), prem=b["mid"].sum(),
                                 pay=b["payout"].sum(),
                                 n_itm=int((b["payout"] > 0).sum())))
    except Exception as e:
        print(f"{day}: skipped ({e})")

pd.DataFrame(rows).to_csv(OUT, index=False)

# --- aggregation: seller edge, implied vs realized ITM rate per bucket ---
d = pd.read_csv(OUT)
g = d.groupby(["side", "bucket"]).agg(
    days=("date", "nunique"), n=("n", "sum"),
    prem=("prem", "sum"), pay=("pay", "sum"), n_itm=("n_itm", "sum"))
g["edge_%"]      = (g["prem"] - g["pay"]) / g["prem"] * 100
g["real_itm_%"]  = g["n_itm"] / g["n"] * 100
g["impl_itm_%"]  = (g["prem"] / g["n"]) / (g["pay"] / g["n_itm"]) * 100
g["worst_day_%"] = d.groupby(["side","bucket"]).apply(
    lambda x: x["pay"].max() / x["pay"].sum() * 100).values
print(g.round(2).to_string())
# Result: puts 24/49/87% seller edge (monotone in OTM distance), buyers pay up to 8x fair.
# Calls: one day (2025-04-09, +9.5%) = >95% of all payouts -> no conclusion possible.