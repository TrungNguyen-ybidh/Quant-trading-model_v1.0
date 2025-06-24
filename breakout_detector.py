def detect_breakouts(df, range_window=10, range_pct=0.005, vol_multiplier=1.5, rsi_threshold=60):
    df = df.copy()
    df['is_breakout'] = False

    for i in range(range_window, len(df)):
        window = df.iloc[i - range_window:i]
        candle= df.iloc[i]

        if candle['trend_bias'] not in ['bullish', 'bearish']:
            continue

        max_high = window['High'].max()
        min_low = window['Low'].min()
        range_size = max_high - min_low
        mid_price = (max_high + min_low) / 2
        if range_size / mid_price > range_pct:
            continue

        body = abs(candle["Close"] - candle['Open'])
        median_body = window['Close'].sub(window["Open"]).abs().median()
        if body < 1.5 * median_body:
            continue

        # Directional breakout (based on trend)
        if candle["trend_bias"] == "bullish" and candle["Close"] <= max_high:
            continue
        if candle["trend_bias"] == "bearish" and candle["Close"] >= min_low:
            continue

        # Volume & momentum
        if candle["Volume"] < vol_multiplier * candle["vol_avg_20"]:
            continue
        if candle["trend_bias"] == "bullish" and candle["rsi"] < rsi_threshold:
            continue
        if candle["trend_bias"] == "bearish" and candle["rsi"] > (100 - rsi_threshold):
            continue

        df.at[df.index[i], "is_breakout"] = True

    return df
