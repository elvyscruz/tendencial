import requests
import time
import numpy as np
from datetime import datetime, timedelta

BASE_URL = "https://api.binance.com/api/v3/klines"
NOTIFY_URL = "https://ntfy.sh/tendencial"
SYMBOLS = ["BTCUSDT", "ETHUSDT","LTCUSDT","BCHUSDT","SOLUSDT","ADAUSDT","HBARUSDT","BNBUSDT","TRXUSDT","HBARUSDT"]
INTERVALS = {
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w"
}
MA_PROXIMITY_TFS = {"5m", "15m", "30m", "1h"}
SLEEP_SECONDS = 300  # 5 minutos
RETRACE_MIN = 0.4
RETRACE_MAX = 0.6

def fetch_candles(symbol, interval, limit=50):
    try:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[{symbol}][{interval}] Error fetching candles: {e}")
        return []

def get_trend_and_ma(candles):
    try:
        closes = np.array([float(c[4]) for c in candles])
        opens = np.array([float(c[1]) for c in candles])
        volumes = np.array([float(c[5]) for c in candles])

        if len(closes) < 21:
            return None

        trend = "up" if closes[-1] > closes[0] else "down"
        ma20 = np.mean(closes[-20:])
        ma_trend = "rising" if ma20 > np.mean(closes[-40:-20]) else "falling"

        proximity = abs(closes[-1] - ma20) / ma20 < 0.01

        # Retroceso
        max_price = np.max(closes[:-1])
        min_price = np.min(closes[:-1])
        retrace = 0
        if trend == "up":
            retrace = (max_price - closes[-1]) / (max_price - min_price) if max_price > min_price else 0
        else:
            retrace = (closes[-1] - min_price) / (max_price - min_price) if max_price > min_price else 0

        retrace_ok = RETRACE_MIN <= retrace <= RETRACE_MAX

        # Últimas 3 velas contra tendencia (retroceso)
        last_3 = candles[-3:]
        retrace_bars = 0
        for c in last_3:
            o, h, l, cl = float(c[1]), float(c[2]), float(c[3]), float(c[4])
            if trend == "up" and cl < o:
                retrace_bars += 1
            if trend == "down" and cl > o:
                retrace_bars += 1

        # Doji / Narrow Range Bar
        last_bar = candles[-1]
        o, h, l, cl = float(last_bar[1]), float(last_bar[2]), float(last_bar[3]), float(last_bar[4])
        body = abs(cl - o)
        range_ = h - l
        doji = body / range_ < 0.2 if range_ > 0 else False

        # Volumen alto
        vol = volumes[-1]
        vol_mean = np.mean(volumes[-20:])
        high_volume = vol > vol_mean * 1.5

        # Low spread (solo para 5m)
        low_spread = range_ / cl < 0.005 if cl > 0 else False

        return {
            "trend": trend,
            "ma20": ma20,
            "ma_trend": ma_trend,
            "proximity": proximity,
            "retrace_ok": retrace_ok,
            "retrace_bars": retrace_bars >= 3,
            "doji": doji,
            "high_volume": high_volume,
            "low_spread": low_spread
        }
    except Exception as e:
        print(f"Error in trend/MA calculation: {e}")
        return None

def analyze_symbol(symbol):
    print(f"\n🔍 Checking {symbol} at {datetime.now().strftime('%H:%M:%S')}")
    all_trends = []
    ma_agreement = []
    proximity_list = []
    extra_info = []

    for tf_name, interval in INTERVALS.items():
        candles = fetch_candles(symbol, interval)
        if not candles or len(candles) < 21:
            print(f"⚠️  Not enough data for {symbol} - {interval}")
            return

        res = get_trend_and_ma(candles)
        if not res:
            print(f"⚠️  Failed analysis for {symbol} - {interval}")
            return

        all_trends.append(res["trend"])
        ma_agreement.append(res["ma_trend"])
        if tf_name in MA_PROXIMITY_TFS and res["proximity"]:
            proximity_list.append(tf_name)

        if res["retrace_ok"]:
            extra_info.append(f"🔁 Retrace {tf_name}")
        if res["retrace_bars"]:
            extra_info.append(f"🕯️ Retro bars {tf_name}")
        if res["doji"]:
            extra_info.append(f"🤏 Doji {tf_name}")
        if res["high_volume"]:
            extra_info.append(f"📈 Vol+ {tf_name}")
        if tf_name == "5m" and res["low_spread"]:
            extra_info.append(f"💧 Low Spread")

    if len(set(all_trends)) == 1:
        trend = all_trends[0]
        direction = "📈 UP" if trend == "up" else "📉 DOWN"
        ma_confirm = "✅ MA20 OK" if len(set(ma_agreement)) == 1 else "⚠️ MA20 Mixed"
        ma_close = f"📍Near MA20: {', '.join(proximity_list)}" if proximity_list else ""
        extras = " | ".join(extra_info)

        msg = f"{symbol} {direction}\n{ma_confirm}\n{ma_close}\n{extras}".strip()
        print(f"🚨 ALERT: {msg}")
        requests.post(NOTIFY_URL, data=msg.encode("utf-8"))
    else:
        print(f"⏸️ No uniform trend for {symbol}")

def main():
    while True:
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
        print(f"🕒 Waiting {SLEEP_SECONDS//60} min...\n")
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()

