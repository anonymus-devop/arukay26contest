import json
import os
import hmac
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL", "https://arukaycontest26-default-rtdb.firebaseio.com"
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime")
GEMINI_LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview")
firebase_initialized = False


def init_firebase():
    global firebase_initialized
    if firebase_admin._apps:
        firebase_initialized = True
        return True
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("Firebase no inicializado: falta FIREBASE_SERVICE_ACCOUNT_JSON")
        firebase_initialized = False
        return False
    try:
        credentials_dict = json.loads(service_account_json)
        credential = credentials.Certificate(credentials_dict)
        firebase_admin.initialize_app(credential, {"databaseURL": FIREBASE_DB_URL})
        firebase_initialized = True
        print("Firebase inicializado correctamente")
        return True
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        firebase_initialized = False
        print(f"Firebase: credenciales JSON inválidas: {error}")
    except Exception as error:
        firebase_initialized = False
        print(f"Firebase: no se pudo inicializar: {error}")
    return False


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def numeric_value(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def normalize_sensor_data(sensor_data):
    """Normalize current and legacy Firebase sensor keys."""
    if not isinstance(sensor_data, dict):
        return None
    humidity = numeric_value(sensor_data.get("humidity"))
    temperature = numeric_value(
        sensor_data.get("temperature", sensor_data.get("temp"))
    )
    light = numeric_value(sensor_data.get("light"))
    if humidity is None or temperature is None or light is None:
        return None
    return {
        "humidity": humidity,
        "temperature": temperature,
        "light": light,
        "updated_at": sensor_data.get("updated_at") or utc_now(),
    }


def read_sensors():
    if not init_firebase():
        return None, "firebase_unavailable"
    try:
        raw_data = db.reference("/sensors").get()
    except Exception as error:
        print(f"Firebase: error leyendo sensores: {error}")
        return None, "firebase_read_error"
    normalized = normalize_sensor_data(raw_data)
    if normalized is None:
        return None, "no_data"
    return normalized, None


def rule_based_advice(sensor_data):
    humidity = sensor_data["humidity"]
    temperature = sensor_data["temperature"]
    light = sensor_data["light"]
    actions = []
    # Humedad is the Micro:bit analog soil-probe reading (0-1023).
    if humidity < 350:
        actions.append("revisa la tierra y considera regar")
    elif humidity > 850:
        actions.append("revisa que la tierra no esté demasiado húmeda")
    if temperature < 12:
        actions.append("protege la planta del frío")
    elif temperature > 32:
        actions.append("busca un poco de sombra y ventilación")
    if light < 80:
        actions.append("acerca la planta a un lugar con más luz")
    elif light > 240:
        actions.append("vigila el calor si recibe sol directo")
    if not actions:
        return "Tu huerto se ve equilibrado. Mantén la rutina y observa las plantas cada día."
    return "Te recomiendo " + " y ".join(actions) + "."


def openai_advice(sensor_data, api_key):
    client = OpenAI(api_key=api_key)
    prompt = (
        "Eres GAIrden AI, el asistente de un huerto escolar. Da un consejo breve, cálido y accionable "
        "en español, sin tecnicismos. La humedad es una lectura analógica Micro:bit (0-1023), "
        "la temperatura está en °C y la luz es el nivel del Micro:bit.\n\n"
        f"Humedad: {sensor_data['humidity']}\n"
        f"Temperatura: {sensor_data['temperature']} °C\n"
        f"Luz: {sensor_data['light']}\n"
    )
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=120,
    )
    return response.choices[0].message.content


def gemini_advice(sensor_data, api_key):
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    prompt = (
        "Eres GAIrden AI, el asistente de un huerto escolar. Da un consejo breve, cálido y accionable "
        "en español, sin tecnicismos. La humedad es una lectura analógica Micro:bit (0-1023), "
        "la temperatura está en °C y la luz es el nivel del Micro:bit.\n\n"
        f"Humedad: {sensor_data['humidity']}\n"
        f"Temperatura: {sensor_data['temperature']} °C\n"
        f"Luz: {sensor_data['light']}\n"
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={urllib.parse.quote(api_key)}"
    )
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"]


def live_system_instruction():
    return (
        "Eres GAIrden AI, un asistente de huerto escolar. Responde en español, de forma breve, "
        "cálida y accionable. La humedad es una lectura analógica Micro:bit de 0 a 1023; "
        "la temperatura está en grados Celsius y la luz es el nivel del sensor Micro:bit."
    )


def openai_live_call(sdp, api_key=None):
    """Relay the WebRTC SDP offer to OpenAI without exposing the server API key."""
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurada")
    req = urllib.request.Request(
        "https://api.openai.com/v1/realtime/calls",
        data=sdp.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/sdp",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        answer = response.read().decode("utf-8")
    return answer


def gemini_live_token(api_key=None):
    """Mint a short-lived Gemini Live token for the browser WebSocket."""
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no está configurada")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        "uses": 1,
        "expireTime": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "newSessionExpireTime": (now + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "liveConnectConstraints": {
            "model": f"models/{GEMINI_LIVE_MODEL}",
            "config": {
                "responseModalities": ["TEXT"],
                "systemInstruction": {"parts": [{"text": live_system_instruction()}]},
            },
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1alpha/auth_tokens",
        data=body,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    token = result.get("name")
    if not token:
        raise ValueError("Gemini no devolvió un token efímero")
    return token


def upstream_error_detail(error):
    try:
        detail = error.read().decode("utf-8", errors="replace")
    except Exception:
        detail = str(error)
    return detail[:800]


def generate_advice(sensor_data, provider=None, user_api_key=None):
    provider = (provider or "").lower().strip()
    if provider not in {"openai", "gemini"}:
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "gemini"

    api_key = user_api_key or (
        os.getenv("OPENAI_API_KEY") if provider == "openai" else os.getenv("GEMINI_API_KEY")
    )
    if not api_key:
        return rule_based_advice(sensor_data), "rules", f"No hay clave configurada para {provider}"

    try:
        advice = openai_advice(sensor_data, api_key) if provider == "openai" else gemini_advice(sensor_data, api_key)
        if advice:
            return advice.strip(), provider, None
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, ValueError) as error:
        print(f"{provider} no disponible; se usará consejo local: {error}")
        return rule_based_advice(sensor_data), "rules", f"{provider} no disponible"
    except Exception as error:
        print(f"{provider} no disponible; se usará consejo local: {error}")
        return rule_based_advice(sensor_data), "rules", f"{provider} no disponible"
    return rule_based_advice(sensor_data), "rules", f"{provider} no devolvió contenido"


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    firebase_ok = init_firebase()
    return jsonify({
        "status": "online" if firebase_ok else "degraded",
        "message": "GAIrden AI activo" if firebase_ok else "Firebase requiere configuración",
        "firebase_initialized": firebase_ok,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "openai_realtime_configured": bool(os.getenv("OPENAI_API_KEY")),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "gemini_live_configured": bool(os.getenv("GEMINI_API_KEY")),
    }), 200


@app.route("/api/live/openai-call", methods=["POST"])
def live_openai_call():
    payload = request.get_json(silent=True) or {}
    sdp = payload.get("sdp")
    if not isinstance(sdp, str) or not sdp.strip():
        return jsonify({"error": "missing_sdp"}), 400
    try:
        answer_sdp = openai_live_call(sdp, request.headers.get("X-OpenAI-Key"))
    except urllib.error.HTTPError as error:
        detail = upstream_error_detail(error)
        print(f"OpenAI Live HTTP {error.code}: {detail}")
        return jsonify({"error": "openai_live_unavailable", "detail": detail}), 503
    except (urllib.error.URLError, RuntimeError, ValueError) as error:
        print(f"OpenAI Live: {error}")
        return jsonify({"error": "openai_live_unavailable", "detail": str(error)}), 503
    return jsonify({"sdp": answer_sdp, "model": OPENAI_REALTIME_MODEL}), 200


@app.route("/api/live/gemini-token", methods=["POST"])
def live_gemini_token():
    try:
        token = gemini_live_token(request.headers.get("X-Gemini-Key"))
    except urllib.error.HTTPError as error:
        detail = upstream_error_detail(error)
        print(f"Gemini Live HTTP {error.code}: {detail}")
        return jsonify({"error": "gemini_live_unavailable", "detail": detail}), 503
    except (urllib.error.URLError, RuntimeError, ValueError) as error:
        print(f"Gemini Live: {error}")
        return jsonify({"error": "gemini_live_unavailable", "detail": str(error)}), 503
    return jsonify({"token": token, "model": GEMINI_LIVE_MODEL}), 200


@app.route("/api/sensors", methods=["GET"])
def sensors():
    sensor_data, error = read_sensors()
    if sensor_data is None:
        return jsonify({"status": "no_data", "data": None, "error": error}), 200
    return jsonify({"status": "success", "data": sensor_data}), 200


@app.route("/api/sensors", methods=["POST"])
def receive_sensors():
    configured_token = os.getenv("DEVICE_INGEST_TOKEN")
    supplied_token = request.headers.get("X-Device-Token", "")
    if not configured_token or not hmac.compare_digest(supplied_token, configured_token):
        return jsonify({"status": "error", "error": "device_unauthorized"}), 401

    sensor_data = normalize_sensor_data(request.get_json(silent=True))
    if sensor_data is None:
        return jsonify({"status": "error", "error": "invalid_sensor_data"}), 400
    if not init_firebase():
        return jsonify({"status": "error", "error": "firebase_unavailable"}), 503
    try:
        db.reference("/sensors").set(sensor_data)
    except Exception as error:
        print(f"Firebase: error guardando sensores Web Serial: {error}")
        return jsonify({"status": "error", "error": "firebase_write_error"}), 503
    return jsonify({"status": "success", "data": sensor_data}), 201


@app.route("/analizar", methods=["GET", "POST"])
def analizar_huerto():
    if request.method == "POST":
        sensor_data = normalize_sensor_data(request.get_json(silent=True))
        error = None if sensor_data else "invalid_sensor_data"
    else:
        sensor_data, error = read_sensors()
    if sensor_data is None:
        status_code = 400 if error == "invalid_sensor_data" else (503 if error == "firebase_unavailable" else 404)
        return jsonify({"status": "no_data", "error": error}), status_code
    provider = request.headers.get("X-AI-Provider") or request.args.get("provider")
    if (provider or "").lower() == "gemini":
        user_api_key = request.headers.get("X-Gemini-Key")
    else:
        user_api_key = request.headers.get("X-OpenAI-Key")
    advice, source, warning = generate_advice(sensor_data, provider, user_api_key)
    response = {
        "status": "success",
        "data": sensor_data,
        "consejo": advice,
        "source": source,
    }
    if warning:
        response["warning"] = warning
    return jsonify(response), 200


init_firebase()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
