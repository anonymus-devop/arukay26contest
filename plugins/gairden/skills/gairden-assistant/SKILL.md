---
name: gairden-assistant
description: Asistente para monitorear y cuidar el huerto escolar inteligente GAIrden usando lecturas de sensores y consejos agronómicos.
---

# GAIrden Assistant Skill

Usa esta skill cuando el usuario pregunte sobre el estado de su huerto escolar, las plantas, humedad, temperatura o luz.

## Herramientas MCP disponibles
- `consultar_sensores`: Obtiene las lecturas en tiempo real de humedad (0-1023), temperatura (°C) y nivel de luz (0-255).
- `obtener_consejo`: Genera recomendaciones de cuidado y riego para las plantas basadas en las condiciones actuales.

## Umbrales de referencia agronómica
- **Humedad del suelo:**
  - `< 350`: Tierra seca, requiere riego pronto.
  - `350 - 850`: Rango óptimo y equilibrado.
  - `> 850`: Exceso de agua, riesgo de asfixia radicular.
- **Temperatura:**
  - `< 12 °C`: Frío, proteger del viento o heladas.
  - `12 °C - 32 °C`: Rango ideal de crecimiento.
  - `> 32 °C`: Calor excesivo, asegurar sombra y ventilación.
- **Luz:**
  - `< 80`: Poca luz, acercar a ventana o fuente luminosa.
  - `> 240`: Sol directo intenso, vigilar evaporación rápida.
