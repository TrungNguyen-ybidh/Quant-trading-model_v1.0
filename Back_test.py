def run_strategy(symbol, timeframe_ltf="15Min", timeframe_htf="1Hour"):
    from ta.trend import EMAIndicator
    from live_data import get_live_data
    from trend_filter import classify_trend_bias
    from breakout_detector import detect_breakouts
    from ote_zone import calculate_ote_zones
    from entry_trigger import detect_entry_signals
    from risk_reward import set_risk_reward

    import os
    import pandas as pd
    import time

    log_path = f"{symbol.replace('/', '_')}_log.csv"

    def log_trade_to_csv(trade_dict):
        df = pd.DataFrame([trade_dict])
        if not os.path.isfile(log_path):
            df.to_csv(log_path, index=False)
        else:
            df.to_csv(log_path, mode='a', index=False, header=False)

    while True:
        try:
            ltf = get_live_data(symbol, timeframe_ltf)
            htf = get_live_data(symbol, timeframe_htf)

            htf.columns = [str(col).title() for col in htf.columns]
            htf['ema_50'] = EMAIndicator(close=htf['Close'], window=50).ema_indicator()
            htf['ema_200'] = EMAIndicator(close=htf['Close'], window=200).ema_indicator()

            ltf = classify_trend_bias(ltf, htf)
            trend = ltf['trend_bias'].iloc[-1]

            breakout_leg = detect_breakouts(ltf)
            if breakout_leg['is_breakout'].any():
                ote = calculate_ote_zones(breakout_leg)
                if detect_entry_signals(ltf, ote):
                    rr_df = set_risk_reward(ltf, breakout_leg, ote)
                    latest_trade = rr_df.iloc[-1].to_dict()
                    log_trade_to_csv(latest_trade)
                    print(f"✅ [{symbol}] Trade logged:", latest_trade)

            time.sleep(900)

        except Exception as e:
            print(f"⚠️ [{symbol}] Error:", e)
            time.sleep(60)


import threading

symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]

for symbol in symbols:
    t = threading.Thread(target=run_strategy, args=(symbol,))
    t.start()
