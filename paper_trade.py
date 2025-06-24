import time
from live_data import get_live_data
from trend_filter import classify_trend_bias
from breakout_detector import detect_breakouts
from ote_zone import calculate_ote_zones
from entry_trigger import detect_entry_signals
from risk_reward import set_risk_reward
from ta.trend import EMAIndicator

position = None
trade_log = []


''''''
while True:
    # 1. Fetch live data
    ltf = get_live_data("BTC/USD", "15Min")
    htf = get_live_data("BTC/USD", "1Hour")

# Make sure HTF has capitalized column names
    htf.columns = [str(col).title() for col in htf.columns]

# Add EMA indicators
    htf['ema_50'] = EMAIndicator(close=htf['Close'], window=50).ema_indicator()
    htf['ema_200'] = EMAIndicator(close=htf['Close'], window=200).ema_indicator()

    # 2. Determine trend
    ltf = classify_trend_bias(ltf, htf)
    trend = ltf['trend_bias'].iloc[-1]  # ✅ This gives you the most recent bias


    # 3. Detect breakout
    breakout_leg = detect_breakouts(ltf)

    if breakout_leg['is_breakout'].any():
        # 4. Calculate OTE zones
        ote = calculate_ote_zones(breakout_leg)

        # 5. Look for entry trigger inside OTE zone
        if detect_entry_signals(ltf, ote):
            # 6. Set SL/TP
            rr = set_risk_reward(ltf, breakout_leg, ote)

            # 7. Simulate paper trade
            trade_log.append(rr)
            print("✅ Simulated trade:", rr)
            position = "open"

    # 8. Sleep until next candle
    time.sleep(900)  # 15 min
