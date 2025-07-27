import requests
import numpy as np
import time
from statistics import mean

BINANCE_API_URL = "https://api.binance.com"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT", "XRPUSDT", "BNBUSDT","HBARUSDT","ADAUSDT"]
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
NOTIFY_URL = "https://ntfy.sh/tendencial"

def get_candles(symbol, interval, limit=50):
    url = f"{BINANCE_API_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

def get_trend_and_ma20(candles):
    closes = np.array([float(c[4]) for c in candles if len(c) > 4])
    if len(closes) < 21:
        return None, None, None
    ma20 = mean(closes[-20:])
    current_price = closes[-1]
    trend = "UP" if current_price > ma20 else "DOWN"
    ma_trend = "CLOSE" if abs(current_price - ma20) / ma20 < 0.005 else "FAR"
    return trend, ma20, ma_trend

def is_retrace(candles, trend):
    last_3 = candles[-3:]
    if trend == "UP":
        return all(float(c[4]) < float(c[1]) for c in last_3)
    elif trend == "DOWN":
        return all(float(c[4]) > float(c[1]) for c in last_3)
    return False

def has_three_candles_opposite_color(candles, trend):
    last_3 = candles[-3:]
    if trend == "UP":
        # 3 or more red candles (close < open)
        return all(float(c[4]) < float(c[1]) for c in last_3)
    elif trend == "DOWN":
        # 3 or more green candles (close > open)
        return all(float(c[4]) > float(c[1]) for c in last_3)
    return False

def is_doji(c):
    open_p, close_p = float(c[1]), float(c[4])
    return abs(open_p - close_p) / float(c[2]) < 0.01

def is_narrow_range(c):
    high, low = float(c[2]), float(c[3])
    return (high - low) / float(c[4]) < 0.01

def has_high_volume(c, candles):
    volumes = [float(x[5]) for x in candles[:-1]]
    avg_volume = mean(volumes) if volumes else 0
    return float(c[5]) > avg_volume * 1.5 if avg_volume > 0 else False

def has_low_spread(c):
    high, low = float(c[2]), float(c[3])
    return (high - low) / float(c[4]) < 0.01

def get_support_resistance(candles):
    closes = [float(c[4]) for c in candles]
    support = min(closes)
    resistance = max(closes)
    return support, resistance

def notify(symbol, messages):
    trend_val = list(messages["trend"].values())[0]
    trend_text = "⬆️ Uptrend" if trend_val == "UP" else "⬇️ Downtrend"

    # MA20 cerca (spread) timeframes
    ma_near_tfs = []
    # Retroceso 40-60% detected (bool)
    retrace_40_60 = messages.get("retrace_40_60", False)
    # 3 velas rojas o verdes según tendencia
    three_candles_tfs = []
    # Doji tfs
    doji_tfs = []
    # High volume tfs
    volume_tfs = []
    # Low spread (5m only)
    low_spread_5m = False

    for extra in messages["extras"]:
        tf, emojis = extra.split(":")
        if "🪶" in emojis:  # MA cerca (spread)
            ma_near_tfs.append(tf)
        if "🔄" in emojis:  # Retrace detected in TF (we'll skip listing here, use flag)
            pass
        if "3c" in emojis:  # Custom marker for 3 candles opposite color
            three_candles_tfs.append(tf)
        if "🌀" in emojis:  # Doji
            doji_tfs.append(tf)
        if "🔊" in emojis:  # High volume
            volume_tfs.append(tf)
        if "5m" == tf and has_low_spread(messages["last_candles"][tf][-1]):
            low_spread_5m = True

    lines = []
    lines.append(f"🔔 {symbol} - {trend_text}")
    lines.append(f"✔️ Tendencia alineada en todos los timeframes")

    if ma_near_tfs:
        lines.append(f"📍 MA20 cerca en: {', '.join(ma_near_tfs)}")

    if retrace_40_60:
        lines.append(f"🔄 Retroceso 40–60%")

    if three_candles_tfs:
        color_candles = "rojas" if trend_val == "UP" else "verdes"
        lines.append(f"📉 3 velas {color_candles} detectadas (retroceso)")

    if doji_tfs:
        lines.append(f"💠 Doji detectado ({', '.join(doji_tfs)})")

    if volume_tfs:
        lines.append(f"📊 Volumen alto ({', '.join(volume_tfs)})")

    if low_spread_5m:
        lines.append(f"📏 Low spread en 5m")

    # Add support/resistance if available
    if messages["support_res"]:
        lines.append("\n🔽 Support/Resistance")
        lines.extend(messages["support_res"])

    content = "\n".join(lines)

    print(content)
    requests.post(NOTIFY_URL, data=content.encode("utf-8"))

def check_retrace_40_60(candles):
    # Simple placeholder example: checks if last candle retraced 40-60% of previous move
    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    if len(closes) < 5:
        return False
    # Find last swing high and low
    last_close = closes[-1]
    prev_close = closes[-2]
    max_high = max(highs[-5:])
    min_low = min(lows[-5:])
    range_ = max_high - min_low
    if range_ == 0:
        return False
    retrace_amount = abs(last_close - prev_close)
    retrace_ratio = retrace_amount / range_

    # Check if retrace between 40% and 60% of range
    return 0.4 <= retrace_ratio <= 0.6

def analyze_symbol(symbol):
    trend_by_tf = {}
    extras = []
    support_res_by_tf = []
    last_candles = {}

    for tf in TIMEFRAMES:
        candles = get_candles(symbol, tf)
        last_candles[tf] = candles
        trend, ma20, ma_status = get_trend_and_ma20(candles)
        if not trend:
            continue

        trend_by_tf[tf] = trend

        extra_line = ""

        # MA20 close ~ spread (🪶)
        if ma_status == "CLOSE":
            extra_line += " 🪶"

        # High volume (🔊) for 5m,15m,30m
        if tf in ["5m", "15m", "30m"] and has_high_volume(candles[-1], candles):
            extra_line += " 🔊"

        # Low spread only 5m (📏)
        if tf == "5m" and has_low_spread(candles[-1]):
            extra_line += " 📏"

        # Doji (🌀)
        if is_doji(candles[-1]):
            extra_line += " 🌀"

        # Retrace (🔄)
        if is_retrace(candles, trend):
            extra_line += " 🔄"

        # Check 3 candles opposite color, mark with "3c" emoji for custom handling
        if has_three_candles_opposite_color(candles, trend):
            extra_line += " 3c"

        if extra_line:
            extras.append(f"{tf}:{extra_line.strip()}")

        if tf in ["1h", "4h", "1d"]:
            support, resistance = get_support_resistance(candles)
            support_res_by_tf.append(f"{tf}: S={support:.2f} R={resistance:.2f}")

    # Check retrace 40-60% on highest timeframe candles (e.g. daily)
    retrace_40_60 = False
    for tf in ["1h", "4h", "1d"]:
        if tf in last_candles and check_retrace_40_60(last_candles[tf]):
            retrace_40_60 = True
            break

    # Solo notificar si todos los timeframes tienen tendencia igual y completa
    if len(trend_by_tf) == len(TIMEFRAMES):
        unique_trends = set(trend_by_tf.values())
        if len(unique_trends) == 1 and unique_trends.pop() in {"UP", "DOWN"}:
            notify(symbol, {
                "trend": trend_by_tf,
                "extras": extras,
                "support_res": support_res_by_tf,
                "retrace_40_60": retrace_40_60,
                "last_candles": last_candles,
            })

if __name__ == "__main__":
    while True:
        for symbol in SYMBOLS:
            try:
                analyze_symbol(symbol)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
        print("Waiting 5 minutes before next check...\n")
        time.sleep(60)

