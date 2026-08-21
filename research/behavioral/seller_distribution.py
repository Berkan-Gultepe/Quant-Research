# Seller P&L distribution for 2-5% OTM 0DTE puts: win rate, median, skew, worst day
# Paste the distribution cell here (from KW34 Wed notebook).
import pandas as pd

d = pd.read_csv(r"C:\Users\Berkan\Documents\Quant_data\data\features\lottery\lottery_daily.csv")
k = d[(d["side"] == "PUT") & (d["bucket"] == "2.0-5.0%")].copy()

k["r"] = (k["prem"] - k["pay"]) / k["prem"]   # daily result per premium dollar

print("days:      ", len(k))
print("win rate:  ", (k["r"] > 0).mean().round(4))
print("median:    ", k["r"].median().round(4))
print("mean:      ", k["r"].mean().round(4))
print("worst day: ", k["r"].min().round(2), "on", k.loc[k["r"].idxmin(), "date"])
print("skew:      ", k["r"].skew().round(2))
# Result: win rate 99.81%, median 1.0, mean 0.858, skew -32.67,
# worst day -147.88 per premium dollar on 2024-12-18 (Fed decision day).
# Win rate says how often you win - the worst day decides if you survive.