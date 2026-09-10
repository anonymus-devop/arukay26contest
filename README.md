# GAIrden

GAIrden es un huerto inteligente que combina Micro:bit, sensores, Firebase, Flask e inteligencia artificial. Puede funcionar como dashboard web, aplicación Android/React Native y escena preparada para Meta Spatial Editor.

## Qué incluye

- Dashboard web responsive servido por Flask.
- Lecturas de humedad, temperatura y luz.
- Firebase Realtime Database en la ruta `/sensors`.
- Análisis con OpenAI o Gemini.
- Consejo local por reglas cuando no hay IA externa.
- Chat de voz Live con OpenAI Realtime o Gemini Live.
- Conexión de Micro:bit mediante Web Serial en Chrome/Edge.
- Alternativa mediante `bridge.py` y USB serial.
- Simulador para probar sin hardware.
- App React Native/Expo para Android.
- Escena base para Meta Spatial Editor y futura experiencia XR.

## Arquitectura

```text
Micro:bit + sensores
        │ USB serial
        ├── bridge.py ──► Firebase Realtime Database (/sensors)
        │
        └── Web Serial desde el navegador ──► Flask (/api/sensors)

Firebase ──► Flask ──► OpenAI/Gemini ──► consejo y voz Live
```

| Archivo o carpeta | Función |
|---|---|
| `main.py` | Backend Flask, Firebase, análisis y sesiones Live |
| `bridge.py` | Lee el puerto serial y escribe en Firebase |
| `templates/index.html` | Dashboard web |
| `App.js` | Cliente React Native/Expo |
| `microbit_code.txt` | Código de referencia del Micro:bit |
| `XR_META/` | Proyecto y script de Meta Spatial Editor |
| `requirements.txt` | Dependencias Python |
| `package.json` | Dependencias Expo/React Native |
| `SETUP.md` | Configuración rápida adicional |

## Requisitos

- Python 3.10 o superior.
- Node.js LTS y npm para la app móvil.
- Firebase Realtime Database.
- Una cuenta de OpenAI y/o Gemini si se quiere IA externa.
- Micro:bit y sensores para las pruebas físicas.
- Chrome o Edge de escritorio para Web Serial y Live.
- Meta Spatial Editor v16 para la parte XR.

## Instalación local

Desde la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
```

Comprueba la sintaxis Python:

```powershell
python -m py_compile main.py bridge.py
```

## Variables de entorno

No subas claves, contraseñas ni el JSON de Firebase al repositorio.

### Backend Flask

| Variable | Obligatoria | Uso |
|---|---:|---|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Para Firebase en Render | JSON completo de la cuenta de servicio |
| `FIREBASE_DB_URL` | Para Firebase | URL de Realtime Database |
| `OPENAI_API_KEY` | No | Análisis OpenAI y OpenAI Realtime global |
| `GEMINI_API_KEY` | No | Análisis Gemini y Gemini Live global |
| `OPENAI_MODEL` | No | Por defecto `gpt-4o-mini` |
| `OPENAI_REALTIME_MODEL` | No | Por defecto `gpt-realtime` |
| `GEMINI_MODEL` | No | Por defecto `gemini-2.0-flash` |
| `GEMINI_LIVE_MODEL` | No | Modelo usado por Gemini Live |
| `DEVICE_INGEST_TOKEN` | Recomendado | Protege el envío de lecturas |

### `bridge.py`

| Variable | Valor por defecto | Uso |
|---|---|---|
| `FIREBASE_SERVICE_ACCOUNT_FILE` | `serviceAccountKey.json` | Ruta local al JSON de Firebase |
| `FIREBASE_DB_URL` | Configurable | URL de Realtime Database |
| `SERIAL_PORT` | `COM3` | Puerto del Micro:bit |
| `SERIAL_BAUDRATE` | `115200` | Velocidad serial |

Ejemplo temporal en PowerShell:

```powershell
$env:FIREBASE_SERVICE_ACCOUNT_FILE = "C:\ruta\serviceAccountKey.json"
$env:FIREBASE_DB_URL = "https://TU-PROYECTO-default-rtdb.firebaseio.com"
$env:SERIAL_PORT = "COM3"
$env:DEVICE_INGEST_TOKEN = "un-token-local"
```

## Configurar Firebase

1. Crea o abre un proyecto en Firebase.
2. Activa Realtime Database.
3. Crea una cuenta de servicio en la configuración del proyecto.
4. Descarga el JSON solo para tu equipo local.
5. Usa `FIREBASE_SERVICE_ACCOUNT_FILE` para `bridge.py`.
6. En Render copia el JSON completo en `FIREBASE_SERVICE_ACCOUNT_JSON`.
7. Configura `FIREBASE_DB_URL` con la URL exacta de la base.

El formato oficial en `/sensors` es:

```json
{
  "humidity": 512,
  "temperature": 24,
  "light": 140,
  "updated_at": "2026-09-08T12:00:00+00:00"
}
```

Se acepta temporalmente la clave antigua `temp` al leer datos existentes.

## Ejecutar el backend local

Terminal 1:

```powershell
python main.py
```

Abre:

- [http://localhost:5000/](http://localhost:5000/) — dashboard.
- [http://localhost:5000/health](http://localhost:5000/health) — estado.
- [http://localhost:5000/api/sensors](http://localhost:5000/api/sensors) — lectura actual.
- [http://localhost:5000/analizar](http://localhost:5000/analizar) — análisis.

No abras `templates/index.html` directamente con doble clic. Si se abre como `file://`, el navegador bloqueará las peticiones `/api/...` por CORS. Usa Flask o la URL HTTPS de Render.

## Conectar el Micro:bit

### Opción A: Web Serial

1. Ejecuta Flask o abre el dominio HTTPS de Render.
2. Usa Chrome o Edge en un computador de escritorio.
3. Conecta el Micro:bit por USB.
4. Pulsa `Conectar Micro:bit`.
5. Introduce el mismo `DEVICE_INGEST_TOKEN` del backend.
6. Selecciona el puerto USB.

Web Serial necesita HTTPS, salvo `localhost`, y permiso del navegador.

### Opción B: `bridge.py`

Esta opción sirve cuando la web está desplegada y el Micro:bit está conectado al computador local:

```powershell
python bridge.py
```

`bridge.py` no se ejecuta automáticamente en Render: Render es remoto y no puede acceder al USB de tu computador.

El formato serial oficial es:

```text
humedad,temperatura,luz
```

Ejemplo:

```text
512,24,140
```

Las líneas incompletas o no numéricas se rechazan sin detener el puente.

## Probar sin Micro:bit

En el dashboard usa:

```text
512,24,140
```

o:

```json
{"humidity":512,"temperature":24,"light":140}
```

El simulador mini de Micro:bit prueba la interfaz y el consejo, pero no representa una lectura física real.

## IA, API keys y Live

El usuario puede seleccionar OpenAI o Gemini y pegar su propia API key. La clave se envía por HTTPS para esa solicitud y no se guarda en Firebase ni en el servidor.

- OpenAI usa el header `X-OpenAI-Key`.
- Gemini usa el header `X-Gemini-Key`.
- Sin clave del usuario se usa la clave global del servidor, si existe.
- Sin ninguna clave se utiliza el consejo local por reglas.

El botón `Hablar con la IA` necesita HTTPS, navegador actualizado y permiso de micrófono. OpenAI Live usa WebRTC; Gemini Live usa WebSocket.

Si aparece `Unsupported content type ... application/sdp`, el backend debe enviar el SDP de OpenAI como texto con `Content-Type: application/sdp`, no como JSON.

## Endpoints

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/` | Dashboard web |
| `GET` | `/health` | Estado de Firebase y proveedores IA |
| `GET` | `/api/sensors` | Lee sensores actuales |
| `POST` | `/api/sensors` | Guarda una lectura protegida por token |
| `GET/POST` | `/analizar` | Genera consejo |
| `POST` | `/api/live/openai-call` | Crea sesión OpenAI Realtime |
| `POST` | `/api/live/gemini-token` | Crea token temporal Gemini Live |

## Desplegar en Render

1. Sube el repositorio a GitHub sin credenciales.
2. Crea en Render un `Web Service` conectado al repositorio.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn main:app`.
5. Añade `FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_DB_URL` y `DEVICE_INGEST_TOKEN`.
6. Añade `OPENAI_API_KEY` y/o `GEMINI_API_KEY` si quieres IA global.
7. Despliega y verifica `/`, `/health` y `/api/sensors`.

La web pública puede usarla el navegador y la app móvil. El Micro:bit debe seguir conectado al computador local que ejecuta `bridge.py` o Web Serial.

## App React Native / Expo

La app móvil actual es una experiencia Android 2D con sensores, simulador, tema oscuro, proveedor IA y campo de API key.

```powershell
npx expo start
```

Para Android local:

```powershell
npx expo run:android
```

Para cambiar el backend:

```powershell
$env:EXPO_PUBLIC_API_URL = "https://TU-SERVICIO.onrender.com"
npx expo start
```

Web Serial no es una API nativa universal de Android. Para conectar directamente una Micro:bit desde Android XR/Horizon OS se necesita un módulo Android USB/Bluetooth específico.

## Meta Spatial Editor / XR

El proyecto XR está en `XR_META/gAIrden`. La escena base contiene suelo, bancales, plantas y paneles preparados para humedad, temperatura, luz y consejo.

### Abrir y conectar

1. Abre Meta Spatial Editor v16.
2. Abre `XR_META/gAIrden`.
3. Deja activo el editor.
4. En una PowerShell del mismo usuario, ejecuta:

```powershell
cd "C:\Program Files\Meta Spatial Editor\v16\Resources"
.\mse-agent.exe ping
```

Debe responder `pong`.

### Crear o actualizar la escena

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\canin\AntiGravedad\Innova\Arukay 26\PyAI\HuertoApp\XR_META\create_gairden_scene.ps1"
```

El script busca objetos por nombre para evitar duplicados, aplica escala/color y guarda la escena.

### Verificar y capturar

```powershell
.\mse-agent.exe list-objects
.\mse-agent.exe get-camera
.\mse-agent.exe screenshot --output "C:\Users\canin\AntiGravedad\Innova\Arukay 26\PyAI\HuertoApp\XR_META\preview.png"
```

La captura se guarda en `XR_META/preview.png`.

El agente depende de la sesión de usuario del editor. Si se ejecuta desde otra cuenta, servicio o terminal aislada puede fallar aunque el editor esté abierto. La escena actual es una base visual; todavía falta conectar sus paneles a sensores en tiempo real y empaquetar una experiencia inmersiva para un visor compatible.

## Comprobaciones rápidas

```powershell
python -m py_compile main.py bridge.py
git status
```

Prueba manual mínima:

1. `python main.py` inicia sin error.
2. `/health` devuelve JSON.
3. `/api/sensors` maneja correctamente la ausencia de Firebase.
4. El simulador genera un consejo.
5. `512,24,140` aparece en el dashboard.
6. Una línea serial inválida no detiene `bridge.py`.
7. La app abre con `npx expo start`.
8. Meta Spatial Editor responde `pong` y genera `preview.png`.

## Solución de problemas

### `localhost rechazó la conexión`

Ejecuta `python main.py` y abre el puerto 5000.

### Error CORS con `file:///.../index.html`

No abras el HTML como archivo local. Usa `http://localhost:5000/` o Render.

### No hay lecturas

Revisa `FIREBASE_DB_URL`, credenciales, la ruta `/sensors`, el token y `SERIAL_PORT`.

### Error de API key

Comprueba que la clave corresponda al proveedor seleccionado y que Render tenga la versión más reciente. Sin claves, debe funcionar el consejo local.

### El editor XR no responde

Abre el proyecto, deja el editor activo y ejecuta `mse-agent.exe ping` desde la PowerShell del mismo usuario.

## Seguridad

- No subas `serviceAccountKey.json`, `.env` ni API keys.
- No pongas claves dentro de `App.js` o `templates/index.html`.
- Usa HTTPS en Render.
- Mantén `DEVICE_INGEST_TOKEN` secreto.
- No guardes las API keys de usuarios en logs, Firebase, commits ni capturas.
- Rota cualquier token que haya quedado expuesto en una URL de Git remoto.

## Estado y próximos pasos

El MVP web, simulador, puente serial, análisis IA, app Android 2D y escena XR base están preparados. Pasos recomendados:

1. Conectar un Micro:bit real y calibrar umbrales.
2. Validar Firebase y Render con datos reales.
3. Añadir historial y gráficas.
4. Sustituir placeholders XR por modelos y paneles interactivos.
5. Conectar paneles XR a `/api/sensors`.
6. Implementar USB/Bluetooth nativo para Android XR si se necesita conexión directa.
7. Empaquetar y probar en un visor Meta compatible.
