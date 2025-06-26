from b_backtest import (
    download_crypto_data, add_indicators, classify_trend_bias,
    detect_breakouts, calculate_ote_zones, detect_entry_signals,
    set_risk_reward_loose, run_backtest
)
import pandas as pd
import os

def main():
    symbol = "BTC-USD"
    print("🔁 Starting backtest for", symbol)

    # Step 1: Get data
    ltf_df, htf_df = download_crypto_data(symbol, ltf_period="60d", htf_period="1y")
    print(f"✅ Downloaded {len(ltf_df)} LTF and {len(htf_df)} HTF rows")

    # Step 2: Indicators
    ltf_df = add_indicators(ltf_df)
    htf_df = add_indicators(htf_df)

    # Step 3: Bias classification
    ltf_df = classify_trend_bias(ltf_df, htf_df)

    # Step 4: Breakout + OTE + Entry
    ltf_df = detect_breakouts(ltf_df)
    ltf_df = calculate_ote_zones(ltf_df)
    ltf_df = detect_entry_signals(ltf_df)

    ltf_df["ote_dir"] = ltf_df["ote_dir"].fillna(method="ffill", limit=10)

    # Step 5: Risk-Reward + Backtest
    ltf_df = set_risk_reward_loose(ltf_df)
    result_df = run_backtest(ltf_df)

    # ✅ Step 6: Clean up invalid entries (fix order here)
    for i in result_df[result_df["is_entry"]].index:
        breakout_time = result_df.loc[i, "entry_from_breakout_time"]
        if pd.isna(breakout_time) or not result_df.loc[breakout_time, "is_breakout"]:
            result_df.at[i, "is_entry"] = False
            result_df.at[i, "entry_price"] = None
            result_df.at[i, "entry_time"] = None

    # ✅ Step 7: Save filtered results
    filtered_df = result_df[(result_df["is_breakout"] == True) | (result_df["is_entry"] == True)]
    print("✅ Results saved to backtest_B_results.csv (breakouts and entries only)")

     # Step 8: Summary
    entries = result_df[result_df["is_entry"] == True]
    wins = entries[entries["trade_result"].isin(["tp1", "tp2"])]
    losses = entries[entries["trade_result"] == "loss"]

    summary_data = {
        "symbol": symbol,
        "test_type": 'B',
        "total_breakouts": int(result_df["is_breakout"].sum()),
        "entries": int(len(entries)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "win_rate": round(len(wins) / len(entries) * 100, 2) if len(entries) else 0,
        "avg_holding_time": round(entries["holding_time"].mean(), 1) if len(entries) else 0,
        "net_r": round(entries["reward_achieved"].sum(), 2) if len(entries) else 0
    }

    summary_df = pd.DataFrame([summary_data])

    file_path = "backtest_result_1y.csv"
    if os.path.exists(file_path):
        summary_df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        summary_df.to_csv(file_path, index=False)

    print("✅ Summary appended to backtest_result_1y.csv")

if __name__ == "__main__":
    main()
