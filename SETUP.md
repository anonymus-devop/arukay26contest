# Guía de instalación de Huerto AI

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

Variables requeridas: `FIREBASE_SERVICE_ACCOUNT_JSON` y `FIREBASE_DB_URL`. `OPENAI_API_KEY` y `GEMINI_API_KEY` son opcionales porque el usuario también puede proporcionar una clave desde el dashboard. Las claves introducidas en la interfaz solo se usan para la solicitud actual y no se almacenan.
