import requests
import time
import datetime
import numpy as np
import json
import urllib.request

# Configuración
SYMBOLS = ["BTCUSDT", "ETHUSDT","LTCUSDT","BCHUSDT","SOLUSDT","XRPUSDT","BNBUSDT","ADAUSDT","TRXUSDT","DOGEUSDT"]
TIMEFRAMES = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"
}
SLEEP_INTERVAL = 300  # 5 minutos
NTFY_URL = "https://ntfy.sh/3lvys"

# Función para obtener velas
def get_candles(symbol, interval, limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

# Determinar tendencia y MA20
def get_trend_and_ma20(candles):
    closes = np.array([float(c[4]) for c in candles])
    ma20 = closes[-20:].mean()
    trend = "up" if closes[-1] > closes[0] else "down"
    ma_trend = "rising" if ma20 > closes[-30:-10].mean() else "declining"
    return trend, ma20, ma_trend

# Verificar si precio está cerca del MA20
def is_close_to_ma20(price, ma20, threshold=0.01):
    return abs(price - ma20) / ma20 < threshold

# Detectar retroceso del 40-60%
def detect_retrace(candles):
    closes = np.array([float(c[4]) for c in candles])
    high = closes.max()
    low = closes.min()
    last = closes[-1]
    if last < high and last > low:
        drop = (high - last) / (high - low)
        if 0.4 <= drop <= 0.6:
            return True
    return False

# Verificar retroceso por color de velas
def is_retrace_by_color(candles, main_trend):
    count = 0
    for c in candles[-5:]:
        open_, close = float(c[1]), float(c[4])
        is_red = close < open_
        is_green = close > open_
        if (main_trend == "up" and is_red) or (main_trend == "down" and is_green):
            count += 1
    return count >= 3

# Notificación
def send_notification(symbol, trend, info):
    msg = f"{symbol} → {trend.upper()}\n{info}"
    requests.post(NTFY_URL, data=msg.encode())

# Análisis por símbolo
def analyze_symbol(symbol):
    print(f"\n{symbol} -> analizando...")
    price_directions, ma20_matches, ma_trends, retrace_flags, color_retrace_flags = [], [], [], [], []

    for tf_name, tf in TIMEFRAMES.items():
        try:
            candles = get_candles(symbol, tf)
            trend, ma20, ma_trend = get_trend_and_ma20(candles)
            last_price = float(candles[-1][4])

            price_directions.append(trend)
            ma_trends.append(ma_trend)

            if tf_name in ["5m", "15m", "30m", "1h"]:
                close_to_ma = is_close_to_ma20(last_price, ma20)
                ma20_matches.append(close_to_ma)
            else:
                ma20_matches.append(False)

            retrace_flags.append(detect_retrace(candles))
            color_retrace_flags.append(is_retrace_by_color(candles, trend))

        except Exception as e:
            print(f"Error procesando {symbol} {tf}: {e}")
            return

    # Validar tendencia unificada
    if all(d == price_directions[0] for d in price_directions):
        info = []
        if all(mt == ma_trends[0] for mt in ma_trends):
            info.append(f"MA20: {ma_trends[0]}")
        if any(ma20_matches):
            info.append("Cerca MA20 (TF cortos)")
        if any(retrace_flags):
            info.append("Retroceso 40-60%")
        if any(color_retrace_flags):
            info.append("3+ velas opuestas")

        print(f"{symbol}: tendencia UNIFICADA → {price_directions[0]}")
        send_notification(symbol, price_directions[0], " | ".join(info))
    else:
        print(f"{symbol}: sin tendencia clara. Direcciones: {price_directions}")

# Bucle principal
def monitor():
    print("Iniciando monitoreo de tendencias...")
    while True:
        print(f"\n⏰ {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    monitor()

