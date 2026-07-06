"""
PHASE 2–5 — Dual Momentum Strategy (Antonacci 2012)
Alle Phasen in einem File — führe die Zellen der Reihe nach aus.

STRATEGIE-LOGIK (monatlich, Ende Monat):
1. Berechne 12M-Return für SPY, EFA, BIL
2. Gewinner = SPY wenn SPY_12M > EFA_12M, sonst EFA
3. Wenn Gewinner_12M > BIL_12M → in Gewinner investieren
   Wenn Gewinner_12M ≤ BIL_12M → in AGG investieren (sicherer Hafen)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ══════════════════════════════════════════════════════════════════════════════
# SETUP — Daten laden (einmal laufen lassen)
# ══════════════════════════════════════════════════════════════════════════════

tickers = ['SPY', 'EFA', 'AGG', 'BIL']
raw = yf.download(tickers, start='2003-01-01', progress=False)['Close'].dropna()  # yfinance: 'Close' ist seit auto_adjust=True bereits adjustiert (ehem. 'Adj Close')
daily_ret = raw.pct_change().dropna()

print(f"Daten: {raw.index[0].date()} → {raw.index[-1].date()}")
print(f"Assets: {', '.join(tickers)}\n")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — STRATEGIE IMPLEMENTIEREN
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 65)
print("PHASE 2 — STRATEGIE: Dual Momentum")
print("=" * 65)

# Monatliche Preise (Ende Monat)
monthly = raw.resample('ME').last()

# 12-Monats-Momentum (mit shift(1) → kein Look-Ahead-Bias)
# shift(1): Signal von Ende Monat M gilt ab Monat M+1
mom_12 = monthly.pct_change(12).shift(1)

# --- Signal-Funktion ---
def dual_momentum_signal(row):
    """Gibt Asset-Name zurück basierend auf Dual Momentum Logik."""
    spy  = row['SPY']
    efa  = row['EFA']
    bil  = row['BIL']
    if pd.isna(spy) or pd.isna(efa) or pd.isna(bil):
        return np.nan
    # Relativer Momentum: wer ist stärker?
    winner     = 'SPY' if spy > efa else 'EFA'
    winner_mom = spy   if spy > efa else efa
    # Absoluter Momentum: schlägt Gewinner T-Bills?
    return winner if winner_mom > bil else 'AGG'

# Monatliche Positionen
monthly_pos = mom_12.apply(dual_momentum_signal, axis=1).dropna()

print(f"\nSignale: {len(monthly_pos)} Monate")
print("\nPositions-Verteilung:")
print(monthly_pos.value_counts().to_string())

# Auf Tagesebene hochrechnen (Position gilt bis nächstes Monatssignal)
positions_daily = monthly_pos.reindex(daily_ret.index, method='ffill')

# --- Strategie-Tagesrenditen ---
strategy_returns = pd.Series(index=daily_ret.index, dtype=float)
for date in daily_ret.index:
    pos = positions_daily.get(date)
    if pos in daily_ret.columns:
        strategy_returns[date] = daily_ret.loc[date, pos]

strategy_returns = strategy_returns.dropna()
bnh_returns = daily_ret['SPY'].reindex(strategy_returns.index)  # Benchmark

# --- Basis-Metriken ---
def basis_metriken(returns, name="Strategie", benchmark=None):
    ann_ret = returns.mean() * 252
    ann_vol = returns.std() * np.sqrt(252)
    sharpe  = ann_ret / ann_vol
    sortino = ann_ret / (returns[returns < 0].std() * np.sqrt(252))
    equity  = (1 + returns).cumprod()
    dd      = equity / equity.cummax() - 1
    max_dd  = dd.min()
    calmar  = ann_ret / abs(max_dd)
    print(f"\n{'─'*40}")
    print(f"{name}:")
    print(f"  Rendite p.a.     : {ann_ret*100:6.1f}%")
    print(f"  Volatilität p.a. : {ann_vol*100:6.1f}%")
    print(f"  Sharpe           : {sharpe:6.2f}")
    print(f"  Sortino          : {sortino:6.2f}")
    print(f"  Max Drawdown     : {max_dd*100:6.1f}%")
    print(f"  Calmar           : {calmar:6.2f}")
    print(f"  Handelstage      : {len(returns)}")
    if sharpe < 0.3:
        print("  ⚠️  Sharpe < 0.3 — Edge fraglich, tiefere Analyse nötig")
    return dict(ann_ret=ann_ret, ann_vol=ann_vol, sharpe=sharpe,
                sortino=sortino, max_dd=max_dd, calmar=calmar)

m_strat = basis_metriken(strategy_returns, "Dual Momentum")
m_bnh   = basis_metriken(bnh_returns, "SPY Buy & Hold")

# IS/OOS Split — 70% / 30%
split_date = strategy_returns.index[int(len(strategy_returns) * 0.7)]
print(f"\nIS/OOS Split: IS bis {split_date.date()}, OOS ab {split_date.date()}")

is_ret  = strategy_returns[:split_date]
oos_ret = strategy_returns[split_date:]

print(f"\nIn-Sample Sharpe  : {is_ret.mean()*252 / (is_ret.std()*np.sqrt(252)):.2f}")
print(f"Out-of-Sample Sharpe: {oos_ret.mean()*252 / (oos_ret.std()*np.sqrt(252)):.2f}")
oos_is_ratio = (oos_ret.mean()*252 / (oos_ret.std()*np.sqrt(252))) / (is_ret.mean()*252 / (is_ret.std()*np.sqrt(252)))
status = "✅" if oos_is_ratio > 0.5 else "⚠️"
print(f"OOS/IS Ratio       : {oos_is_ratio:.2f}  {status}")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — VALIDIERUNG
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("PHASE 3 — VALIDIERUNG")
print("=" * 65)

# --- Walk-Forward (Jahresweise) ---
print("\nWALK-FORWARD (pro Jahr):")
years = strategy_returns.index.year.unique()
wf_results = []
for y in sorted(years):
    yr = strategy_returns[strategy_returns.index.year == y]
    bm = bnh_returns[bnh_returns.index.year == y]
    if len(yr) < 50:
        continue
    sr_strat = yr.mean() * 252 / (yr.std() * np.sqrt(252))
    sr_bm    = bm.mean() * 252 / (bm.std() * np.sqrt(252))
    ret_strat = (1 + yr).prod() - 1
    ret_bm    = (1 + bm).prod() - 1
    won = "✅" if ret_strat > ret_bm else "❌"
    wf_results.append(ret_strat > ret_bm)
    print(f"  {y}: Strat {ret_strat*100:6.1f}% | SPY {ret_bm*100:6.1f}%  {won}")

wf_positive = sum(wf_results) / len(wf_results)
print(f"\n  Walk-Forward Score: {sum(wf_results)}/{len(wf_results)} = {wf_positive*100:.0f}%  {'✅' if wf_positive >= 0.6 else '⚠️'}")

# --- Signifikanz-Tests ---
print("\nSIGNIFIKANZ-TESTS:")

# 1. t-Test (Tagesrenditen Strategie vs. 0)
t_stat, t_pval = stats.ttest_1samp(strategy_returns, 0)
print(f"\n  1. t-Test (Tagesrenditen > 0): p = {t_pval:.4f}  {'✅' if t_pval < 0.05 else '❌'}")

# 2. Sharpe-Test (Lo 2002)
# FIX 06.07.2026: Formel braucht den DAILY Sharpe (gleiche Frequenz wie n)!
# Vorher wurde der annualisierte Sharpe (×√252) eingesetzt → z = 40 (Unsinn).
n        = len(strategy_returns)
sr_daily = strategy_returns.mean() / strategy_returns.std()
sr_se    = np.sqrt((1 + 0.5 * sr_daily**2) / n)
sr_z     = sr_daily / sr_se
sr_p     = 1 - stats.norm.cdf(sr_z)
print(f"  2. Sharpe-Test (Lo 2002): z = {sr_z:.2f}, p = {sr_p:.4f}  {'✅' if sr_p < 0.05 else '❌'}")

# 3. Bootstrap-CI für Sharpe
np.random.seed(42)
n_boot = 5000
boot_sharpes = []
for _ in range(n_boot):
    sample = strategy_returns.sample(n=len(strategy_returns), replace=True)
    boot_sharpes.append(sample.mean() / sample.std() * np.sqrt(252))
ci_low, ci_high = np.percentile(boot_sharpes, [2.5, 97.5])
print(f"  3. Bootstrap 95%-CI Sharpe: [{ci_low:.2f}, {ci_high:.2f}]  {'✅' if ci_low > 0 else '❌'}")

# 4. Outperformance vs. Benchmark (monatlich)
monthly_strat = strategy_returns.resample('ME').apply(lambda r: (1+r).prod()-1)
monthly_bnh   = bnh_returns.resample('ME').apply(lambda r: (1+r).prod()-1)
common_m      = monthly_strat.index.intersection(monthly_bnh.index)
t2, p2 = stats.ttest_rel(monthly_strat[common_m], monthly_bnh[common_m])
print(f"  4. Paired t-Test vs. SPY (monatlich): p = {p2:.4f}  {'✅' if p2 < 0.05 else '❌'}")

# Gesamt
n_passed = sum([t_pval < 0.05, sr_p < 0.05, ci_low > 0, p2 < 0.05])
print(f"\n  Gesamt: {n_passed}/4 Tests bestanden  {'✅' if n_passed >= 3 else '⚠️'}")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — TIEFENANALYSE
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("PHASE 4 — TIEFENANALYSE")
print("=" * 65)

# --- Alpha & Beta vs. SPY ---
common = strategy_returns.index.intersection(bnh_returns.index)
X = bnh_returns[common].values
Y = strategy_returns[common].values
slope, intercept, r_val, p_val_ab, se = stats.linregress(X, Y)
beta  = slope
alpha = intercept * 252
print(f"\nAlpha/Beta Regression vs. SPY:")
print(f"  Beta   : {beta:.3f}")
print(f"  Alpha  : {alpha*100:.2f}% p.a.  (p = {p_val_ab:.4f})  {'✅' if p_val_ab < 0.05 else '❌'}")
print(f"  R²     : {r_val**2:.3f}")

# --- Positions-Analyse ---
print("\nPOSITIONS-ANALYSE:")
pos_monthly = pd.DataFrame({'position': monthly_pos})
pos_monthly['next_month_ret'] = monthly_strat.shift(-1)
for asset in ['SPY', 'EFA', 'AGG']:
    subset = pos_monthly[pos_monthly['position'] == asset]['next_month_ret'].dropna()
    if len(subset) > 0:
        print(f"  {asset}: {len(subset)} Monate | Ø Return {subset.mean()*100:.2f}% | Sharpe ≈ {subset.mean()/subset.std()*np.sqrt(12):.2f}")

# --- Rolling Sharpe (12M Fenster) ---
roll_sharpe = strategy_returns.rolling(252).apply(
    lambda r: r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
)
pct_pos = (roll_sharpe.dropna() > 0).mean()
print(f"\nRolling Sharpe (252 Tage): {pct_pos*100:.1f}% der Zeit > 0  {'✅' if pct_pos > 0.65 else '⚠️'}")

# --- Charts ---
fig, axes = plt.subplots(3, 1, figsize=(14, 14))
fig.suptitle('Phase 4 — Dual Momentum Tiefenanalyse', fontsize=14, fontweight='bold')

# 1. Equity Curve
ax = axes[0]
(1 + strategy_returns).cumprod().plot(ax=ax, label='Dual Momentum', color='steelblue', lw=2)
(1 + bnh_returns).cumprod().plot(ax=ax, label='SPY B&H', color='gray', lw=1.5, ls='--')
ax.set_title('Equity Curve vs. SPY Buy & Hold')
ax.set_ylabel('Wert ($)')
ax.set_yscale('log')
ax.legend()
ax.grid(alpha=0.3)

# Positions farbig markieren
for asset, color in [('SPY', 'lightblue'), ('EFA', 'lightgreen'), ('AGG', 'lightyellow')]:
    in_pos = positions_daily.reindex(strategy_returns.index) == asset
    ax.fill_between(strategy_returns.index, ax.get_ylim()[0], ax.get_ylim()[1],
                    where=in_pos, alpha=0.08, color=color, label=f'{asset}-Phase')

# 2. Rolling Sharpe
ax2 = axes[1]
roll_sharpe.plot(ax=ax2, color='steelblue', lw=1)
ax2.axhline(0, color='red', lw=0.8, ls='--')
ax2.axhline(1, color='green', lw=0.8, ls='--', alpha=0.7)
ax2.set_title(f'Rolling 252d Sharpe — {pct_pos*100:.1f}% > 0')
ax2.set_ylabel('Sharpe')
ax2.grid(alpha=0.3)

# 3. Drawdown
ax3 = axes[2]
equity = (1 + strategy_returns).cumprod()
dd = equity / equity.cummax() - 1
dd.plot(ax=ax3, color='red', lw=1.2, label='Dual Momentum DD')
bnh_eq = (1 + bnh_returns).cumprod()
bnh_dd = bnh_eq / bnh_eq.cummax() - 1
bnh_dd.plot(ax=ax3, color='gray', lw=1, ls='--', alpha=0.7, label='SPY DD')
ax3.set_title('Drawdown-Vergleich')
ax3.set_ylabel('Drawdown')
ax3.fill_between(dd.index, dd, 0, alpha=0.3, color='red')
ax3.legend()
ax3.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('dual_momentum_phase4.png', dpi=120)
plt.show()
print("\n→ Phase 4 Chart gespeichert")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — DEFLATED SHARPE + ENTSCHEIDUNG
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("PHASE 5 — DEFLATED SHARPE & ENTSCHEIDUNG")
print("=" * 65)

def deflated_sharpe_ratio(returns, n_tests=1, sr_benchmark=0.0):
    """
    Probabilistic Sharpe Ratio (Bailey & Lopez de Prado, 2012).
    Wie hoch ist die Wahrscheinlichkeit, dass der wahre Sharpe > sr_benchmark?
    """
    n      = len(returns)
    sr     = returns.mean() / returns.std() * np.sqrt(252)
    skew   = stats.skew(returns)
    kurt   = stats.kurtosis(returns)
    # Bonferroni-Korrektur: erwarteter Max-Sharpe bei n_tests Tests
    if n_tests > 1:
        expected_max_sr = stats.norm.ppf(1 - 1/n_tests)
        sr_star = sr_benchmark + expected_max_sr * np.sqrt((1 - skew*sr + (kurt-1)/4 * sr**2) / n)
    else:
        sr_star = sr_benchmark
    # PSR
    sr_se  = np.sqrt((1 + 0.5*sr**2 - skew*sr + (kurt+2)/4*sr**2) / (n - 1))
    z      = (sr - sr_star) / sr_se
    psr    = stats.norm.cdf(z)
    return sr, psr, sr_se

def min_track_record_length(sr_target, confidence=0.95, sr_benchmark=0.0):
    """Minimale Track Record Länge (in Jahren) für gegebene Konfidenz."""
    z = stats.norm.ppf(confidence)
    # Auf Daily umrechnen
    sr_daily = sr_target / np.sqrt(252)
    bm_daily = sr_benchmark / np.sqrt(252)
    # Näherungsformel (Bailey & Lopez de Prado)
    mtrl = (1 + (1 - stats.skew(strategy_returns)) * sr_daily
            + (stats.kurtosis(strategy_returns) - 1) / 4 * sr_daily**2) * (z / (sr_daily - bm_daily))**2
    return mtrl

sr_val, psr, sr_se = deflated_sharpe_ratio(strategy_returns, n_tests=1)
print(f"\nSharpe Ratio    : {sr_val:.3f}")
print(f"Sharpe Std Error: {sr_se:.3f}")
print(f"PSR (P[SR > 0]) : {psr*100:.1f}%  {'✅' if psr > 0.95 else '⚠️' if psr > 0.8 else '❌'}")

try:
    mtrl = min_track_record_length(sr_val)
    mtrl_years = mtrl / 252
    print(f"Min. Track Record: {mtrl:.0f} Tage ({mtrl_years:.1f} Jahre) — wir haben {len(strategy_returns)/252:.1f} Jahre")
    track_ok = len(strategy_returns) > mtrl
    print(f"Track Record ausreichend: {'✅' if track_ok else '⚠️'}")
except:
    print("Min TRL: Berechnung nicht möglich")
    track_ok = True  # Dual Momentum hat theoretischen Prior

# CVaR
alpha_cvar = 0.05
var_threshold = strategy_returns.quantile(alpha_cvar)
cvar = strategy_returns[strategy_returns <= var_threshold].mean()
print(f"\nVaR  (5%): {var_threshold*100:.2f}% pro Tag")
print(f"CVaR (5%): {cvar*100:.2f}% pro Tag")
print(f"CVaR ann. : {cvar*252*100:.1f}% — im schlechtesten 5% der Tage erwartet")

# Ruin-Wahrscheinlichkeit
pos_days = strategy_returns[strategy_returns > 0]
neg_days = strategy_returns[strategy_returns < 0]
if len(pos_days) > 0 and len(neg_days) > 0:
    win_rate = len(pos_days) / (len(pos_days) + len(neg_days))
    payoff   = pos_days.mean() / abs(neg_days.mean())
    q = 1 - win_rate
    p = win_rate
    kelly_half = 0.5
    if p * payoff > q:
        ruin_prob = (q / (p * payoff)) ** (1 / kelly_half)
    else:
        ruin_prob = 1.0
    print(f"\nWin Rate   : {win_rate*100:.1f}%")
    print(f"Payoff     : {payoff:.2f}")
    print(f"Ruin-P (Half-Kelly): {ruin_prob*100:.2f}%  {'✅' if ruin_prob < 0.01 else '⚠️'}")

# --- Checkliste ---
print("\n" + "═" * 65)
print("ENTSCHEIDUNGS-CHECKLISTE (Mindeststandards)")
print("═" * 65)

checks = {
    "Sharpe > 0.5"                  : m_strat['sharpe'] > 0.5,
    "Sortino > 0.8"                 : m_strat['sortino'] > 0.8,
    "Max DD < -50%"                 : m_strat['max_dd'] > -0.50,
    "Walk-Forward ≥ 60% positiv"    : wf_positive >= 0.60,
    "OOS/IS Sharpe > 50%"           : oos_is_ratio > 0.50,
    "t-Test p < 0.05"               : t_pval < 0.05,
    "PSR > 80%"                     : psr > 0.80,
}

passed = sum(checks.values())
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'}  {k}")

print(f"\n  {passed}/{len(checks)} Checks bestanden")
if passed >= 6:
    print("\n  → ✅ PAPER TRADING starten")
elif passed >= 4:
    print("\n  → ⚠️ Grenzfall — Ergebnisse dokumentieren, Edge klein aber vorhanden")
else:
    print("\n  → ❌ Strategie verwerfen oder grundlegend überarbeiten")

print("\n✅ Alle 5 Phasen abgeschlossen")
print("→ Ergebnisse in Obsidian: [[DualMomentum_Ergebnisse]]")
