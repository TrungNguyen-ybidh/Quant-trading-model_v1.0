import yfinance as yf
import pandas as pd
import ta
from ta.volatility import AverageTrueRange
import os

def download_crypto_data(symbol: str, 
                          ltf_interval: str = '15m', ltf_period: str = '60d',
                          htf_interval: str = '1h', htf_period: str = '6mo'):
    """
    Downloads cryptocurrency price data from Yahoo Finance for two different timeframes.

    Parameters:
        symbol (str): The ticker symbol of the cryptocurrency (e.g., 'BTC-USD').
        ltf_interval (str): Interval for the low time frame data (default '15m').
        ltf_period (str): Period for the low time frame data (default '60d').
        htf_interval (str): Interval for the high time frame data (default '1h').
        htf_period (str): Period for the high time frame data (default '6mo').

    Returns:
        tuple: DataFrames for low time frame (ltf) and high time frame (htf) price data.
    """
    
    print(f"\U0001F4E5 Downloading {symbol} data...")
    
    # Download low time frame (ltf) data
    ltf = yf.download(symbol, interval=ltf_interval, period=ltf_period, auto_adjust=False)
    # Download high time frame (htf) data
    htf = yf.download(symbol, interval=htf_interval, period=htf_period, auto_adjust=False)

    # Flatten MultiIndex columns if necessary
    ltf.columns = [col[0].title() if isinstance(col, tuple) else col.title() for col in ltf.columns]
    htf.columns = [col[0].title() if isinstance(col, tuple) else col.title() for col in htf.columns]

    return ltf, htf

def add_indicators(df):
    """
    Adds technical indicators to a DataFrame: EMA 50, EMA 200, ATR, RSI, and 20-period average volume.

    Parameters:
        df (pd.DataFrame): DataFrame with columns 'High', 'Low', 'Close', and 'Volume'.

    Returns:
        pd.DataFrame: Original DataFrame with new columns for indicators.
    """
    required_cols = ['High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    ema50 = ta.trend.EMAIndicator(close=df['Close'], window=50)
    ema200 = ta.trend.EMAIndicator(close=df['Close'], window=200)
    atr = ta.volatility.AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    rsi = ta.momentum.RSIIndicator(close=df['Close'], window=14)

    df['ema_50'] = ema50.ema_indicator()
    df['ema_200'] = ema200.ema_indicator()
    df['atr'] = atr.average_true_range()
    df['rsi'] = rsi.rsi()
    df['vol_avg_20'] = df['Volume'].rolling(window=20).mean()

    return df

def classify_trend_bias(ltf_df, htf_df):
    #make sure both Dataframe are datetime indexed
    ltf_df = ltf_df.copy()
    htf_df = htf_df.copy()
    ltf_df.index = pd.to_datetime(ltf_df.index)
    htf_df.index = pd.to_datetime(htf_df.index)

    #Create a trend_bias column
    trend_bias = []

    for timestamp in ltf_df.index:
        #find the most recent HTF candle <== current LTF timeframe
        htf_time = htf_df.index[htf_df.index <= timestamp].max()

        if pd.isna(htf_time):
            trend_bias.append('neutral')
            continue

        row = htf_df.loc[htf_time]
        ema_50 = row['ema_50']
        ema_200 = row['ema_200']

        if pd.isna(ema_50) or pd.isna(ema_200):
            trend_bias.append("neutral")
        elif ema_50 > ema_200:
            trend_bias.append('bullish')
        elif ema_50 < ema_200:
            trend_bias.append('bearish')
        else:
            trend_bias.append('neutral')

    ltf_df['trend_bias'] = trend_bias
    return ltf_df

def detect_breakouts(df, range_window=10, range_pct=0.01, vol_multiplier=1.2, rsi_threshold=55):
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

        if not row["is_breakout"]:
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

        # 🪵 Debug log for manual inspection
        print(f"📐 OTE Zone [{df.index[i]}]:")
        print(f"    ➤ Direction: {bias}")
        print(f"    ➤ OTE Range: {round(ote_end, 2)} → {round(ote_start, 2)} (best = {round(ote_best, 2)})")
        print(f"    ➤ Breakout Candle Close: {row['Close']}\n")

        # Store the values in the DataFrame
        df.at[df.index[i], "ote_start"] = round(ote_start, 2)
        df.at[df.index[i], "ote_best"] = round(ote_best, 2)
        df.at[df.index[i], "ote_end"] = round(ote_end, 2)
        df.at[df.index[i], "ote_dir"] = bias

    return df

def detect_entry_signals(df, max_wait=10):
    """
    After each breakout, scan up to `max_wait` candles ahead for an OTE entry trigger.
    Entry = candle enters the OTE zone + closes in the direction of the trend.
    """
    df = df.copy()
    df["is_entry"] = False
    df["entry_price"] = None
    df["entry_time"] = None
    df["entry_from_breakout_time"] = None  # ✅ Track source breakout

    for i in range(len(df)):
        if not df.iloc[i]["is_breakout"]:
            continue

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
                if candle["Low"] <= ote_end and candle["High"] >= ote_start:
                    df.at[df.index[i + j], "is_entry"] = True
                    df.at[df.index[i + j], "entry_price"] = candle["Close"]
                    df.at[df.index[i + j], "entry_time"] = df.index[i + j]
                    df.at[df.index[i + j], "entry_from_breakout_time"] = df.index[i]  # ✅ Store breakout time
                    break  # take the first valid entry

            elif direction == "bearish":
                if candle["High"] >= ote_end and candle["Low"] <= ote_start:
                    df.at[df.index[i + j], "is_entry"] = True
                    df.at[df.index[i + j], "entry_price"] = candle["Close"]
                    df.at[df.index[i + j], "entry_time"] = df.index[i + j]
                    df.at[df.index[i + j], "entry_from_breakout_time"] = df.index[i]  # ✅ Store breakout time
                    break

    return df


def set_risk_reward_loose(df, atr_col="atr", rr1_mult=1.5, rr2_mult=3.0):
    df = df.copy()
    df["stop_loss"] = None
    df["take_profit_1"] = None
    df["take_profit_2"] = None
    df["rr_1"] = None
    df["rr_2"] = None

    for i in range(1, len(df)):
        row = df.iloc[i]

        if not row.get("is_entry"):
            continue

        direction = row["ote_dir"]
        entry = row["entry_price"]
        atr = row.get(atr_col, None)
        if pd.isna(atr) or atr == 0:
            continue

        # Dynamic RR based on ATR
        if direction == "bullish":
            sl = entry - atr
            tp1 = entry + rr1_mult * atr
            tp2 = entry + rr2_mult * atr

        elif direction == "bearish":
            sl = entry + atr
            tp1 = entry - rr1_mult * atr
            tp2 = entry - rr2_mult * atr

        else:
            continue

        rr1 = abs(tp1 - entry) / abs(entry - sl)
        rr2 = abs(tp2 - entry) / abs(entry - sl)

        df.at[df.index[i], "stop_loss"] = round(sl, 2)
        df.at[df.index[i], "take_profit_1"] = round(tp1, 2)
        df.at[df.index[i], "take_profit_2"] = round(tp2, 2)
        df.at[df.index[i], "rr_1"] = round(rr1, 2)
        df.at[df.index[i], "rr_2"] = round(rr2, 2)

    return df


def run_backtest(df, max_holding=20):
    df = df.copy()
    df["trade_result"] = None
    df["exit_price"] = None
    df["exit_time"] = None
    df["holding_time"] = None
    df["reward_achieved"] = None

    for i in range(len(df)):
        if not bool(df.iloc[i].get("is_entry")):
            continue

        entry_time = df.index[i]
        entry_price = df.iloc[i]["entry_price"]
        sl = df.iloc[i]["stop_loss"]
        tp1 = df.iloc[i]["take_profit_1"]
        tp2 = df.iloc[i]["take_profit_2"]
        rr1 = df.iloc[i]["rr_1"]
        rr2 = df.iloc[i]["rr_2"]
        direction = df.iloc[i]["ote_dir"]

        outcome, exit_price, exit_time, r_mult = "timeout", None, None, 0

        for j in range(1, max_holding + 1):
            if i + j >= len(df):
                break

            future = df.iloc[i + j]
            high, low = future["High"], future["Low"]
            ts = df.index[i + j]

            if direction == "bullish":
                if low <= sl:
                    outcome, exit_price, exit_time, r_mult = "loss", sl, ts, -1
                    break
                elif high >= tp2:
                    outcome, exit_price, exit_time, r_mult = "tp2", tp2, ts, rr2
                    break
                elif high >= tp1:
                    outcome, exit_price, exit_time, r_mult = "tp1", tp1, ts, rr1
                    break

            elif direction == "bearish":
                if high >= sl:
                    outcome, exit_price, exit_time, r_mult = "loss", sl, ts, -1
                    break
                elif low <= tp2:
                    outcome, exit_price, exit_time, r_mult = "tp2", tp2, ts, rr2
                    break
                elif low <= tp1:
                    outcome, exit_price, exit_time, r_mult = "tp1", tp1, ts, rr1
                    break

        # Timeout fallback
        if outcome == "timeout":
            final_index = min(i + max_holding, len(df) - 1)
            exit_price = df.iloc[final_index]["Close"]
            exit_time = df.index[final_index]

        df.at[df.index[i], "trade_result"] = outcome
        df.at[df.index[i], "exit_price"] = round(exit_price, 2)
        df.at[df.index[i], "exit_time"] = exit_time
        df.at[df.index[i], "reward_achieved"] = r_mult

        holding_minutes = (exit_time - entry_time).total_seconds() / 60
        df.at[df.index[i], "holding_time"] = round(holding_minutes, 1)

    return df
