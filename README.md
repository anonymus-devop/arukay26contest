# GAIrden

MVP de jardín inteligente: un Micro:bit envía lecturas por serial, `bridge.py` las guarda en Firebase Realtime Database, Flask las expone y GAIrden AI genera recomendaciones.

## Arquitectura

`Micro:bit → bridge.py → Firebase /sensors → Flask → GAIrden AI → UI web`

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
- `GEMINI_API_KEY`: opcional; permite usar Gemini como proveedor predeterminado cuando no hay clave de OpenAI.
- `OPENAI_MODEL`: opcional, por defecto `gpt-4o-mini`.
- `GEMINI_MODEL`: opcional, por defecto `gemini-2.0-flash`.
- `DEVICE_INGEST_TOKEN`: requerido para Web Serial; token compartido entre el dashboard y el dispositivo.
- `SERIAL_PORT`: puerto del Micro:bit, por defecto `COM3`.
- `FLASK_SECRET_KEY`: secreto para firmar la sesión web.
- `CS_ID_CLIENT_ID`: client ID de Coki Studios ID.
- `CS_ID_CLIENT_SECRET`: opcional; solo para clientes OAuth confidenciales.
- `CS_ID_REDIRECT_URI`: URL exacta de callback, por ejemplo `https://arukay26contest.onrender.com/callback`.

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
- `/analizar`: datos y consejo de GAIrden AI.
- `/login`: inicio de sesión oficial con Coki Studios ID.
- `/callback`: callback OAuth 2.1/OIDC.
- `/auth/status`: estado de sesión actual.

Si OpenAI no está configurado o falla, `/analizar` devuelve un consejo local basado en umbrales.

En el dashboard el usuario puede seleccionar ChatGPT/OpenAI o Google Gemini y pegar una API key para esa solicitud. La clave se envía en un header HTTPS, no se guarda en Firebase, no se escribe en logs y no se persiste en el servidor.

El dashboard también ofrece Web Serial. En Chrome o Edge de escritorio pulsa “Conectar Micro:bit”, selecciona el puerto USB e introduce el mismo `DEVICE_INGEST_TOKEN` configurado en Render. `bridge.py` permanece disponible para ejecución automática/local.

Para visitantes sin hardware hay un mini simulador de Micro:bit en la página. Sus lecturas se envían a `/analizar` solo para probar la interfaz y el consejo AI; no modifican Firebase.

## Render

Usa `gunicorn main:app` como comando de inicio y configura `FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_DB_URL`, `FLASK_SECRET_KEY`, `CS_ID_CLIENT_ID` y `CS_ID_REDIRECT_URI`. `CS_ID_CLIENT_SECRET` solo es necesario para clientes confidenciales. `OPENAI_API_KEY` y `GEMINI_API_KEY` son opcionales. Nunca subas credenciales al repositorio.
