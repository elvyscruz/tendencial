# 📈 Tendencial - Crypto Trend Signal Notifier

Este programa analiza la acción del precio de criptomonedas en múltiples temporalidades para detectar señales de continuación de tendencia o retrocesos significativos.

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

- **Cálculo de niveles de soporte y resistencia** (1h) Calcula los niveles de soporte y resistencia a 1 hora

---

## 🔔 Indicadores de Tendencias

Los indicadores de tendencias generados son los iguientes:

- Tendencia principal con emoji (⬆️ o ⬇️)
- Confirmaciones de tendencia
- Timeframes donde el MA20 está cerca
- Alertas de retroceso y volumen
- Detección de velas contrarias, Doji o low spread
- Deteccion de Impulso de Elliot detectado en 4h

Ejemplo de Salida:

```

🔔 BTC/USDT - ⬆️ Uptrend
✔️ Tendencia alineada en todos los timeframes
📍 MA20 cerca en: 5m, 15m
🔄 Retroceso 40–60%
💠 Doji detectado (15m)
📊 Volumen alto (5m, 15m)
📏 Low spread en 5m
🔽 S/R (1h) 113,567.80 / 110,603.10
🔼 Impulso Elliott detectado en 4h (Posible Onda 3)


```

---

**📌 Tabla de Mensajes: Análisis Técnico + Elliott Wave + Fibonacci**

| **Mensaje**                               | **Significado**                                                                  | **Cuándo Ocurre**                                                     | **Acción Sugerida**                                                                     |
| ----------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `🔔 SYMBOL - ⬆️ Uptrend`                  | Tendencia alcista alineada en todos los timeframes.                              | - Cuando el precio hace máximos y mínimos crecientes en D1, 4h, 1h.   | **Operar en largo**. Buscar entradas en retrocesos (Onda 2, 4 o ABC).                   |
| `🔔 SYMBOL - ⬇️ Downtrend`                | Tendencia bajista alineada en todos los timeframes.                              | - Cuando el precio hace máximos y mínimos decrecientes en D1, 4h, 1h. | **Operar en corto**. Buscar entradas en rallies correctivos.                            |
| `📍 MA20 cerca en: 1h, 4h`                | El precio está cerca de la media móvil de 20 períodos (soporte/resistencia).     | - En retrocesos durante una tendencia.                                | Confirmar con velas de reversión. Usar MA20 como zona de entrada.                       |
| `🔄 Retroceso 30–60% en: 1h`              | El precio retrocedió entre 30% y 60% desde el último máximo/mínimo.              | - Durante ondas 2, 4 o correcciones ABC.                              | Buscar entradas si coincide con Fibonacci (ej: 50% o 61.8%).                            |
| `💠 Doji: 1h, 4h`                         | Apareció una vela Doji (indecisión del mercado).                                 | - En soportes/resistencias o niveles clave.                           | Esperar confirmación (vela alcista/bajista siguiente).                                  |
| `🗠 Narrow range: 1h`                      | Rango de precio estrecho (posible consolidación antes de breakout).              | - Antes de rupturas de S/R o continuación de tendencia.               | Prepararse para operar el breakout con volumen.                                         |
| `📊 Volumen alto: 15m, 30m`               | Aumento anormal de volumen (confirma interés en la dirección del movimiento).    | - En rupturas de S/R o inicio de ondas impulsivas (Onda 3).           | Validar con estructura de Elliott.                                                      |
| `📏 Low spread en 5m`                     | Spread bajo entre máximo y mínimo (poca volatilidad temporal).                   | - Antes de movimientos fuertes (acumulación/distribución).            | Monitorizar para posibles breakouts.                                                    |
| `🔽 S/R (1h) 50.0 / 52.0`                 | Niveles de soporte/resistencia clave detectados.                                 | - En zonas de rechazo histórico o retrocesos.                         | Usar para colocar stops o tomar ganancias.                                              |
| `🔼 Impulso Elliott detectado en 4h`      | Confirmación de ondas 1-3-5 (fase impulsiva).                                    | - Tras una corrección validada (ABC o retroceso Fibonacci).           | Entrar en la dirección de la tendencia. Stop en inicio de la Onda 1.                    |
| `🔽 Corrección ABC en ✅ Fibonacci 61.8%` | Fin de corrección ABC en nivel Fibonacci clave (alta probabilidad de reversión). | - Tras un impulso previo (Onda 1 o 3).                                | Entrar en dirección de la tendencia principal. Stop por debajo del mínimo de la Onda C. |
| `✅ Fibonacci 61.8% (52000.00)`           | Precio en nivel clave de retroceso Fibonacci (61.8%).                            | - Durante ondas 2, 4 o correcciones ABC.                              | Buscar entradas si hay confirmación de reversión (velas, volumen).                      |

---

## ⚙️ Requisitos

Python 3.10+

Instalar dependencias:

```bash
pip install -r requirements.txt
```

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
| `RETRACE_RANGE`     | Rango porcentual de retroceso considerado significativo (default: 40–60%) |
| `VOLUME_MULTIPLIER` | Umbral para considerar volumen alto (ej. > 1.2 \* media)                  |
| `SPREAD_THRESHOLD`  | Umbral para considerar una vela como de low spread                        |
| `NTFY_TOPIC_URL`    | URL del topic de NTFY para recibir notificaciones                         |

---

## 🧪 Estado actual

- ✅ Estable y funcional
- 🛠 En desarrollo para agregar más patrones técnicos (soporte/resistencia, RSI, etc.)
- 🚫 No ejecuta operaciones reales (puede integrarse en el futuro)

---

## 🤝 Cómo contribuir

Contribuciones son bienvenidas. Puedes reportar errores, sugerir mejoras o enviar pull requests.

---

## ✍️ Autor

Desarrollado por \[elvys cruz] en Dominican Republic 🇩🇴
