import pandas as pd

def detect_entry_signals(df, max_wait=10):
    """
    After each breakout, scan up to `max_wait` candles ahead for an OTE entry trigger.
    Entry = candle enters the OTE zone + closes in the direction of the trend.
    """
    df = df.copy()
    df["is_entry"] = False
    df["entry_price"] = None
    df["entry_time"] = None

    for i in range(len(df)):
        if pd.isna(df.iloc[i]["ote_dir"]):
            continue

        direction = df.iloc[i]["ote_dir"]
        ote_start = df.iloc[i]["ote_start"]
        ote_end = df.iloc[i]["ote_end"]

        for j in range(1, max_wait + 1):
            if i + j >= len(df):
                break
            candle = df.iloc[i + j]

            if direction == "bullish":
                if candle["Low"] <= ote_end and candle["Close"] >= ote_start:
                    df.at[df.index[i + j], "is_entry"] = True
                    df.at[df.index[i + j], "entry_price"] = candle["Close"]
                    df.at[df.index[i + j], "entry_time"] = df.index[i + j]
                    break  # only take the first valid entry

            elif direction == "bearish":
                if candle["High"] >= ote_end and candle["Close"] <= ote_start:
                    df.at[df.index[i + j], "is_entry"] = True
                    df.at[df.index[i + j], "entry_price"] = candle["Close"]
                    df.at[df.index[i + j], "entry_time"] = df.index[i + j]
                    break

    return df
