import requests
import time
import datetime
import numpy as np

SYMBOLS = ["BTCUSDT", "ETHUSDT","LTCUSDT","BCHUSDT","XRPUSDT","SOLUSDT","BNBUSDT","TRXUSDT","HBARUSDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
MA_PERIOD = 20

def get_candles(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    return response.json()

def get_trend_and_ma20(candles):
    closes = [float(c[4]) for c in candles if len(c) > 4]
    if len(closes) < MA_PERIOD:
        return None, None, None
    closes_array = np.array(closes)
    ma20 = np.mean(closes_array[-MA_PERIOD:])
    ma_trend = 'rising' if ma20 > np.mean(closes_array[-MA_PERIOD*2:-MA_PERIOD]) else 'falling'
    trend = 'up' if closes_array[-1] > closes_array[-2] else 'down'
    return trend, ma20, ma_trend

def is_close_to_ma(current_price, ma):
    return abs(current_price - ma) / ma < 0.01  # within 1%

def detect_retrace(candles):
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    peak = max(highs)
    bottom = min(lows)
    last_close = float(candles[-1][4])
    drop = (peak - last_close) / (peak - bottom + 1e-9)
    return 0.4 <= drop <= 0.6

def detect_contrary_bars(candles, trend):
    colors = []
    for c in candles[-3:]:
        open_price = float(c[1])
        close_price = float(c[4])
        colors.append('green' if close_price > open_price else 'red')
    if trend == 'up':
        return all(c == 'red' for c in colors)
    else:
        return all(c == 'green' for c in colors)

def is_doji(candle):
    open_price = float(candle[1])
    close_price = float(candle[4])
    return abs(open_price - close_price) < 0.1 * (float(candle[2]) - float(candle[3]))

def is_narrow_range(candles):
    ranges = [float(c[2]) - float(c[3]) for c in candles[-5:]]
    return ranges[-1] < np.mean(ranges[:-1])

def has_high_volume(candle, volume_list):
    vol = float(candle[5])
    avg_vol = np.mean([float(v) for v in volume_list[-20:]])
    return vol > avg_vol * 1.5

def low_spread(candle):
    return (float(candle[2]) - float(candle[3])) / float(candle[4]) < 0.0015

def get_support_resistance(candles):
    closes = np.array([float(c[4]) for c in candles])
    sr_levels = {
        "support": round(np.min(closes[-30:]), 2),
        "resistance": round(np.max(closes[-30:]), 2)
    }
    return sr_levels

def analyze_symbol(symbol):
    trends = []
    same_trend = None
    ma20_info = []
    close_to_ma20 = []
    retrace = False
    contrarian_bars = []
    extra_signals = []
    support_resist = []

    for tf in TIMEFRAMES:
        candles = get_candles(symbol, tf)
        if not candles or len(candles) < MA_PERIOD:
            continue

        trend, ma20, ma_trend = get_trend_and_ma20(candles)
        if trend is None:
            continue
        trends.append(trend)

        if tf in ["5m", "15m", "30m", "1h"]:
            current_price = float(candles[-1][4])
            if is_close_to_ma(current_price, ma20):
                close_to_ma20.append(tf)

        if tf == "1h":
            retrace = detect_retrace(candles)

        if detect_contrary_bars(candles, trend):
            contrarian_bars.append(tf)

        if tf in ["5m", "15m", "30m"]:
            if is_doji(candles[-1]):
                extra_signals.append(f"Doji on {tf}")
            if is_narrow_range(candles):
                extra_signals.append(f"Narrow bar on {tf}")
            if has_high_volume(candles[-1], [c[5] for c in candles]):
                extra_signals.append(f"High volume on {tf}")

        if tf == "5m" and low_spread(candles[-1]):
            extra_signals.append("Low spread on 5m")

        if tf in ["4h", "1d"]:
            sr = get_support_resistance(candles)
            support_resist.append((tf, sr))

    if len(set(trends)) == 1:
        direction = trends[0]
        emojis = {'up': '📈', 'down': '📉'}
        msg = f"{emojis[direction]} {symbol} trending {direction.upper()} in all timeframes"

        if close_to_ma20:
            msg += f" | Near MA20 on: {', '.join(close_to_ma20)} 🟡"

        if retrace:
            msg += " | 🔁 40–60% Retrace"

        if contrarian_bars:
            msg += f" | 🔻 Contrary candles on: {', '.join(contrarian_bars)}"

        if extra_signals:
            msg += " | " + " | ".join(extra_signals)

        for tf, sr in support_resist:
            msg += f" | {tf.upper()} S/R: S={sr['support']} R={sr['resistance']}"

        print(msg)
    else:
        print(f"⏳ {symbol} no clear trend in all timeframes")

if __name__ == "__main__":
    while True:
        print(f"--- {datetime.datetime.now(datetime.UTC).isoformat()} ---")
        for symbol in SYMBOLS:
            try:
                analyze_symbol(symbol)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
        time.sleep(60)

