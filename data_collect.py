import yfinance as yf
import pandas as pd
import ta

# === Download data ===
print("📥 Downloading BTC-USD data...")
ltf = yf.download('BTC-USD', interval='15m', period='60d', auto_adjust=False)
htf = yf.download('BTC-USD', interval='1h', period='6mo', auto_adjust=False)


# === Flatten MultiIndex columns ===
ltf.columns = [col[0].title() for col in ltf.columns]
htf.columns = [col[0].title() for col in htf.columns]

# === Define indicator function ===
def add_indicators(df):
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

# === Apply indicators ===
ltf = add_indicators(ltf).dropna()
htf = add_indicators(htf).dropna()

# === Save to CSV ===
ltf.to_csv('BTC_LTF_15m.csv')
htf.to_csv('BTC_HTF_1h.csv')
