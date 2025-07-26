import time
import requests
from datetime import datetime

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT","LTCUSDT","TRXUSDT","SOLUSDT","XRPUSDT","ADAUSDT","BCHUSDT"]
NTFY_URL = "https://ntfy.sh/3lvys"

# Obtener velas desde Binance
def get_klines(symbol, interval, limit=21):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Tendencia del precio
def get_price_trend(symbol, interval):
    try:
        candles = get_klines(symbol, interval, limit=2)
        close1 = float(candles[-2][4])
        close2 = float(candles[-1][4])
        if close2 > close1:
            return "up"
        elif close2 < close1:
            return "down"
        else:
            return "flat"
    except Exception as e:
        print(f"[{symbol} - {interval} - PRICE] Error: {e}")
        return None

# Tendencia de la MA20
def get_ma20_trend(symbol, interval):
    try:
        candles = get_klines(symbol, interval, limit=21)
        closes = [float(c[4]) for c in candles]
        ma_prev = sum(closes[-21:-1]) / 20
        ma_curr = sum(closes[-20:]) / 20
        if ma_curr > ma_prev:
            return "up"
        elif ma_curr < ma_prev:
            return "down"
        else:
            return "flat"
    except Exception as e:
        print(f"[{symbol} - {interval} - MA20] Error: {e}")
        return None

# Verifica alineación de tendencia de precio y calcula alineación de MA20
def check_price_alignment(symbol):
    price_trends = []
    ma_trends = []

    for tf in TIMEFRAMES:
        price_trend = get_price_trend(symbol, tf)
        ma_trend = get_ma20_trend(symbol, tf)

        if price_trend is None or price_trend == "flat":
            return None, None  # Cancelar si el precio es plano o error

        price_trends.append(price_trend)
        ma_trends.append(ma_trend)

    # Comprobar si el precio tiene misma dirección en todos los marcos
    if all(t == price_trends[0] for t in price_trends):
        price_direction = price_trends[0]
        # Verificar si la MA20 también coincide en la misma dirección
        if all(t == price_direction for t in ma_trends):
            return price_direction, True
        else:
            return price_direction, False

    return None, None

# Enviar notificación
def send_notification(symbol, direction, ma20_confirma):
    dir_str = "📈 ALCISTA" if direction == "up" else "📉 BAJISTA"
    ma_note = "✅ MA20 confirmada" if ma20_confirma else "❌ MA20 sin confirmar"
    message = f"🔔 {symbol}: Tendencia {dir_str} en el precio en todos los marcos de tiempo\n{ma_note}"
    try:
        response = requests.post(NTFY_URL, data=message.encode("utf-8"))
        if response.status_code == 200:
            print(f"✅ Notificación enviada: {message}")
        else:
            print(f"⚠️ Error al enviar notificación: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")

# Monitor principal
def monitor():
    print("📡 Iniciando monitoreo con tendencia de precio + info MA20...")
    while True:
        print(f"\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        for symbol in SYMBOLS:
            trend, ma20_match = check_price_alignment(symbol)
            if trend:
                dir_str = "📈 ALCISTA" if trend == "up" else "📉 BAJISTA"
                ma_txt = "✅ MA20 confirmada" if ma20_match else "❌ MA20 sin confirmar"
                print(f"🔔 ALERTA: {symbol} tiene tendencia {dir_str} en todos los marcos. {ma_txt}")
                send_notification(symbol, trend, ma20_match)
            else:
                print(f"⏳ {symbol} sin alineación clara de tendencia de precio.")
        time.sleep(300)

if __name__ == "__main__":
    monitor()
