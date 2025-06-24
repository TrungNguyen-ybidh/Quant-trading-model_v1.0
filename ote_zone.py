def calculate_ote_zones(df, lookback=10):
    """
    For each breakout candle, calculate the OTE (Optimal Trade Entry) zone
    using a custom Fibonacci retracement: 0.62 to 0.79 (best at 0.705).
    """
    df = df.copy()
    df["ote_start"] = None
    df["ote_best"] = None
    df["ote_end"] = None
    df["ote_dir"] = None

    for i in range(lookback, len(df)):
        row = df.iloc[i]

        if row["is_breakout"] is not True:
            continue

        bias = row["trend_bias"]
        if bias not in ["bullish", "bearish"]:
            continue

        # Identify swing high/low N bars before breakout
        lookback_window = df.iloc[i - lookback:i]

        if bias == "bullish":
            swing_low = lookback_window["Low"].min()
            breakout_high = row["High"]

            impulse_range = breakout_high - swing_low
            ote_start = breakout_high - 0.62 * impulse_range
            ote_best = breakout_high - 0.705 * impulse_range
            ote_end = breakout_high - 0.79 * impulse_range

        elif bias == "bearish":
            swing_high = lookback_window["High"].max()
            breakout_low = row["Low"]

            impulse_range = swing_high - breakout_low
            ote_start = breakout_low + 0.62 * impulse_range
            ote_best = breakout_low + 0.705 * impulse_range
            ote_end = breakout_low + 0.79 * impulse_range

        else:
            continue  # Just in case

        # Store the values in the DataFrame
        df.at[df.index[i], "ote_start"] = round(ote_start, 2)
        df.at[df.index[i], "ote_best"] = round(ote_best, 2)
        df.at[df.index[i], "ote_end"] = round(ote_end, 2)
        df.at[df.index[i], "ote_dir"] = bias

    return df
