import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from openai import OpenAI

app = Flask(__name__)
CORS(app)

FIREBASE_DB_URL = 'https://arukaycontest26-default-rtdb.firebaseio.com'

def init_firebase():
    try:
        # Verificar si ya hay una app inicializada
        if not firebase_admin._apps:
            print('Intentando inicializar Firebase...')
            service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                print('❌ Error: FIREBASE_SERVICE_ACCOUNT_JSON no configurada')
                return False
            
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
            print('✅ Firebase inicializado correctamente')
            return True
        else:
            print('✅ Firebase ya estaba inicializado')
            return True
    except Exception as e:
        print(f'❌ ERROR CRÍTICO al inicializar Firebase: {e}')
        return False

# Inicializar al arrancar
firebase_initialized = init_firebase()

# Cliente de OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/health', methods=['GET'])
def health():
    status = 'online' if firebase_initialized else 'firebase_error'
    return jsonify({
        'status': status, 
        'message': 'Botánico AI activo' if firebase_initialized else 'Error de Firebase',
        'firebase_initialized': firebase_initialized
    }), 200

@app.route('/analizar', methods=['GET'])
def analizar_huerto():
    try:
        # Intentar inicializar si falló al inicio o no existe
        if not firebase_admin._apps:
            if not init_firebase():
                return jsonify({'error': 'Firebase no está inicializado. Revisa los logs del servidor.'}), 500

        # Referencia a la base de datos en tiempo real
        ref = db.reference('/sensors')
        sensor_data = ref.get()
        
        if not sensor_data:
            return jsonify({'error': 'No hay datos de sensores disponibles en Firebase'}), 404

        # Extraer datos con valores por defecto
        humedad = sensor_data.get('humidity', 'N/A')
        temperatura = sensor_data.get('temperature', 'N/A')
        luz = sensor_data.get('light', 'N/A')

        # Prompt para la IA
        prompt = (
            f'Eres un experto botánico y asistente de jardinería muy amable. '
            f'Analiza los siguientes datos de sensores de un huerto inteligente:\n'
            f'- Humedad del suelo: {humedad}%\n'
            f'- Temperatura: {temperatura}°C\n'
            f'- Luz: {luz} lux\n\n'
            f'Dime de forma breve, humana y cercana si el huerto está OK o si el usuario debe hacer algo '
            f'(como regar o mover la planta al sol). No uses lenguaje técnico aburrido.'
        )

        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7
        )
        
        consejo = response.choices[0].message.content
        return jsonify({
            'status': 'success', 
            'data': sensor_data, 
            'consejo': consejo
        })
        
    except Exception as e:
        print(f'Error en el análisis: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
