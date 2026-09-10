"""
GAIrden - Emulador de Sensores Micro:bit (Ultra-ligero, 0 VRAM)
Simula el comportamiento de un Micro:bit con sensores de humedad, temperatura y luz.
Envía lecturas periódicas al endpoint /api/sensors de Flask o directamente a Firebase.
"""

import math
import os
import random
import time
import requests

API_URL = os.getenv("API_URL", "http://localhost:5000/api/sensors")
INGEST_TOKEN = os.getenv("DEVICE_INGEST_TOKEN", "")
INTERVAL_SECONDS = float(os.getenv("EMU_INTERVAL", "3.0"))


def generate_reading(tick: int):
    # Simulamos ciclo diario y variaciones naturales
    t = tick * 0.1
    # Humedad de suelo (0 - 1023): decae lentamente con ruido aleatorio
    base_hum = 550 + 80 * math.sin(t * 0.05) + random.uniform(-5, 5)
    humidity = max(0, min(1023, int(base_hum)))

    # Temperatura ambiente (grados C): ciclo suave entre 20°C y 28°C
    base_temp = 24.0 + 4.0 * math.sin(t * 0.1) + random.uniform(-0.5, 0.5)
    temperature = round(base_temp, 1)

    # Luz (0 - 255): ciclo entre sombra y luz
    base_light = 140 + 80 * math.cos(t * 0.08) + random.uniform(-8, 8)
    light = max(0, min(255, int(base_light)))

    return {"humidity": humidity, "temperature": temperature, "light": light}


def main():
    headers = {"Content-Type": "application/json"}
    if INGEST_TOKEN:
        headers["X-Device-Token"] = INGEST_TOKEN

    print("=" * 60)
    print("GAIrden - Emulador Micro:bit iniciado")
    print(f"Destino: {API_URL}")
    print(f"Intervalo: {INTERVAL_SECONDS}s")
    print("Presiona Ctrl+C para detener.")
    print("=" * 60)

    tick = 0
    while True:
        tick += 1
        data = generate_reading(tick)
        try:
            resp = requests.post(API_URL, json=data, headers=headers, timeout=5)
            if resp.status_code == 200:
                print(
                    f"[{time.strftime('%H:%M:%S')}] OK -> Humedad: {data['humidity']} | Temp: {data['temperature']} C | Luz: {data['light']}"
                )
            else:
                print(
                    f"[{time.strftime('%H:%M:%S')}] Servidor respondio HTTP {resp.status_code}: {resp.text}"
                )
        except requests.exceptions.ConnectionError:
            print(
                f"[{time.strftime('%H:%M:%S')}] Conexion rechazada. Inicia el backend con 'python main.py'"
            )
        except Exception as err:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {err}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
