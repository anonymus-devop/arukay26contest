import os
import time
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, db
import serial

SERVICE_ACCOUNT_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "servicio-firebase.json")
DATABASE_URL = os.getenv(
    "FIREBASE_DB_URL", "https://arukaycontest26-default-rtdb.firebaseio.com"
)
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
BAUD_RATE = int(os.getenv("SERIAL_BAUD_RATE", "115200"))
READ_INTERVAL_SECONDS = float(os.getenv("READ_INTERVAL_SECONDS", "1"))


def initialize_firebase():
    if firebase_admin._apps:
        return
    credential = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(credential, {"databaseURL": DATABASE_URL})


def parse_sensor_line(line):
    """Parse Micro:bit CSV: humidity,temperature,light."""
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 3:
        raise ValueError("se esperaban tres valores: humedad,temperatura,luz")
    values = [float(part) for part in parts]
    if any(not (-float("inf") < value < float("inf")) for value in values):
        raise ValueError("los valores deben ser finitos")
    normalized = [int(value) if value.is_integer() else value for value in values]
    return {
        "humidity": normalized[0],
        "temperature": normalized[1],
        "light": normalized[2],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_bridge():
    initialize_firebase()
    print(f"Firebase conectado. Escuchando Micro:bit en {SERIAL_PORT}...")
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as connection:
        while True:
            raw_line = connection.readline().decode("utf-8", errors="replace").strip()
            if not raw_line:
                time.sleep(READ_INTERVAL_SECONDS)
                continue
            try:
                sensor_data = parse_sensor_line(raw_line)
                db.reference("/sensors").set(sensor_data)
                print(f"Sensores sincronizados: {sensor_data}")
            except (ValueError, TypeError) as error:
                print(f"Línea ignorada ({raw_line!r}): {error}")
            except Exception as error:
                print(f"Error guardando sensores; se continúa escuchando: {error}")
            time.sleep(READ_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        run_bridge()
    except KeyboardInterrupt:
        print("Puente detenido por el usuario.")
    except Exception as error:
        print(f"No se pudo iniciar el puente: {error}")
