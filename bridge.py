import serial
import firebase_admin
from firebase_admin import credentials, db
import time

# ==============================================================================
# CONFIGURACIÓN DEL SISTEMA
# ==============================================================================
# El archivo JSON es la 'llave' que permite que Python escriba en tu Firebase.
# Lo descargas desde: Proyecto -> Configuración -> Cuentas de Servicio
SERVICE_ACCOUNT_KEY = "servicio-firebase.json" 
DATABASE_URL = "https://tu-proyecto-default-rtdb.firebaseio.com/"

# Puerto COM: Verifica en el Administrador de Dispositivos de Windows cuál es el de tu Micro:bit.
SERIAL_PORT = 'COM3'  
BAUD_RATE = 115200 # Velocidad de comunicación estándar para Micro:bit

try:
    # --- PASO 1: CONEXIÓN A LA NUBE ---
    # Cargamos las credenciales y abrimos el canal con Firebase
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    print("? Conexión exitosa con Firebase. La nube está lista.")

    # --- PASO 2: CONEXIÓN AL HARDWARE ---
    # Abrimos la comunicación serial con el cable USB
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"? Micro:bit detectado en {SERIAL_PORT}. Escuchando sensores...")

    # --- PASO 3: BUCLE DE DATOS (Main Loop) ---
    while True:
        # Leemos una línea de texto del puerto USB
        line = ser.readline().decode('utf-8').strip()
        
        if line:
            # El Micro:bit debe enviar los datos así: "humedad,temp,luz" (separados por coma)
            print(f"Dato bruto recibido: {line}")
            parts = line.split(',')
            
            if len(parts) == 3:
                # Convertimos los textos a números enteros
                data = {
                    'humidity': int(parts[0]),
                    'temp': int(parts[1]),
                    'light': int(parts[2])
                }
                # Subimos los datos a la ruta 'sensors' en Firebase
                # .set() reemplaza el valor anterior por el nuevo
                db.reference('sensors').set(data)
                print(f"?? Sincronizado en la nube: {data}")
            else:
                print("?? Formato de dato incorrecto. Se esperaba: valor,valor,valor")
        
        # Pequeña pausa para no saturar el procesador
        time.sleep(1)

except Exception as e:
    print(f"? Ocurrió un error crítico: {e}")
    print("Sugerencia: Verifica que el Micro:bit esté conectado y que el archivo .json esté en la carpeta.")
