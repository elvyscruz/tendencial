import requests
import time
import numpy as np
from datetime import datetime, timezone

# Configuración
SYMBOLS = ['BTCUSDT', 'ETHUSDT','SOLUSDT','LTCUSDT','BCHUSDT','DOGEUSDT','TRXUSDT','ADAUSDT','HBARUSDT','XRPUSDT']  # Puedes agregar más símbolos aquí
TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d', '1w']
CHECK_INTERVAL = 300  # 5 minutos
NTFY_URL = 'https://ntfy.sh/3lvys'
CLOSE_TO_MA_THRESHOLD = 0.005  # 0.5%

def fetch_klines(symbol, interval, limit=50):
    url = f'https://api.binance.com/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"Error al obtener datos para {symbol} {interval}: {r.status_code}")
        return []
    return r.json()

def get_trend_and_ma20(candles):
    closes = []
    for c in candles:
        if isinstance(c, (list, tuple)) and len(c) > 4:
            closes.append(float(c[4]))
        else:
            print(f"Elemento inválido en candles: {c}")
    closes = np.array(closes)
    if len(closes) < 21:
        print("No hay suficientes datos para calcular MA20")
        return "flat", 0, "flat"
    ma20 = np.mean(closes[-20:])
    ma_prev = np.mean(closes[-21:-1])
    trend = "up" if closes[-1] > closes[0] else "down"
    ma_trend = "rising" if ma20 > ma_prev else "falling" if ma20 < ma_prev else "flat"
    return trend, ma20, ma_trend

def is_close_to_ma20(current_price, ma20):
    return abs(current_price - ma20) / ma20 < CLOSE_TO_MA_THRESHOLD

def calculate_retracement(closes):
    peak = max(closes)
    trough = min(closes)
    last_price = closes[-1]
    if peak == trough:
        return False
    if last_price < peak:
        retracement = (peak - last_price) / (peak - trough)
    elif last_price > trough:
        retracement = (last_price - trough) / (peak - trough)
    else:
        retracement = 0
    return 0.4 <= retracement <= 0.6

def count_consecutive_candle_colors(candles):
    count = 0
    direction = None
    for c in candles[-3:]:
        open_price = float(c[1])
        close_price = float(c[4])
        if close_price > open_price:
            if direction == 'red':
                return 0
            direction = 'green'
            count += 1
        elif close_price < open_price:
            if direction == 'green':
                return 0
            direction = 'red'
            count += 1
    return count if count >= 3 else 0

def analyze_symbol(symbol):
    print(f"\nAnalizando {symbol}...")
    price_directions = []
    ma_directions = []
    ma_values = {}
    close_to_ma = []
    retracements = []
    candles_info = []

    for tf in TIMEFRAMES:
        candles = fetch_klines(symbol, tf)
        if not candles:
            print(f"No se obtuvieron datos para {symbol} en {tf}")
            return
        trend, ma20, ma_trend = get_trend_and_ma20(candles)
        closes = [float(c[4]) for c in candles if isinstance(c, (list, tuple)) and len(c) > 4]
        current_price = closes[-1] if closes else None

        price_directions.append(trend)
        ma_directions.append(ma_trend)
        ma_values[tf] = ma20

        if tf in ['5m', '15m', '30m', '1h'] and current_price is not None and is_close_to_ma20(current_price, ma20):
            close_to_ma.append(tf)

        if current_price is not None and calculate_retracement(closes):
            retracements.append(tf)

        same_color_count = count_consecutive_candle_colors(candles)
        candles_info.append((tf, same_color_count))

    print(f"Tendencias de precio: {price_directions}")
    print(f"Tendencias MA20: {ma_directions}")
    print(f"Precios cerca del MA20 en: {close_to_ma if close_to_ma else 'ninguno'}")
    print(f"Retrocesos detectados en: {retracements if retracements else 'ninguno'}")
    cpat = {tf: cnt for tf, cnt in candles_info if cnt >= 3}
    if cpat:
        print(f"Velas consecutivas detectadas en: {cpat}")
    else:
        print("No hay velas consecutivas relevantes")

    if all(d == price_directions[0] for d in price_directions):
        direction = price_directions[0]
        ma_aligned = all(m == ma_directions[0] for m in ma_directions)
        ma_direction = ma_directions[0]
        message = f"🔔 {symbol} tendencia {direction.upper()} en TODOS los marcos de tiempo.\n"
        if ma_aligned:
            message += f"✔️ MA20 también en tendencia {ma_direction}\n"
        if close_to_ma:
            message += f"📍 Precio cerca del MA20 en: {', '.join(close_to_ma)}\n"
        if retracements:
            message += f"🔄 Retroceso del 40-60% detectado en: {', '.join(retracements)}\n"
        if cpat:
            candle_color = "rojas" if direction == "up" else "verdes"
            candle_str = ", ".join([f"{tf} ({cnt})" for tf, cnt in cpat.items()])
            message += f"🕯️ Últimas 3+ velas {candle_color} consecutivas en: {candle_str}\n"

        print(f"ALERTA: {message}")
        try:
            r = requests.post(NTFY_URL, data=message.encode("utf-8"))
            if r.status_code == 200:
                print("Notificación enviada correctamente.")
            else:
                print(f"Error al enviar notificación: {r.status_code}")
        except Exception as e:
            print(f"Error enviando notificación: {e}")
    else:
        print(f"{symbol} no tiene tendencia unificada en todos los marcos de tiempo.")

def monitor():
    print("Iniciando monitoreo...")
    while True:
        print(f"\n===== {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} =====")
        for symbol in SYMBOLS:
            try:
                analyze_symbol(symbol)
            except Exception as e:
                print(f"Error analizando {symbol}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()

