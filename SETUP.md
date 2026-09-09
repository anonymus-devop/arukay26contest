# Guía de instalación de GAIrden

## Firebase

1. Activa Realtime Database en tu proyecto Firebase.
2. Copia la URL en `FIREBASE_DB_URL`.
3. Genera una clave privada de cuenta de servicio.
4. Para Flask/Render, guarda su contenido completo en `FIREBASE_SERVICE_ACCOUNT_JSON`.
5. Para el puente local, guarda el archivo como `servicio-firebase.json` o configura `FIREBASE_SERVICE_ACCOUNT_FILE`.

La ruta utilizada por el sistema es `/sensors`.

## Micro:bit y puente

Carga `microbit_code.txt` desde MakeCode. Debe emitir una línea CSV con humedad, temperatura y luz cada pocos segundos. Instala dependencias y ejecuta:

```bash
pip install -r requirements.txt
python bridge.py
```

Configura `SERIAL_PORT` si el Micro:bit no está en `COM3`. El puente ignora líneas inválidas y continúa escuchando.

## Backend y dashboard

```bash
python main.py
```

Abre `http://localhost:5000/` y prueba también `/health`, `/api/sensors` y `/analizar`.

## Render

- Build: `pip install -r requirements.txt`
- Start: `gunicorn main:app`

Variables requeridas: `FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_DB_URL` y `DEVICE_INGEST_TOKEN`. `OPENAI_API_KEY` y `GEMINI_API_KEY` son opcionales porque el usuario también puede proporcionar una clave desde el dashboard. Las claves introducidas en la interfaz solo se usan para la solicitud actual y no se almacenan.

## Web Serial

En Chrome o Edge de escritorio, abre la URL HTTPS de Render, introduce `DEVICE_INGEST_TOKEN` en el campo del dashboard y pulsa “Conectar Micro:bit”. Selecciona el puerto USB del Micro:bit. El navegador leerá el CSV y enviará las lecturas a Firebase a través de Flask.

Web Serial necesita una acción explícita del usuario y no está disponible de forma universal en celulares. Si no se desea mantener el navegador abierto, usa `bridge.py` en el computador conectado al Micro:bit.

## Análisis Live

El campo `Datos reales o simulados` acepta `512,24,140` o un JSON con `humidity`, `temperature` y `light`. Las lecturas del Micro:bit y del simulador se copian ahí automáticamente.

Configura en Render `OPENAI_API_KEY` y/o `GEMINI_API_KEY` para habilitar el botón `Hablar con la IA`. También puedes dejar que cada visitante escriba su propia clave en el campo de IA: se usa únicamente para crear esa sesión y se descarta al terminar la petición. OpenAI Realtime usa WebRTC con micrófono/altavoz y Gemini Live usa WebSocket con audio PCM de 16 kHz; el backend entrega la señalización o un token efímero. Los modelos se pueden cambiar con `OPENAI_REALTIME_MODEL` y `GEMINI_LIVE_MODEL`.

## Simulador público

El panel “Simula tu Micro:bit” permite probar humedad, temperatura y luz sin token ni dispositivo físico. La lectura simulada solo se procesa para la demostración y no se guarda en Firebase.
