import time
import requests
from datetime import datetime

TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
SHORT_TIMEFRAMES = ["5m", "15m", "30m", "1h"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "LTCUSDT","BCHUSDT","XRPUSDT","SOLUSDT","DOGEUSDT","ADAUSDT","SUIUSDT","ONDOUSDT","HBARUSDT", "BNBUSDT"]
NTFY_URL = "https://ntfy.sh/3lvys"
SLEEP_INTERVAL = 300  # 5 minutes
CLOSE_TO_MA_PERCENT = 0.5  # porcentaje permitido para estar "cerca" del MA20


def get_klines(symbol, interval, limit=21):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_price_trend(candles):
    close1 = float(candles[-2][4])
    close2 = float(candles[-1][4])
    if close2 > close1:
        return "up"
    elif close2 < close1:
        return "down"
    else:
        return "flat"


def get_ma20_trend(candles):
    closes = [float(c[4]) for c in candles[-21:]]
    ma_now = sum(closes[1:]) / 20
    ma_prev = sum(closes[:-1]) / 20
    if ma_now > ma_prev:
        return "rising"
    elif ma_now < ma_prev:
        return "falling"
    else:
        return "flat"


def is_close_to_ma20(candles, percent_threshold=0.5):
    closes = [float(c[4]) for c in candles[-21:]]
    ma = sum(closes) / 20
    current_price = float(candles[-1][4])
    diff_percent = abs(current_price - ma) / ma * 100
    return diff_percent <= percent_threshold


def analyze_symbol(symbol):
    price_directions = []
    ma20_directions = []
    close_to_ma = []

    for tf in TIMEFRAMES:
        try:
            candles = get_klines(symbol, tf, 21)
            price_trend = get_price_trend(candles)
            ma20_trend = get_ma20_trend(candles)

            price_directions.append(price_trend)
            ma20_directions.append(ma20_trend)

            if tf in SHORT_TIMEFRAMES:
                close_to = is_close_to_ma20(candles, CLOSE_TO_MA_PERCENT)
                close_to_ma.append((tf, close_to))
        except Exception as e:
            print(f"[{symbol}-{tf}] Error: {e}")
            return None

    # Verificar si todas las direcciones de precio coinciden
    if all(d == price_directions[0] for d in price_directions if d != "flat"):
        aligned_trend = price_directions[0]
        info = {
            "symbol": symbol,
            "trend": aligned_trend,
            "ma20_trend": ma20_directions,
            "ma20_agreement": all(m == ma20_directions[0] for m in ma20_directions if m != "flat"),
            "ma20_status": ma20_directions[0],
            "close_to_ma20": [tf for tf, close in close_to_ma if close]
        }
        return info
    return None


def send_notification(info):
    trend_str = "📈 ALCISTA" if info["trend"] == "up" else "📉 BAJISTA"
    message = f"🔔 {info['symbol']} tendencia {trend_str} en TODOS los marcos de tiempo.\n"

    if info["ma20_agreement"]:
        ma_str = "↗️ RISING" if info["ma20_status"] == "rising" else "↘️ FALLING"
        message += f"✔️ MA20 también alineada: {ma_str}.\n"

    if info["close_to_ma20"]:
        tf_str = ", ".join(info["close_to_ma20"])
        message += f"💡 Precio cerca del MA20 en: {tf_str}.\n"

    try:
        r = requests.post(NTFY_URL, data=message.encode("utf-8"))
        if r.status_code == 200:
            print(f"✅ Notificación enviada:\n{message}")
        else:
            print(f"⚠️ Error al enviar notificación: {r.status_code}")
    except Exception as e:
        print(f"⚠️ Excepción al enviar notificación: {e}")


def monitor():
    print("📡 Iniciando monitoreo...")
    while True:
        print(f"\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        for symbol in SYMBOLS:
            result = analyze_symbol(symbol)
            if result:
                send_notification(result)
            else:
                print(f"⏳ {symbol} sin alineación clara de tendencia.")
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    monitor()

