# Huerto AI

MVP de huerto inteligente: un Micro:bit envía lecturas por serial, `bridge.py` las guarda en Firebase Realtime Database, Flask las expone y Botánico AI genera recomendaciones.

## Arquitectura

`Micro:bit → bridge.py → Firebase /sensors → Flask → OpenAI → UI web`

La interfaz principal está en `templates/index.html` y se sirve desde el mismo backend.

## Ejecución local

```bash
pip install -r requirements.txt
python main.py
```

En otra terminal, con el Micro:bit conectado:

```bash
python bridge.py
```

Variables disponibles:

- `FIREBASE_SERVICE_ACCOUNT_JSON`: JSON completo de la cuenta de servicio para Flask/Render.
- `FIREBASE_SERVICE_ACCOUNT_FILE`: ruta local al JSON para `bridge.py`.
- `FIREBASE_DB_URL`: URL de Firebase Realtime Database.
- `OPENAI_API_KEY`: opcional; sin ella se usa un consejo local por reglas.
- `OPENAI_MODEL`: opcional, por defecto `gpt-4o-mini`.
- `SERIAL_PORT`: puerto del Micro:bit, por defecto `COM3`.

## Formato del Micro:bit

Cada línea serial debe tener exactamente `humedad,temperatura,luz`, por ejemplo:

```text
512,24,140
```

Firebase guarda:

```json
{"humidity":512,"temperature":24,"light":140,"updated_at":"2026-09-08T12:00:00+00:00"}
```

## Endpoints

- `/`: dashboard web.
- `/health`: estado de Firebase y OpenAI.
- `/api/sensors`: datos actuales para la UI.
- `/analizar`: datos y consejo del Botánico AI.

Si OpenAI no está configurado o falla, `/analizar` devuelve un consejo local basado en umbrales.

## Render

Usa `gunicorn main:app` como comando de inicio y configura `FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_DB_URL` y, si se desea IA generativa, `OPENAI_API_KEY`. Nunca subas credenciales al repositorio.
