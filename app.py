import requests
import time
import numpy as np
from datetime import datetime, UTC
import json
import urllib.request

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BCHUSDT","LTCUSDT","SOLUSDT","XRPUSDT","BNBUSDT"]
TIMEFRAMES = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w"
}
SLEEP_INTERVAL = 300  # 5 minutes
NTFY_URL = "https://ntfy.sh/3lvys"

def fetch_klines(symbol, interval, limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        return data

def get_trend_and_ma20(candles):
    closes = np.array([float(c[4]) for c in candles])
    if len(closes) < 20:
        return "flat", None, "flat"
    
    ma20 = np.mean(closes[-20:])
    current = closes[-1]
    previous = closes[-2]

    trend = "up" if current > previous else "down" if current < previous else "flat"
    ma_trend = "rising" if ma20 > np.mean(closes[-21:-1]) else "falling" if ma20 < np.mean(closes[-21:-1]) else "flat"
    return trend, ma20, ma_trend

def near_ma20(current, ma20, threshold=0.01):
    return abs(current - ma20) / ma20 < threshold

def has_retrace(candles, direction):
    closes = np.array([float(c[4]) for c in candles])
    highs = np.array([float(c[2]) for c in candles])
    lows = np.array([float(c[3]) for c in candles])

    if direction == "up":
        recent_high = np.max(highs[-10:])
        retrace = (recent_high - closes[-1]) / (recent_high - np.min(lows[-10:]) + 1e-8)
    else:
        recent_low = np.min(lows[-10:])
        retrace = (closes[-1] - recent_low) / (np.max(highs[-10:]) - recent_low + 1e-8)

    return 0.4 <= retrace <= 0.6

def opposite_colored_candles(candles, trend):
    recent = candles[-3:]
    count = 0
    for c in recent:
        open_ = float(c[1])
        close = float(c[4])
        if trend == "up" and close < open_:
            count += 1
        elif trend == "down" and close > open_:
            count += 1
    return count >= 3

def send_notification(symbol, trend, ma_trends, near_ma_times, retrace_times, opposite_candles):
    emoji = "📈" if trend == "up" else "📉"
    message = f"{emoji} {symbol} {trend.upper()} trend on all TFs\n"

    if ma_trends and all(mt == ma_trends[0] for mt in ma_trends):
        message += f"🧠 MA20 {ma_trends[0]}\n"

    if near_ma_times:
        message += f"📍Near MA20: {', '.join(near_ma_times)}\n"

    if retrace_times:
        message += f"🔄 Retrace: {', '.join(retrace_times)}\n"

    if opposite_candles:
        message += f"🕯️ Reversal Candles: {', '.join(opposite_candles)}\n"

    payload = {
        "topic": "3elvys",
        "message": message.strip(),
        "title": f"{symbol} {emoji} ALERT",
        "tags": [trend]
    }
    requests.post(NTFY_URL, data=message.encode('utf-8'), headers={"Content-Type": "text/plain; charset=utf-8"})


def analyze_symbol(symbol):
    print(f"\n[{datetime.now(UTC).strftime('%H:%M:%S')}] Analizando {symbol}...")
    price_directions = []
    ma_trends = []
    near_ma_times = []
    retrace_times = []
    opposite_candles_times = []

    for tf_name, tf_interval in TIMEFRAMES.items():
        try:
            candles = fetch_klines(symbol, tf_interval)
            trend, ma20, ma_trend = get_trend_and_ma20(candles)
            price_directions.append(trend)
            ma_trends.append(ma_trend)

            if tf_name in ["5m", "15m", "30m", "1h"]:
                current = float(candles[-1][4])
                if near_ma20(current, ma20):
                    near_ma_times.append(tf_name)

            if has_retrace(candles, trend):
                retrace_times.append(tf_name)

            if opposite_colored_candles(candles, trend):
                opposite_candles_times.append(tf_name)

        except Exception as e:
            print(f"Error en {symbol} {tf_name}: {e}")
            return

    main_trend = price_directions[0]
    if all(d == main_trend for d in price_directions if d != "flat"):
        print(f"🔔 {symbol}: tendencia {main_trend} en todos los TF")
        send_notification(
            symbol, main_trend, ma_trends,
            near_ma_times, retrace_times,
            opposite_candles_times
        )
    else:
        print(f"{symbol}: no hay tendencia unificada. {price_directions}")

def monitor():
    print("⏳ Iniciando monitoreo...")
    while True:
        print(f"\n⏱️ {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} Monitoreando...")
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    monitor()

