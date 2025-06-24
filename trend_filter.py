import pandas as pd

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