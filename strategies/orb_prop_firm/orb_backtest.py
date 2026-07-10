"""
ORB Backtest v3 — IBKR TWS Datenquelle
Voraussetzung: TWS läuft auf localhost:7497 (Paper) oder 7496 (Live)
pip install ib_insync nest_asyncio pandas numpy matplotlib pandas_datareader
"""

# Jupyter-Fix: asyncio Event Loop Konflikt
import nest_asyncio
nest_asyncio.apply()

from ib_insync import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader.data as web
from scipy import stats
import datetime, time, os, warnings
warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
TWS_HOST        = "127.0.0.1"
TWS_PORT        = 7497            # 7497 = Paper | 7496 = Live
CLIENT_ID       = 1

# ETF Proxies → Live Mapping: SPY=MES | QQQ=MNQ | IWM=M2K
TICKERS         = ["SPY", "QQQ", "IWM"]
OR_BARS         = 2               # Opening Range = erste 2 × 15min = 30 Minuten
BAR_SIZE        = "15 mins"
YEARS_BACK      = 10              # Wie viele Jahre History

RR              = 1.5
MAX_HOUR        = 14
CLOSE_HOUR      = 15
MAX_RISK_TRADE  = 250             # Max $ Risiko pro Trade pro Instrument
MAX_SHARES      = 500
PROP_LIMIT      = 2000
PROP_TARGET     = 3000
SLIPPAGE        = 0.05            # $ pro Share Entry-Slippage (realistisch für ETFs)
COMMISSION      = 1.00            # $ pro Trade Round-Trip (Lucid: $0.50/side für Micro-Futures)

# ── Style ─────────────────────────────────────────────────────────────────────
BG = "#0a0a0f"; GREEN = "#00e5a0"; RED = "#ef4444"
BLUE = "#3b82f6"; WHITE = "#ffffff"; GRAY = "#4b5563"; AMBER = "#f59e0b"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor": GRAY, "axes.labelcolor": WHITE,
    "xtick.color": GRAY, "ytick.color": GRAY, "text.color": WHITE,
    "grid.color": "#1f2937", "grid.linestyle": "--", "grid.linewidth": 0.4,
    "font.family": "monospace",
})

# ── IBKR Daten laden ──────────────────────────────────────────────────────────
def load_ibkr_data(ticker):
    """Lädt 15min Bars von IBKR TWS in 1-Jahres-Chunks."""
    data_file = f"{ticker.lower()}_15min_ibkr.csv"
    print(f"\nVerbinde für {ticker}...")
    ib = IB()
    ib.connect(TWS_HOST, TWS_PORT, clientId=CLIENT_ID)

    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)

    all_bars = []
    end_date = datetime.datetime.now()

    for i in range(YEARS_BACK):
        end_str = end_date.strftime("%Y%m%d %H:%M:%S")
        print(f"  Chunk {i+1}/{YEARS_BACK}: bis {end_str[:10]}...")
        bars = ib.reqHistoricalData(
            contract, endDateTime=end_str, durationStr="1 Y",
            barSizeSetting=BAR_SIZE, whatToShow="TRADES",
            useRTH=True, formatDate=1,
        )
        if bars:
            all_bars.append(util.df(bars))
            print(f"    → {len(bars)} Bars")
        end_date -= datetime.timedelta(days=365)
        time.sleep(12)

    ib.disconnect()

    if not all_bars:
        raise ValueError(f"Keine Daten für {ticker}")

    df = pd.concat(all_bars).drop_duplicates(subset="date").sort_values("date")
    df = df.rename(columns={"date": "Datetime", "open": "Open", "high": "High",
                             "low": "Low", "close": "Close", "volume": "Volume"})
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df = df.set_index("Datetime")[["Open", "High", "Low", "Close", "Volume"]]
    if df.index.tz is None:
        df.index = df.index.tz_localize("America/New_York")

    df.to_csv(data_file)
    print(f"Gespeichert: {data_file} ({len(df)} Bars)")
    return df


def load_data(ticker):
    data_file = f"{ticker.lower()}_15min_ibkr.csv"
    if os.path.exists(data_file):
        print(f"Cache: {data_file}")
        df = pd.read_csv(data_file, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True).tz_convert("America/New_York")
        print(f"  {len(df)} Bars | {df.index[0].date()} → {df.index[-1].date()}")
        return df
    return load_ibkr_data(ticker)


# ── Makro-Filter ──────────────────────────────────────────────────────────────
def load_macro():
    print("\nLade Makro-Daten von FRED...")
    start = datetime.datetime(2021, 1, 1)
    end   = datetime.datetime.today()
    try:
        hy = web.DataReader("BAMLH0A0HYM2", "fred", start, end)
        yc = web.DataReader("T10Y2Y",       "fred", start, end)
        macro = pd.concat([hy, yc], axis=1)
        macro.columns = ["HY_Spread", "Yield_2s10s"]
        macro = macro.ffill().dropna()
        macro["Risk_On"] = (macro["HY_Spread"] < HY_THRESHOLD) & \
                           (macro["Yield_2s10s"] > YC_THRESHOLD)
        macro.index = pd.to_datetime(macro.index).tz_localize("America/New_York")
        risk_on = set(macro[macro["Risk_On"]].index.date)
        pct = macro["Risk_On"].mean()
        print(f"Makro: Risk-On {pct:.1%} der Zeit | {len(risk_on)} Handelstage")
        return risk_on, True
    except Exception as e:
        print(f"FRED nicht erreichbar: {e} → kein Filter")
        return set(), False


# ── ORB Backtest ──────────────────────────────────────────────────────────────
def run_backtest(raw, risk_on_days, use_macro, or_bars=None, rr=None, max_hour=None):
    _or_bars  = or_bars   if or_bars   is not None else OR_BARS
    _rr       = rr        if rr        is not None else RR
    _max_hour = max_hour  if max_hour  is not None else MAX_HOUR

    trades = []
    equity = 0
    skipped_macro = skipped_range = 0

    days = raw.groupby(raw.index.date)

    for date, day_data in days:
        # Min Bars für validen Tag
        if len(day_data) < _or_bars + 2:
            continue

        # Makro-Filter
        if use_macro and date not in risk_on_days:
            skipped_macro += 1
            continue

        # Opening Range = erste _or_bars Kerzen
        or_data  = day_data.iloc[:_or_bars]
        or_high  = float(or_data["High"].max())
        or_low   = float(or_data["Low"].min())
        or_range = or_high - or_low

        # Volatility-Adjusted Sizing
        if or_range <= 0:
            continue
        shares = int(MAX_RISK_TRADE / or_range)
        shares = min(shares, MAX_SHARES)
        if shares == 0:
            skipped_range += 1
            continue

        traded = False

        for i in range(_or_bars, len(day_data)):
            bar  = day_data.iloc[i]
            hour = bar.name.hour

            if hour >= _max_hour or traded:
                break

            high  = float(bar["High"])
            low   = float(bar["Low"])

            direction = entry = stop = target = None

            if high > or_high:
                direction = "Long"
                entry  = or_high + SLIPPAGE
                stop   = or_low
                target = or_high + or_range * _rr   # Target ab OR_High (ohne Slippage)

            elif low < or_low:
                direction = "Short"
                entry  = or_low - SLIPPAGE
                stop   = or_high
                target = or_low - or_range * _rr    # Target ab OR_Low (ohne Slippage)

            if direction is None:
                continue

            # Exit suchen
            exit_price = exit_reason = None

            for j in range(i + 1, len(day_data)):
                fb = day_data.iloc[j]

                if fb.name.hour >= CLOSE_HOUR:
                    exit_price  = float(fb["Open"])
                    exit_reason = "EOD"
                    break

                if direction == "Long":
                    if float(fb["High"]) >= target:
                        exit_price = target; exit_reason = "Target"; break
                    elif float(fb["Low"]) <= stop:
                        exit_price = stop;   exit_reason = "Stop";   break
                else:
                    if float(fb["Low"]) <= target:
                        exit_price = target; exit_reason = "Target"; break
                    elif float(fb["High"]) >= stop:
                        exit_price = stop;   exit_reason = "Stop";   break
            else:
                exit_price  = float(day_data.iloc[-1]["Close"])
                exit_reason = "EOD"

            if exit_price is None:
                continue

            pnl = (exit_price - entry if direction == "Long" else entry - exit_price) * shares
            pnl -= COMMISSION     # Round-Trip Commission
            equity += pnl
            traded  = True

            trades.append({
                "Date": str(date), "Direction": direction,
                "OR_Range": round(or_range, 3), "Shares": shares,
                "Risk_$": round(or_range * shares, 0),
                "Entry": round(entry, 2), "Stop": round(stop, 2),
                "Target": round(target, 2), "Exit": round(exit_price, 2),
                "ExitReason": exit_reason, "PnL": round(pnl, 2),
                "Equity": round(equity, 2),
            })
            break

    return pd.DataFrame(trades), skipped_macro, skipped_range


# ── Statistiken & Output ──────────────────────────────────────────────────────
def print_stats(df, skipped_macro, skipped_range, use_macro):
    print(f"\n{'='*60}")
    print(f"  ORB v3 IBKR — OR: {OR_BARS*15}min | Makro: {'AN' if use_macro else 'AUS'} | R:R {RR}")
    print(f"{'='*60}")

    if df.empty:
        print("  Keine Trades."); return

    total   = len(df)
    winners = (df["PnL"] > 0).sum()
    losers  = (df["PnL"] <= 0).sum()
    wr      = winners / total
    avg_win = df[df["PnL"] > 0]["PnL"].mean()
    avg_loss= df[df["PnL"] <= 0]["PnL"].mean()
    pf      = abs(df[df["PnL"]>0]["PnL"].sum() / df[df["PnL"]<0]["PnL"].sum()) if losers>0 else np.inf
    max_dd  = (df["Equity"].cummax() - df["Equity"]).max()

    print(f"  Trades:            {total}")
    print(f"  Win Rate:          {wr:.1%}")
    print(f"  Avg Win:           ${avg_win:.0f}")
    print(f"  Avg Loss:          ${avg_loss:.0f}")
    print(f"  Profit Factor:     {pf:.2f}")
    print(f"  Total P&L:         ${df['PnL'].sum():.0f}")
    print(f"  Max Drawdown:      ${max_dd:.0f}")
    print(f"  Avg Risk/Trade:    ${df['Risk_$'].mean():.0f}")
    print(f"  Übersprungen Makro: {skipped_macro}")
    print(f"  Übersprungen Range: {skipped_range}")
    print(f"\n  Exit-Gründe:")
    print(df["ExitReason"].value_counts().to_string())

    # Prop Firm Simulation
    print(f"\n{'='*60}")
    print(f"  PROP FIRM SIM (50K | Max Loss $2,000 EOD | Target $3,000)")
    print(f"{'='*60}")

    account = 50000; peak = 50000; floor = peak - PROP_LIMIT
    passed = busted = False; day_pnls = []

    for _, t in df.iterrows():
        account += t["PnL"]; day_pnls.append(t["PnL"])
        if account > peak:
            peak = account; floor = peak - PROP_LIMIT
        if account <= floor:
            print(f"  ❌ BUST  — ${account:.0f} (Floor: ${floor:.0f}) nach {len(day_pnls)} Trades")
            busted = True; break
        if account >= 50000 + PROP_TARGET:
            print(f"  ✅ PASSED — ${account:.0f} nach {len(day_pnls)} Trades")
            passed = True; break

    if not busted and not passed:
        print(f"  ⏳ Offen — ${account:.0f}")

    if day_pnls and (pos := sum(p for p in day_pnls if p > 0)) > 0:
        c = max(day_pnls) / pos
        print(f"  Consistency:       {c:.1%} {'✅' if c < 0.5 else '⚠️  VIOLATION'}")

    # ── Statistische Signifikanz ──────────────────────────────────────────────
    pnl_arr = df["PnL"].values
    t_stat, p_value = stats.ttest_1samp(pnl_arr, popmean=0)
    se = pnl_arr.std() / np.sqrt(len(pnl_arr))
    print(f"\n{'='*60}")
    print(f"  STATISTISCHE SIGNIFIKANZ")
    print(f"{'='*60}")
    print(f"  EV/Trade:    ${pnl_arr.mean():.2f}")
    print(f"  Std Dev:     ${pnl_arr.std():.2f}")
    print(f"  Std Error:   ${se:.2f}")
    print(f"  t-Statistik: {t_stat:.2f}")
    print(f"  p-Wert:      {p_value:.6f}")
    sig = "✅ Hochsignifikant (p < 0.001)" if p_value < 0.001 else \
          "✅ Signifikant (p < 0.05)"      if p_value < 0.05  else \
          "⚠️  Nicht signifikant"
    print(f"  Ergebnis:    {sig}")

    return wr, pf, max_dd


# ── Monte Carlo Simulation ────────────────────────────────────────────────────
def monte_carlo(df, n_sims=1000, max_trades=500):
    pnls = df["PnL"].values
    passed = busted = open_ = 0
    trades_to_pass = []

    for _ in range(n_sims):
        sequence = np.random.choice(pnls, size=max_trades, replace=True)
        account  = 50000
        peak     = 50000
        floor    = peak - PROP_LIMIT
        result   = "open"

        for i, pnl in enumerate(sequence):
            account += pnl
            if account > peak:
                peak  = account
                floor = peak - PROP_LIMIT
            if account <= floor:
                result = "bust"; break
            if account >= 50000 + PROP_TARGET:
                result = "pass"
                trades_to_pass.append(i + 1)
                break

        if result == "pass":   passed += 1
        elif result == "bust": busted += 1
        else:                  open_  += 1

    pass_rate = passed / n_sims
    bust_rate = busted / n_sims
    ev = pass_rate * PROP_TARGET - bust_rate * 98

    print(f"\n{'='*60}")
    print(f"  MONTE CARLO ({n_sims:,} Simulationen | max {max_trades} Trades)")
    print(f"{'='*60}")
    print(f"  ✅ Pass Rate:        {pass_rate:.1%}  ({passed}/{n_sims})")
    print(f"  ❌ Bust Rate:        {bust_rate:.1%}  ({busted}/{n_sims})")
    print(f"  ⏳ Offen:            {open_/n_sims:.1%}  ({open_}/{n_sims})")
    print(f"\n  EV pro Attempt:     ${ev:.0f}")
    print(f"  EV × 10 Accounts:   ${ev*10:.0f}")
    if trades_to_pass:
        print(f"  Ø Trades bis Pass:  {np.mean(trades_to_pass):.0f}")
        print(f"  Median bis Pass:    {np.median(trades_to_pass):.0f}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Monte Carlo — Pass {pass_rate:.1%} | Bust {bust_rate:.1%} | EV ${ev:.0f}/Attempt", color=WHITE, fontsize=12)

    # Equity Pfade (100 Samples)
    ax1 = axes[0]
    for _ in range(100):
        seq = np.random.choice(pnls, size=max_trades, replace=True)
        eq_path = [0]
        account = 50000; peak = 50000; floor = peak - PROP_LIMIT
        for p in seq:
            account += p
            if account > peak: peak = account; floor = peak - PROP_LIMIT
            eq_path.append(account - 50000)
            if account <= floor or account >= 50000 + PROP_TARGET: break
        ax1.plot(eq_path, alpha=0.15, linewidth=0.6, color=GREEN)
    ax1.axhline(PROP_TARGET,  color=GREEN, linewidth=1.5, linestyle="--", label=f"Target +${PROP_TARGET}")
    ax1.axhline(-PROP_LIMIT,  color=RED,   linewidth=1.5, linestyle="--", label=f"Bust -${PROP_LIMIT}")
    ax1.axhline(0, color=GRAY, linewidth=0.5)
    ax1.set_title("100 zufällige Equity-Pfade", color=WHITE, fontsize=11)
    ax1.set_ylabel("P&L ($)", color=WHITE); ax1.grid(True)
    ax1.legend(facecolor="#13131f", edgecolor=GRAY, labelcolor=WHITE, fontsize=9)
    for sp in ax1.spines.values(): sp.set_edgecolor(GRAY)

    # Trades bis Pass Verteilung
    ax2 = axes[1]
    if trades_to_pass:
        ax2.hist(trades_to_pass, bins=30, color=GREEN, alpha=0.7, edgecolor=GRAY)
        ax2.axvline(np.mean(trades_to_pass), color=AMBER, linewidth=1.5, linestyle="--", label=f"Ø {np.mean(trades_to_pass):.0f}")
        ax2.set_title("Trades bis Pass (Verteilung)", color=WHITE, fontsize=11)
        ax2.set_xlabel("Anzahl Trades", color=WHITE)
        ax2.set_ylabel("Häufigkeit", color=WHITE); ax2.grid(True)
        ax2.legend(facecolor="#13131f", edgecolor=GRAY, labelcolor=WHITE, fontsize=9)
    for sp in ax2.spines.values(): sp.set_edgecolor(GRAY)

    plt.tight_layout()
    plt.savefig("orb_monte_carlo.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.show(); plt.close()
    print(f"\n→ Chart: orb_monte_carlo.png")


def plot_results(df, use_macro, wr, pf):
    fig, axes = plt.subplots(4, 1, figsize=(14, 16))
    title = f"ORB v3 IBKR — {OR_BARS*15}min OR | Makro {'AN' if use_macro else 'AUS'} | R:R {RR} | WR {wr:.1%} | PF {pf:.2f}"
    fig.suptitle(title, color=WHITE, fontsize=12, y=0.99)

    eq = df["Equity"].values; pnl = df["PnL"].values

    ax1 = axes[0]
    ax1.plot(range(len(eq)), eq, color=GREEN, linewidth=1.2)
    ax1.axhline(0, color=GRAY, linewidth=0.5, linestyle=":")
    ax1.fill_between(range(len(eq)), eq, 0, where=(eq>0), alpha=0.1, color=GREEN)
    ax1.fill_between(range(len(eq)), eq, 0, where=(eq<0), alpha=0.1, color=RED)
    ax1.set_title("Equity Curve", color=WHITE, fontsize=11)
    ax1.set_ylabel("P&L ($)", color=WHITE); ax1.grid(True)
    for sp in ax1.spines.values(): sp.set_edgecolor(GRAY)

    ax2 = axes[1]
    colors = [GREEN if p > 0 else RED for p in pnl]
    ax2.bar(range(len(pnl)), pnl, color=colors, alpha=0.7, width=0.8)
    ax2.axhline(0, color=GRAY, linewidth=0.5)
    ax2.set_title(f"Trade P&L | Wins: {(pnl>0).sum()} | Losses: {(pnl<=0).sum()}", color=WHITE, fontsize=11)
    ax2.set_ylabel("P&L ($)", color=WHITE); ax2.grid(True)
    for sp in ax2.spines.values(): sp.set_edgecolor(GRAY)

    ax3 = axes[2]
    shares_vals = df["Shares"].values
    ax3.bar(range(len(shares_vals)), shares_vals, color=BLUE, alpha=0.7, width=0.8)
    ax3.axhline(df["Shares"].mean(), color=AMBER, linewidth=1.0, linestyle="--",
                label=f"Ø {df['Shares'].mean():.0f}")
    ax3.set_title("Position Size pro Trade (Shares)", color=WHITE, fontsize=11)
    ax3.set_ylabel("Shares", color=WHITE); ax3.grid(True)
    ax3.legend(facecolor="#13131f", edgecolor=GRAY, labelcolor=WHITE, fontsize=9)
    for sp in ax3.spines.values(): sp.set_edgecolor(GRAY)

    ax4 = axes[3]
    rwr = pd.Series((pnl > 0).astype(int)).rolling(20).mean()
    ax4.plot(range(len(rwr)), rwr, color=AMBER, linewidth=1.0)
    ax4.axhline(0.5, color=GRAY, linewidth=0.8, linestyle="--", label="50%")
    ax4.set_title("Rolling Win Rate (20 Trades)", color=WHITE, fontsize=11)
    ax4.set_ylabel("Win Rate", color=WHITE); ax4.set_ylim(0, 1); ax4.grid(True)
    ax4.legend(facecolor="#13131f", edgecolor=GRAY, labelcolor=WHITE, fontsize=9)
    for sp in ax4.spines.values(): sp.set_edgecolor(GRAY)

    plt.tight_layout()
    fname = f"orb_v3_{OR_BARS*15}min_makro{'an' if use_macro else 'aus'}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.show(); plt.close()
    print(f"\n→ Chart: {fname}")


# ── Parameter Sensitivität (Grid Search) ─────────────────────────────────────
def param_sensitivity(all_raw):
    """Testet RR × OR_BARS Kombinationen — zeigt PF Heatmap."""
    rr_range   = [1.0, 1.2, 1.5, 2.0, 2.5]
    orb_range  = [1, 2, 3, 4]           # × 15min = 15, 30, 45, 60min

    results = {}
    total = len(rr_range) * len(orb_range)
    n = 0
    for orb in orb_range:
        for rr_val in rr_range:
            n += 1
            print(f"  [{n}/{total}] OR={orb*15}min | RR={rr_val}", end=" ... ")
            combo_trades = []
            for ticker, raw in all_raw.items():
                df_t, _, _ = run_backtest(raw, set(), False, or_bars=orb, rr=rr_val)
                if not df_t.empty:
                    combo_trades.append(df_t)
            if combo_trades:
                df_c = pd.concat(combo_trades)
                w = df_c[df_c["PnL"] > 0]["PnL"].sum()
                l = abs(df_c[df_c["PnL"] < 0]["PnL"].sum())
                pf = w / l if l > 0 else 0
                results[(orb, rr_val)] = round(pf, 3)
                print(f"PF={pf:.3f}")
            else:
                results[(orb, rr_val)] = 0
                print("keine Trades")

    # Heatmap
    pf_matrix = np.array([[results[(orb, rr_val)] for rr_val in rr_range] for orb in orb_range])

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    im = ax.imshow(pf_matrix, cmap="RdYlGn", aspect="auto", vmin=0.9, vmax=1.4)
    ax.set_xticks(range(len(rr_range))); ax.set_xticklabels([f"RR {r}" for r in rr_range], color=WHITE)
    ax.set_yticks(range(len(orb_range))); ax.set_yticklabels([f"OR {o*15}min" for o in orb_range], color=WHITE)
    ax.set_title("Parameter Sensitivität — Profit Factor", color=WHITE, fontsize=12)
    for i in range(len(orb_range)):
        for j in range(len(rr_range)):
            ax.text(j, i, f"{pf_matrix[i,j]:.3f}", ha="center", va="center",
                    color="black" if 0.95 < pf_matrix[i,j] < 1.35 else WHITE, fontsize=10, fontweight="bold")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig("orb_param_sensitivity.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.show(); plt.close()
    print(f"\n→ Chart: orb_param_sensitivity.png")
    return results


# ── IS/OOS Split ──────────────────────────────────────────────────────────────
IS_END  = "2022-01-01"   # In-Sample:     2016 – 2021
OOS_START = "2022-01-01" # Out-of-Sample: 2022 – 2026

def pf_str(df):
    w = df[df["PnL"] > 0]["PnL"].sum()
    l = abs(df[df["PnL"] < 0]["PnL"].sum())
    return f"{w/l:.2f}" if l > 0 else "∞"

def pf_val(df):
    w = df[df["PnL"] > 0]["PnL"].sum()
    l = abs(df[df["PnL"] < 0]["PnL"].sum())
    return round(w / l, 3) if l > 0 else 0

def quick_stats(df, label):
    if df.empty:
        print(f"  {label}: Keine Trades"); return
    wr = (df["PnL"] > 0).mean()
    pf = pf_str(df)
    ev = df["PnL"].mean()
    print(f"  {label:30s} | Trades: {len(df):4d} | WR: {wr:.1%} | PF: {pf} | EV/Trade: ${ev:.1f}")


# ── Walk-Forward Analyse ──────────────────────────────────────────────────────
def walk_forward(all_raw, train_years=2, test_years=1):
    """Rollendes IS/OOS Fenster über alle verfügbaren Daten."""
    # Datenrange bestimmen
    all_dates = []
    for raw in all_raw.values():
        all_dates.extend(raw.index.date.tolist())
    start_year = min(d.year for d in all_dates)
    end_year   = max(d.year for d in all_dates)

    windows = []
    for is_start in range(start_year, end_year - train_years - test_years + 2):
        is_end   = is_start + train_years
        oos_end  = is_end + test_years
        if oos_end > end_year + 1:
            break
        windows.append((
            f"{is_start}-01-01", f"{is_end}-01-01",
            f"{is_end}-01-01",   f"{oos_end}-01-01",
        ))

    print(f"\n{'='*60}")
    print(f"  WALK-FORWARD ANALYSE  ({train_years}J IS | {test_years}J OOS | {len(windows)} Fenster)")
    print(f"{'='*60}")
    print(f"  {'Fenster':<22} {'IS PF':>7} {'OOS PF':>8} {'Decay':>8} {'OOS Trades':>12} {'OOS PF>1?':>10}")
    print(f"  {'-'*70}")

    wf_results = []
    oos_equity_chunks = []

    for is_s, is_e, oos_s, oos_e in windows:
        combo_is  = []
        combo_oos = []
        for ticker, raw in all_raw.items():
            df_t, _, _ = run_backtest(raw, set(), False)
            if df_t.empty: continue
            df_is_w  = df_t[(df_t["Date"] >= is_s)  & (df_t["Date"] < is_e)]
            df_oos_w = df_t[(df_t["Date"] >= oos_s) & (df_t["Date"] < oos_e)]
            if not df_is_w.empty:  combo_is.append(df_is_w)
            if not df_oos_w.empty: combo_oos.append(df_oos_w)

        if not combo_is or not combo_oos:
            continue

        df_is_w  = pd.concat(combo_is)
        df_oos_w = pd.concat(combo_oos)

        pf_is  = pf_val(df_is_w)
        pf_oos = pf_val(df_oos_w)
        decay  = (pf_is - pf_oos) / (pf_is - 1) * 100 if pf_is > 1 else 100
        ok     = "✅" if pf_oos > 1.0 else "❌"

        label = f"{is_s[:4]}–{is_e[:4]} → {oos_s[:4]}–{oos_e[:4]}"
        print(f"  {label:<22} {pf_is:>7.3f} {pf_oos:>8.3f} {decay:>7.0f}% {len(df_oos_w):>12} {ok:>10}")

        wf_results.append({
            "Fenster": label, "IS_PF": pf_is, "OOS_PF": pf_oos,
            "Decay": decay, "OOS_Trades": len(df_oos_w), "OOS_OK": pf_oos > 1.0
        })
        df_oos_w = df_oos_w.copy()
        df_oos_w["Equity"] = df_oos_w["PnL"].cumsum()
        oos_equity_chunks.append(df_oos_w["PnL"].values)

    if not wf_results:
        print("  Keine Fenster."); return

    ok_count = sum(r["OOS_OK"] for r in wf_results)
    avg_oos_pf = np.mean([r["OOS_PF"] for r in wf_results])
    print(f"\n  Fenster OOS PF > 1.0:  {ok_count}/{len(wf_results)}  {'✅ Robust' if ok_count/len(wf_results) >= 0.7 else '⚠️  Instabil'}")
    print(f"  Ø OOS PF über alle Fenster: {avg_oos_pf:.3f}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"Walk-Forward — {train_years}J IS | {test_years}J OOS | {ok_count}/{len(wf_results)} Fenster profitabel", color=WHITE, fontsize=12)

    # IS vs OOS PF Balken
    ax1 = axes[0]
    labels = [r["Fenster"].split(" → ")[1] for r in wf_results]
    is_pfs  = [r["IS_PF"]  for r in wf_results]
    oos_pfs = [r["OOS_PF"] for r in wf_results]
    x = np.arange(len(labels))
    w = 0.35
    ax1.bar(x - w/2, is_pfs,  w, label="IS PF",  color=BLUE,  alpha=0.8)
    ax1.bar(x + w/2, oos_pfs, w, label="OOS PF", color=GREEN, alpha=0.8)
    ax1.axhline(1.0, color=RED, linewidth=1, linestyle="--", label="PF=1.0")
    ax1.set_xticks(x); ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax1.set_title("IS vs OOS Profit Factor pro Fenster", color=WHITE, fontsize=11)
    ax1.set_ylabel("Profit Factor", color=WHITE); ax1.grid(True)
    ax1.legend(facecolor="#13131f", edgecolor=GRAY, labelcolor=WHITE, fontsize=9)
    for sp in ax1.spines.values(): sp.set_edgecolor(GRAY)

    # Gestiched OOS Equity Curve
    ax2 = axes[1]
    full_oos_pnl = np.concatenate(oos_equity_chunks) if oos_equity_chunks else np.array([])
    if len(full_oos_pnl) > 0:
        eq = np.cumsum(full_oos_pnl)
        ax2.plot(range(len(eq)), eq, color=GREEN, linewidth=1.2)
        ax2.fill_between(range(len(eq)), eq, 0, where=(eq>0), alpha=0.1, color=GREEN)
        ax2.fill_between(range(len(eq)), eq, 0, where=(eq<0), alpha=0.1, color=RED)
        ax2.axhline(0, color=GRAY, linewidth=0.5, linestyle=":")
    ax2.set_title("Gestiched OOS Equity Curve (alle Fenster)", color=WHITE, fontsize=11)
    ax2.set_ylabel("Kum. P&L ($)", color=WHITE); ax2.grid(True)
    for sp in ax2.spines.values(): sp.set_edgecolor(GRAY)

    plt.tight_layout()
    plt.savefig("orb_walk_forward.png", dpi=150, bbox_inches="tight", facecolor=BG)
    plt.show(); plt.close()
    print(f"\n→ Chart: orb_walk_forward.png")
    return wf_results


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Daten laden
    all_raw = {}
    all_trades = []
    for ticker in TICKERS:
        raw = load_data(ticker)
        all_raw[ticker] = raw
        df_t, _, _ = run_backtest(raw, set(), False)
        if not df_t.empty:
            df_t["Ticker"] = ticker
            all_trades.append(df_t)

    # 2. Portfolio kombinieren
    df = pd.concat(all_trades).sort_values("Date").reset_index(drop=True)
    df["Equity"] = df["PnL"].cumsum()

    # 3. IS / OOS Split
    df_is  = df[df["Date"] <  IS_END].copy().reset_index(drop=True)
    df_oos = df[df["Date"] >= OOS_START].copy().reset_index(drop=True)
    df_is["Equity"]  = df_is["PnL"].cumsum()
    df_oos["Equity"] = df_oos["PnL"].cumsum()

    print(f"\n{'='*60}")
    print(f"  IS/OOS VALIDIERUNG")
    print(f"{'='*60}")
    quick_stats(df_is,  f"IN-SAMPLE  (2016–2021)")
    quick_stats(df_oos, f"OUT-OF-SAMPLE (2022–2026)")
    quick_stats(df,     f"GESAMT     (2016–2026)")

    # 4. Robustheit-Check
    pf_is  = float(pf_str(df_is))  if not df_is.empty  else 0
    pf_oos = float(pf_str(df_oos)) if not df_oos.empty else 0
    decay  = (pf_is - pf_oos) / (pf_is - 1) * 100 if pf_is > 1 else 100
    print(f"\n  PF Decay IS→OOS: {decay:.0f}%  ", end="")
    print("✅ Robust" if decay < 30 else "⚠️  Mögliches Overfitting" if decay < 60 else "❌ Overfit")

    print(f"\n{'='*60}")
    print(f"  PORTFOLIO GESAMT: {len(TICKERS)} Instrumente | {len(df)} Trades")
    print(f"{'='*60}")

    # 5. Stats & Plot (Gesamt)
    result = print_stats(df, 0, 0, False)
    if result and not df.empty:
        wr, pf, max_dd = result
        plot_results(df, False, wr, pf)

    # 6. Monte Carlo (auf OOS Daten — realistischer)
    if not df_oos.empty:
        print("\n→ Monte Carlo auf OOS Daten (2022–2026):")
        monte_carlo(df_oos, n_sims=1000, max_trades=500)

    # 7. Parameter Sensitivität
    print(f"\n{'='*60}")
    print(f"  PARAMETER SENSITIVITÄT (RR × OR_BARS)")
    print(f"{'='*60}")
    param_sensitivity(all_raw)

    # 8. RR Vergleich: Monte Carlo 1.5 vs 2.5 (auf OOS)
    print(f"\n{'='*60}")
    print(f"  RR VERGLEICH — Monte Carlo (OOS 2022–2026)")
    print(f"{'='*60}")
    rr_compare = [1.5, 2.5]
    mc_results = {}
    for rr_val in rr_compare:
        oos_trades = []
        for ticker, raw in all_raw.items():
            df_t, _, _ = run_backtest(raw, set(), False, rr=rr_val)
            if not df_t.empty:
                df_t["Ticker"] = ticker
                oos_trades.append(df_t)
        if not oos_trades:
            continue
        df_rr = pd.concat(oos_trades).sort_values("Date").reset_index(drop=True)
        df_rr_oos = df_rr[df_rr["Date"] >= OOS_START].copy()
        df_rr_oos["Equity"] = df_rr_oos["PnL"].cumsum()

        pnls = df_rr_oos["PnL"].values
        n_sims = 1000; max_trades = 500
        passed = busted = open_ = 0
        trades_to_pass = []

        for _ in range(n_sims):
            sequence = np.random.choice(pnls, size=max_trades, replace=True)
            account = 50000; peak = 50000; floor = peak - PROP_LIMIT
            result = "open"
            for i, pnl in enumerate(sequence):
                account += pnl
                if account > peak: peak = account; floor = peak - PROP_LIMIT
                if account <= floor: result = "bust"; break
                if account >= 50000 + PROP_TARGET:
                    result = "pass"; trades_to_pass.append(i + 1); break
            if result == "pass": passed += 1
            elif result == "bust": busted += 1
            else: open_ += 1

        pass_rate = passed / n_sims
        bust_rate = busted / n_sims
        ev = pass_rate * PROP_TARGET - bust_rate * 98
        wr = (df_rr_oos["PnL"] > 0).mean()
        mc_results[rr_val] = {
            "wr": wr, "pass": pass_rate, "bust": bust_rate,
            "ev": ev, "median": int(np.median(trades_to_pass)) if trades_to_pass else 999
        }
        print(f"\n  RR={rr_val} | WR: {wr:.1%} | Pass: {pass_rate:.1%} | Bust: {bust_rate:.1%} | EV: ${ev:.0f} | Median Trades: {mc_results[rr_val]['median']}")

    # Vergleichs-Tabelle
    print(f"\n  {'RR':<8} {'Win Rate':<12} {'Pass Rate':<12} {'Bust Rate':<12} {'EV':<10} {'Median Trades'}")
    print(f"  {'-'*65}")
    for rr_val, r in mc_results.items():
        print(f"  {rr_val:<8} {r['wr']:<12.1%} {r['pass']:<12.1%} {r['bust']:<12.1%} ${r['ev']:<9.0f} {r['median']}")

    # 9. Walk-Forward Analyse
    walk_forward(all_raw, train_years=2, test_years=1)
