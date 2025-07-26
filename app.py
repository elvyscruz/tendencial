import time
import requests
from datetime import datetime

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
NEAR_MA_TFS = ["5m", "15m", "30m", "1h"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT","SOLUSDT","LTCUSDT","BCHUSDT","ADAUSDT","XRPUSDT","TRXUSDT","DOGEUSDT","HBARUSDT","ONDOUSDT","APTUSDT"]
NTFY_URL = "https://ntfy.sh/3lvys"
NEAR_MA_THRESHOLD = 0.01  # 1%

def get_klines(symbol, interval, limit=50):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def get_price_trend(candles):
    close1 = float(candles[-2][4])
    close2 = float(candles[-1][4])
    if close2 > close1:
        return "up"
    elif close2 < close1:
        return "down"
    return "flat"

def get_ma20_trend(candles):
    closes = [float(c[4]) for c in candles]
    ma1 = sum(closes[-21:-1]) / 20
    ma2 = sum(closes[-20:]) / 20
    if ma2 > ma1:
        return "up"
    elif ma2 < ma1:
        return "down"
    return "flat"

def is_price_near_ma20(candles):
    closes = [float(c[4]) for c in candles]
    ma20 = sum(closes[-20:]) / 20
    last_price = closes[-1]
    deviation = abs(last_price - ma20) / ma20
    return deviation <= NEAR_MA_THRESHOLD

def detect_retracement(candles):
    closes = [float(c[4]) for c in candles]
    recent = closes[-20:]
    highest = max(recent)
    lowest = min(recent)
    current = recent[-1]

    if current > lowest and current < highest:
        if (highest - lowest) == 0:
            return False
        retracement = (current - lowest) / (highest - lowest)
        if 0.4 <= retracement <= 0.6:
            return True
    return False

def analyze_symbol(symbol):
    price_directions = []
    ma_directions = []
    near_ma_tfs = []
    retracement_found = False

    for tf in TIMEFRAMES:
        try:
            candles = get_klines(symbol, tf, limit=50)
            price_dir = get_price_trend(candles)
            ma_dir = get_ma20_trend(candles)

            if tf in NEAR_MA_TFS and is_price_near_ma20(candles):
                near_ma_tfs.append(tf)

            if tf == "1h":  # Usamos 1h para revisar retroceso
                if detect_retracement(candles):
                    retracement_found = True

            price_directions.append(price_dir)
            ma_directions.append(ma_dir)
        except Exception as e:
            print(f"[{symbol} - {tf}] Error: {e}")
            return

    if all(d == price_directions[0] for d in price_directions if d != "flat"):
        direction = price_directions[0]
        message = f"🔔 {symbol} tendencia 📊 {direction.upper()} en TODOS los marcos\n"

        if all(m == ma_directions[0] for m in ma_directions if m != "flat"):
            message += f"✅ MA20 también en tendencia {ma_directions[0]}\n"

        if near_ma_tfs:
            message += f"📍 Precio cerca del MA20 en: {', '.join(near_ma_tfs)}\n"

        if retracement_found:
            message += "🔄 Retroceso detectado de 40% a 60% desde el último movimiento\n"

        try:
            r = requests.post(NTFY_URL, data=message.encode("utf-8"))
            if r.status_code == 200:
                print(f"✅ Notificación enviada: {symbol}")
            else:
                print(f"⚠️ Error al notificar {symbol}: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Error al notificar {symbol}: {e}")
    else:
        print(f"⏳ {symbol}: Sin alineación clara de precios.")

def monitor():
    print("🚀 Iniciando monitoreo...")
    while True:
        print(f"\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
        time.sleep(300)  # Espera 5 minutos

if __name__ == "__main__":
    monitor()

