
# 📈 Tendencial - Crypto Trend Signal Notifier

Este programa analiza la acción del precio de criptomonedas en múltiples temporalidades para detectar señales de continuación de tendencia o retrocesos significativos. Las señales son enviadas vía notificación HTTP (ntfy.sh).

---

## 🚀 Características principales

- **Análisis multitemporal**: Evalúa las tendencias en 5m, 15m, 30m, 1h, 4h y 1d.
- **Detección de tendencias**: Calcula la media móvil de 20 periodos (MA20) y la compara con el precio actual para determinar la tendencia.
- **Confirmación de tendencia**: Verifica si la dirección de la tendencia coincide en todos los timeframes.
- **MA20 cercano**: Detecta si el precio está cerca de la MA20 en alguna temporalidad.
- **Retroceso significativo**: Señala retrocesos entre el 40% y 60% desde el último pico o valle.
- **Velas de retroceso**: Identifica si hay 3 o más velas consecutivas contrarias a la tendencia como posible retroceso.
- **Velas Doji o de rango estrecho**: Detecta patrones de indecisión o consolidación.
- **Análisis de volumen** (solo 5m, 15m y 30m): Marca volúmenes superiores a la media reciente como significativos.
- **Low spread** (solo 5m): Indica si la vela actual tiene una diferencia pequeña entre apertura y cierre (baja volatilidad).

---

## 🔔 Notificaciones

Las alertas se envían a través de [ntfy.sh](https://ntfy.sh) e incluyen:

- Tendencia principal con emoji (⬆️ o ⬇️)
- Confirmaciones de tendencia
- Timeframes donde el MA20 está cerca
- Alertas de retroceso y volumen
- Detección de velas contrarias, Doji o low spread

Ejemplo:

```

🔔 BTC/USDT - ⬆️ Uptrend
✔️ Tendencia alineada en todos los timeframes
📍 MA20 cerca en: 5m, 15m
🔄 Retroceso 40–60%
📉 3 velas rojas detectadas (retroceso)
💠 Doji detectado (15m)
📊 Volumen alto (5m, 15m)
📏 Low spread en 5m

````

---

## ⚙️ Requisitos

Python 3.10+

Instalar dependencias:
```bash
pip install -r requirements.txt
````

---

## 📁 Estructura del proyecto

```
tendencial/
│
├── app.py               # Código principal
├── requirements.txt     # Dependencias
└── README.md            # Documentación
```

---

## ⚙️ Parametrización

Puedes ajustar los siguientes parámetros directamente en `app.py`:

| Parámetro           | Descripción                                                               |
| ------------------- | ------------------------------------------------------------------------- |
| `SYMBOLS`           | Lista de símbolos a analizar (ej. `["BTC/USDT", "ETH/USDT"]`)             |
| `TIMEFRAMES`        | Temporalidades a evaluar                                                  |
| `MA_PERIOD`         | Periodo para la media móvil (default: 20)                                 |
| `RETRACE_RANGE`     | Rango porcentual de retroceso considerado significativo (default: 40–60%) |
| `VOLUME_MULTIPLIER` | Umbral para considerar volumen alto (ej. > 1.2 \* media)                  |
| `SPREAD_THRESHOLD`  | Umbral para considerar una vela como de low spread                        |
| `NTFY_TOPIC_URL`    | URL del topic de NTFY para recibir notificaciones                         |

---

## 🧪 Estado actual

* ✅ Estable y funcional
* 🛠 En desarrollo para agregar más patrones técnicos (soporte/resistencia, RSI, etc.)
* 🚫 No ejecuta operaciones reales (puede integrarse en el futuro)

---

## 🤝 Cómo contribuir

Contribuciones son bienvenidas. Puedes reportar errores, sugerir mejoras o enviar pull requests. 

--

## ✍️ Autor

Desarrollado por \[elvys cruz] como herramienta de análisis técnico automatizado para criptomonedas.


