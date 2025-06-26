import pandas as pd
import os
from a_backtest import (
    download_crypto_data as download_A,
    add_indicators as add_A,
    classify_trend_bias as bias_A,
    detect_breakouts as breakout_A,
    calculate_ote_zones as ote_A,
    detect_entry_signals as entry_A,
    set_risk_reward as rr_A,
    run_backtest as run_A
)
from b_backtest import (
    download_crypto_data as download_B,
    add_indicators as add_B,
    classify_trend_bias as bias_B,
    detect_breakouts as breakout_B,
    calculate_ote_zones as ote_B,
    detect_entry_signals as entry_B,
    set_risk_reward_loose as rr_B,
    run_backtest as run_B
)

def run_test(symbol, ltf_period, htf_period, test_type):
    if test_type == 'A':
        download, add_ind, bias, breakout, ote, entry, rr, run_bt = (
            download_A, add_A, bias_A, breakout_A, ote_A, entry_A, rr_A, run_A)
    else:
        download, add_ind, bias, breakout, ote, entry, rr, run_bt = (
            download_B, add_B, bias_B, breakout_B, ote_B, entry_B, rr_B, run_B)

    print(f"\n🔁 Running Test {test_type} | Symbol: {symbol} | LTF: {ltf_period} | HTF: {htf_period}")
    
    try:
        ltf_df, htf_df = download(symbol, ltf_period=ltf_period, htf_period=htf_period)
    except Exception as e:
        print(f"❌ Failed to download data for {symbol}: {e}")
        return

    if ltf_df.empty or htf_df.empty:
        print("⚠️ Empty DataFrame. Skipping...")
        return

    try:
        ltf_df = add_ind(ltf_df)
        htf_df = add_ind(htf_df)
        ltf_df = bias(ltf_df, htf_df)
        ltf_df = breakout(ltf_df)
        ltf_df = ote(ltf_df)
        ltf_df = entry(ltf_df)
        ltf_df["ote_dir"] = ltf_df["ote_dir"].fillna(method="ffill", limit=10)
        ltf_df = rr(ltf_df)
        result_df = run_bt(ltf_df)

        for i in result_df[result_df["is_entry"]].index:
            breakout_time = result_df.loc[i, "entry_from_breakout_time"]
            if pd.isna(breakout_time) or not result_df.loc[breakout_time, "is_breakout"]:
                result_df.at[i, "is_entry"] = False
                result_df.at[i, "entry_price"] = None
                result_df.at[i, "entry_time"] = None

        entries = result_df[result_df["is_entry"] == True]
        wins = entries[entries["trade_result"].isin(["tp1", "tp2"])]
        losses = entries[entries["trade_result"] == "loss"]

        summary_data = {
            "symbol": symbol,
            "test_type": test_type,
            "ltf_period": ltf_period,
            "htf_period": htf_period,
            "total_breakouts": int(result_df["is_breakout"].sum()),
            "entries": int(len(entries)),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "win_rate": round(len(wins) / len(entries) * 100, 2) if len(entries) else 0,
            "avg_holding_time": round(entries["holding_time"].mean(), 1) if len(entries) else 0,
            "net_r": round(entries["reward_achieved"].sum(), 2) if len(entries) else 0
        }

        summary_df = pd.DataFrame([summary_data])
        file_path = "backtest_result_combined.csv"
        if os.path.exists(file_path):
            summary_df.to_csv(file_path, mode='a', header=False, index=False)
        else:
            summary_df.to_csv(file_path, index=False)

        print(f"✅ Summary saved for {symbol} | Test {test_type}")
    
    except Exception as e:
        print(f"❌ Failed to process {symbol} | Test {test_type}: {e}")


def main():
    symbols = [
    "AAPL",     # Apple
    "MSFT",     # Microsoft
    "GOOGL",    # Alphabet (Google)
    "AMZN",     # Amazon
    "META",     # Meta (Facebook)
    "TSLA",     # Tesla
    "NVDA",     # Nvidia
    "BRK-B",    # Berkshire Hathaway
    "JPM",      # JPMorgan Chase
    "UNH",      # UnitedHealth
    "V",        # Visa
    "JNJ",      # Johnson & Johnson
    "WMT",      # Walmart
    "PG",       # Procter & Gamble
    "MA",       # Mastercard
    "XOM",      # ExxonMobil
    "HD",       # Home Depot
    "PFE",      # Pfizer
    "DIS",      # Disney
    "BAC",      # Bank of America
    "KO",       # Coca-Cola
    "INTC",     # Intel
    "NFLX",     # Netflix
    "CRM",      # Salesforce
    "CSCO",     # Cisco Systems
    "PEP",      # PepsiCo
    "T",        # AT&T
    "BA",       # Boeing
    "CVX",      # Chevron
    "NKE",      # Nike
    "ORCL",     # Oracle
    "COST",     # Costco
    "QCOM",     # Qualcomm
    "MDT",      # Medtronic
    "GE",       # General Electric
    "IBM",      # IBM
    "MCD",      # McDonald's
    "ABT",      # Abbott Labs
    "DHR",      # Danaher
    "CMCSA",    # Comcast
]


    ltf_periods = ["60d","30d", "60d"]
    htf_periods = ["6mo", "6m0", "1y"]

    for symbol in symbols:
        for ltf, htf in zip(ltf_periods, htf_periods):
            run_test(symbol, ltf, htf, test_type='A')
            run_test(symbol, ltf, htf, test_type='B')


if __name__ == "__main__":
    main()
