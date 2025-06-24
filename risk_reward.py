def set_risk_reward(df, lookback=10):
    df = df.copy()
    df["stop_loss"] = None
    df["take_profit_1"] = None
    df["take_profit_2"] = None
    df["rr_1"] = None
    df["rr_2"] = None

    for i in range(lookback, len(df)):
        row = df.iloc[i]

        if not row.get("is_entry"):
            continue

        dir = row["ote_dir"]
        entry = row["entry_price"]
        ote_best = row["ote_best"]

        lookback_window = df.iloc[i - lookback:i]

        if dir == "bullish":
            swing_low = lookback_window["Low"].min()
            impulse = entry - swing_low
            tp1 = entry + 0.27 * impulse
            tp2 = entry + 0.62 * impulse
            sl = swing_low

            rr1 = (tp1 - entry) / (entry - sl) if (entry - sl) > 0 else None
            rr2 = (tp2 - entry) / (entry - sl) if (entry - sl) > 0 else None

        elif dir == "bearish":
            swing_high = lookback_window["High"].max()
            impulse = swing_high - entry
            tp1 = entry - 0.27 * impulse
            tp2 = entry - 0.62 * impulse
            sl = swing_high

            rr1 = (entry - tp1) / (sl - entry) if (sl - entry) > 0 else None
            rr2 = (entry - tp2) / (sl - entry) if (sl - entry) > 0 else None

        else:
            continue

        df.at[df.index[i], "stop_loss"] = round(sl, 2)
        df.at[df.index[i], "take_profit_1"] = round(tp1, 2)
        df.at[df.index[i], "take_profit_2"] = round(tp2, 2)
        df.at[df.index[i], "rr_1"] = round(rr1, 2) if rr1 else None
        df.at[df.index[i], "rr_2"] = round(rr2, 2) if rr2 else None

    return df
