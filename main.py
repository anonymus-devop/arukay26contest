import json
import os
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL", "https://arukaycontest26-default-rtdb.firebaseio.com"
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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


def generate_advice(sensor_data):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return rule_based_advice(sensor_data), "rules", "OPENAI_API_KEY no configurada"
    try:
        client = OpenAI(api_key=api_key)
        prompt = (
            "Eres el Botánico AI de un huerto escolar. Da un consejo breve, cálido y accionable "
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
        advice = response.choices[0].message.content
        if advice:
            return advice.strip(), "openai", None
    except Exception as error:
        print(f"OpenAI no disponible; se usará consejo local: {error}")
        return rule_based_advice(sensor_data), "rules", "OpenAI no disponible"
    return rule_based_advice(sensor_data), "rules", "OpenAI no devolvió contenido"


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    firebase_ok = init_firebase()
    return jsonify({
        "status": "online" if firebase_ok else "degraded",
        "message": "Botánico AI activo" if firebase_ok else "Firebase requiere configuración",
        "firebase_initialized": firebase_ok,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }), 200


@app.route("/api/sensors", methods=["GET"])
def sensors():
    sensor_data, error = read_sensors()
    if sensor_data is None:
        return jsonify({"status": "no_data", "data": None, "error": error}), 200
    return jsonify({"status": "success", "data": sensor_data}), 200


@app.route("/analizar", methods=["GET"])
def analizar_huerto():
    sensor_data, error = read_sensors()
    if sensor_data is None:
        status_code = 503 if error == "firebase_unavailable" else 404
        return jsonify({"status": "no_data", "error": error}), status_code
    advice, source, warning = generate_advice(sensor_data)
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
