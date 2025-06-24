def run_backtest(df, max_holding=20):
    df = df.copy()
    df["trade_result"] = None
    df["exit_price"] = None
    df["exit_time"] = None

    for i in range(len(df)):
        if df.iloc[i].get("is_entry") is not True:
            continue

        entry_price = df.iloc[i]["entry_price"]
        sl = df.iloc[i]["stop_loss"]
        tp = df.iloc[i]["take_profit_1"]
        direction = df.iloc[i]["ote_dir"]

        outcome = None
        exit_price = None
        exit_time = None

        # Look ahead for max_holding candles
        for j in range(1, max_holding + 1):
            if i + j >= len(df):
                break

            future = df.iloc[i + j]
            high = future["High"]
            low = future["Low"]
            ts = df.index[i + j]

            if direction == "bullish":
                if low <= sl:
                    outcome = "loss"
                    exit_price = sl
                    exit_time = ts
                    break
                elif high >= tp:
                    outcome = "win"
                    exit_price = tp
                    exit_time = ts
                    break

            elif direction == "bearish":
                if high >= sl:
                    outcome = "loss"
                    exit_price = sl
                    exit_time = ts
                    break
                elif low <= tp:
                    outcome = "win"
                    exit_price = tp
                    exit_time = ts
                    break

        if outcome:
            df.at[df.index[i], "trade_result"] = outcome
            df.at[df.index[i], "exit_price"] = exit_price
            df.at[df.index[i], "exit_time"] = exit_time
        else:
            df.at[df.index[i], "trade_result"] = "timeout"
            df.at[df.index[i], "exit_price"] = df.iloc[i + max_holding]["Close"]
            df.at[df.index[i], "exit_time"] = df.index[i + max_holding]

    return df
