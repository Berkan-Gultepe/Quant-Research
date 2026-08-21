# LETF extreme-day sizing: is the conditional rebalancing flow big enough?
# Paste the fonds-list calculation here (from KW34 Fri notebook).
fonds = [
    {"aum": 7.0,  "faktor": 6},    # SPXL +3x
    {"aum": 5.7,  "faktor": 6},    # UPRO +3x
    {"aum": 7.8,  "faktor": 2},    # SSO  +2x
    {"aum": 0.42, "faktor": 6},    # SDS  -2x
    {"aum": 0.34, "faktor": 12},   # SPXS -3x
    {"aum": 0.94, "faktor": 2},    # SH   -1x
    {"aum": 0.41, "faktor": 12},   # SPXU -3x
]                                  # AUM in $bn, Aug 2026; factor = L^2 - L

masse = 0
for f in fonds:
    masse = masse + f["aum"] * f["faktor"]

print(masse)           # leverage mass: ~105 $bn
print(masse * 0.02)    # forced flow on a +/-2% day: ~$2.1bn
print(masse * 0.003)   # quiet day: ~$0.32bn
# Denominator: close-window liquidity ES (~$143bn) + SPY (~$8bn) = ~$151bn
# -> 2.1 / 151 = 1.4% << 10% pre-registered threshold. Conditional variant dead too.
# Narrow denominator (SPY only) would say 26% - the verdict lives in the denominator.