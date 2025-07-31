import requests
import time
import numpy as np
import pandas as pd
from datetime import datetime

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LTCUSDT", "BCHUSDT", "XRPUSDT", "BNBUSDT","DOGEUSDT","ADAUSDT","TRXUSDT","HBARUSDT", "ONDOUSDT","SUIUSDT","PAXGUSDT"]

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h","1d"]
API_URL = "https://api.binance.com/api/v3/klines"
NTFY_URL = "https://ntfy.sh/tendencial"
VOLUME_MULTIPLIER = 1.2
SPREAD_THRESHOLD = 0.001  # 1%
MA20_THRESHOLD = 0.005  # near to MA20
RETRACE_RANGE = (4, 7)  # 4%-10%
FIBONACCI_LEVELS = [0.382, 0.5, 0.618, 0.786]  # Niveles clave de Fibonacci

# --- Funciones de Fibonacci ---
def calculate_fibonacci_levels(high, low):
    diff = high - low
    return {
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
    }

def is_fibonacci_retracement_valid(current_price, fib_levels, tolerance=0.01):
    for level, price in fib_levels.items():
        if abs(current_price - price) / price <= tolerance:
            return f"✅ Fibonacci {level}% ({price:.2f})"
    return None

# --- Funciones de Ondas de Elliott (actualizadas con Fibonacci) ---
def detect_elliott_waves(df, timeframe):
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # Detección de impulso (5 ondas)
    if len(closes) >= 5:
        impulse_conditions = (
            (closes[-5] < closes[-3] < closes[-1]) and  # Onda 1 < 3 < 5
            (closes[-4] > closes[-5] and closes[-4] > closes[-3]) and  # Onda 2 correctiva
            (closes[-2] > closes[-3] and closes[-2] > closes[-1])  # Onda 4 correctiva
        )
        
        if impulse_conditions:
            return "🔼 Impulso Elliott detectado (Posible Onda 3)"

    # Detección de corrección ABC con Fibonacci
    if len(closes) >= 3:
        wave_A_high = max(highs[-3:-1])
        wave_A_low = min(lows[-3:-1])
        fib_levels = calculate_fibonacci_levels(wave_A_high, wave_A_low)
        current_price = closes[-1]
        
        fib_signal = is_fibonacci_retracement_valid(current_price, fib_levels)
        correction_conditions = (
            (closes[-3] > closes[-2] < closes[-1]) and  # Estructura ABC
            (fib_signal is not None)  # Confirma Fibonacci
        )
        
        if correction_conditions:
            return f"🔽 Corrección ABC en {fib_signal}"

    return None

# --- Funciones existentes (sin cambios) ---
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
    retrace_pct = (1 - last / peak) * 100
    return RETRACE_RANGE[0] <= retrace_pct <= RETRACE_RANGE[1]

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

# --- Función de mensaje actualizada ---
def format_msg(symbol, trend, ma_near, retrace, doji_list, narrow_list, volume_list, low_spread, support, resistance, elliott_signals):
    emoji_trend = "⬆️" if trend == "bullish" else "⬇️"
    ma_line = f"📍 MA20 cerca en: {', '.join(ma_near)}" if ma_near else ""
    retrace_line = f"🔄 Retroceso {RETRACE_RANGE[0]}%-{RETRACE_RANGE[1]}% en: {', '.join(retrace)}" if retrace else ""
    doji_line = f"💠 Doji: {', '.join(doji_list)}" if doji_list else ""
    narrow_line = f"🗠 Narrow range: {', '.join(narrow_list)}" if narrow_list else ""
    volume_line = f"📊 Volumen alto: {', '.join(volume_list)}" if volume_list else ""
    spread_line = "📏 Low spread en 5m" if low_spread else ""
    sr_line = f"⚟ Support / Resistance (1h) {support:.2f} / {resistance:.2f}"
    elliott_line = "\n".join(elliott_signals) if elliott_signals else ""
    
    lines = [
        f"🔔 {symbol} - {emoji_trend} {'Uptrend' if trend == 'bullish' else 'Downtrend'}",
        "✔️ Tendencia alineada en todos los timeframes",
        ma_line,
        retrace_line,
        doji_line,
        narrow_line,
        volume_line,
        spread_line,
        sr_line,
        elliott_line
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
            elliott_signals = []

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

                    # Análisis de Elliott + Fibonacci (1h y 4h)
                    if tf in ["1h", "4h"]:
                        df = pd.DataFrame(klines, columns=[
                            'time', 'open', 'high', 'low', 'close', 'volume', 
                            'close_time', 'quote_asset_volume', 'trades', 
                            'taker_buy_base', 'taker_buy_quote', 'ignore'
                        ])
                        df['close'] = df['close'].astype(float)
                        df['high'] = df['high'].astype(float)
                        df['low'] = df['low'].astype(float)
                        signal = detect_elliott_waves(df, tf)
                        if signal:
                            elliott_signals.append(f"{signal} ({tf})")

            if all(t == trend_ref for t in all_trends):
                msg = format_msg(
                    symbol, trend_ref, ma_near, retrace,
                    doji_list, narrow_list, volume_list,
                    low_spread, support, resistance, elliott_signals
                )
                print(datetime.now())
                print(msg)
                print("")

        time.sleep(300)

if __name__ == "__main__":
    main()
