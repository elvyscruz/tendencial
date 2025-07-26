import time
import requests
from datetime import datetime

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT","LTCUSDT","SOLUSDT","TRXUSDT","ADAUSDT","BCHUSDT"]
NTFY_URL = "https://ntfy.sh/3lvys"

def get_klines(symbol, interval, limit=2):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_trend(symbol, interval):
    try:
        candles = get_klines(symbol, interval)
        close1 = float(candles[-2][4])
        close2 = float(candles[-1][4])
        if close2 > close1:
            return "up"
        elif close2 < close1:
            return "down"
        else:
            return "flat"
    except Exception as e:
        print(f"[{symbol} - {interval}] Error: {e}")
        return None

def check_alignment(symbol):
    trends = []
    for tf in TIMEFRAMES:
        trend = get_trend(symbol, tf)
        if trend is None:
            return None
        trends.append(trend)
    if all(t == trends[0] for t in trends) and trends[0] != "flat":
        return trends[0]
    return None

def send_notification(symbol, direction):
    direction_str = "📈 ALCISTA" if direction == "up" else "📉 BAJISTA"
    message = f"🔔 {symbol}: Tendencia {direction_str} en todos los marcos de tiempo"
    try:
        response = requests.post(NTFY_URL, data=message.encode("utf-8"))
        if response.status_code == 200:
            print(f"✅ Notificación enviada: {message}")
        else:
            print(f"⚠️ Error al enviar notificación: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")

def monitor():
    print("📡 Iniciando monitoreo...")
    while True:
        print(f"\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        for symbol in SYMBOLS:
            trend = check_alignment(symbol)
            if trend:
                direction = "📈 ALCISTA" if trend == "up" else "📉 BAJISTA"
                print(f"🔔 ALERTA: {symbol} tiene tendencia {direction} en todos los marcos de tiempo.")
                send_notification(symbol, trend)
            else:
                print(f"⏳ {symbol} sin alineación total de tendencias.")
        time.sleep(300)

if __name__ == "__main__":
    monitor()

