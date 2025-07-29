import requests
import time
import numpy as np
from datetime import datetime

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT", "XRPUSDT", "BNBUSDT","DOGEUSDT","ADAUSDT","TRXUSDT","HBARUSDT", "ONDOUSDT","SUIUSDT","XLMUSDT","AVAXUSDT","SHIBUSDT","XMRUSDT","PEPEUSDT","APTUSDT","ALGOUSDT", "LINKUSDT","TONUSDT","UNIUSDT","TAOUSDT","NEARUSDT","RENDERUSDT","FETUSDT","DOTUSDT"]

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h","1d"]
API_URL = "https://api.binance.com/api/v3/klines"
NTFY_URL = "https://ntfy.sh/tendencial"
VOLUME_MULTIPLIER = 1.2
SPREAD_THRESHOLD = 0.001 # 1%
MA20_THRESHOLD = 0.005 # near to MA20
RETRACE_RANGE = (30,60) # 30-60%


def get_klines(symbol, interval, limit=100):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def detect_trend(klines):
    closes = [float(k[4]) for k in klines]
    return "bullish" if closes[-1] > closes[0] else "bearish"

def is_ma20_near_price(klines):
    closes = np.array([float(k[4]) for k in klines])
    ma20 = np.mean(closes[-20:])
    return abs(closes[-1] - ma20) / ma20 < MA20_THRESHOLD

def is_retrace(klines):
    closes = [float(k[4]) for k in klines]
    peak = max(closes)
    last = closes[-1]
    retrace_pct = 1 - last / peak
    return RETRACE_RANGE[0] <= retrace_pct <= RETRACE_RANGE(1)

def is_doji(kline):
    open_price = float(kline[1])
    close_price = float(kline[4])
    high = float(kline[2])
    low = float(kline[3])
    body = abs(open_price - close_price)
    range_ = high - low
    return range_ > 0 and body / range_ < 0.1

def is_narrow_range(klines):
    ranges = [float(k[2]) - float(k[3]) for k in klines[-5:]]
    return ranges[-1] < np.percentile(ranges[:-1], 25)

def has_high_volume(kline, recent_klines):
    volumes = [float(k[5]) for k in recent_klines]
    return float(kline[5]) > np.mean(volumes) * VOLUME_MULTIPLIER

def is_low_spread(kline):
    high = float(kline[2])
    low = float(kline[3])
    spread = (high - low) / low
    return spread < SPREAD_THRESHOLD  

def detect_support_resistance(klines):
    closes = [float(k[4]) for k in klines]
    local_min = min(closes[-10:])
    local_max = max(closes[-10:])
    return local_min, local_max

def format_msg(symbol, trend, ma_near, retrace, doji_list, narrow_list, volume_list, low_spread, support, resistance):
    emoji_trend = "⬆️" if trend == "bullish" else "⬇️"
    ma_line = f"📍 MA20 cerca en: {', '.join(ma_near)}" if ma_near else ""
    retrace_line = f"🔄 Retroceso 30–60% en: {', '.join(retrace)}" if retrace else ""
    doji_line = f"💠 Doji: {', '.join(doji_list)}" if doji_list else ""
    narrow_line = f"🗠  Narrow range: {', '.join(narrow_list)}" if narrow_list else ""
    volume_line = f"📊 Volumen alto: {', '.join(volume_list)}" if volume_list else ""
    spread_line = "📏 Low spread en 5m" if low_spread else ""
    sr_line = f"🔽 S/R (1h) {support:.2f} / {resistance:.2f}"
    lines = [
        f"🔔 {symbol} - {emoji_trend} {'Uptrend' if trend == 'bullish' else 'Downtrend'}",
        "✔️ Tendencia alineada en todos los timeframes",
        ma_line,
        retrace_line,
        doji_line,
        narrow_line,
        volume_line,
        spread_line,
        sr_line
    ]
    return "\n".join([line for line in lines if line])

def main():
    while True:
        for symbol in SYMBOLS:
            all_trends = []
            ma_near = []
            retrace = []
            doji_list = []
            narrow_list = []
            volume_list = []
            low_spread = False
            support = resistance = None
            trend_ref = None

            for tf in TIMEFRAMES:
                klines = get_klines(symbol, tf, 100)
                trend = detect_trend(klines)
                all_trends.append(trend)

                if trend_ref is None:
                    trend_ref = trend

                if trend == trend_ref:
                    if is_ma20_near_price(klines):
                        ma_near.append(tf)

                    if is_retrace(klines):
                        retrace.append(tf)

                    if is_doji(klines[-1]):
                        doji_list.append(tf)

                    if is_narrow_range(klines):
                        narrow_list.append(tf)

                    if tf in ["5m", "15m", "30m"] and has_high_volume(klines[-1], klines[-6:-1]):
                        volume_list.append(tf)

                    if tf == "5m" and is_low_spread(klines[-1]):
                        low_spread = True

                    if tf == "1h":
                        support, resistance = detect_support_resistance(klines)

            if all(t == trend_ref for t in all_trends):
                msg = format_msg(
                    symbol, trend_ref, ma_near, retrace,
                    doji_list, narrow_list, volume_list,
                    low_spread, support, resistance
                )
                print(datetime.now())
                print(msg)
                print("")

        time.sleep(300)

if __name__ == "__main__":
    main()

