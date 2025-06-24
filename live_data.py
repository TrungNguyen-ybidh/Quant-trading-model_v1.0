from alpaca_trade_api.rest import REST
import pandas as pd

API_KEY = 'PK4R0JPBNKCUVX1UC2PZ'
API_SECRET = 'NJqH2UPYxUQ1Yxq8qkQO7xCOtvRU2NE5Ib8p0XsS'
BASE_URL = 'https://paper-api.alpaca.markets'

api = REST(API_KEY, API_SECRET, BASE_URL)

def get_live_data(symbol="BTC/USD", timeframe="15Min", limit=100):
    bars = api.get_crypto_bars(symbol, timeframe, limit=limit).df

    # ✅ Safe filter only if 'exchange' column exists
    if 'exchange' in bars.columns:
        bars = bars[bars['exchange'] == 'CBSE']

    # ✅ Filter for the requested symbol
    bars = bars[bars['symbol'] == symbol]

    # ✅ Format
    df = bars.reset_index().rename(columns={"timestamp": "Datetime"})
    df = df[['Datetime', 'open', 'high', 'low', 'close', 'volume']]
    df.columns = [col.title() for col in df.columns]
    df.set_index('Datetime', inplace=True)

    return df
