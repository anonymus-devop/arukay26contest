import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from openai import OpenAI

app = Flask(__name__)
CORS(app)

FIREBASE_DB_URL = 'https://arukaycontest26-default-rtdb.firebaseio.com'

try:
    if not firebase_admin._app:
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        if service_account_json:
            import json
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
                temp.write(service_account_json)
                temp_path = temp.name
            cred = credentials.Certificate(temp_path)
        else:
            cred = None
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
except Exception as e:
    print(f'Error inicializando Firebase: {e}')

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/analizar', methods=['GET'])
def analizar_huerto():
    try:
        ref = db.reference('/sensors')
        sensor_data = ref.get()
        if not sensor_data:
            return jsonify({'error': 'No hay datos de sensores disponibles en Firebase'}), 404
        prompt = (
            f'Eres un experto botánico y asistente de jardinería muy amable. '
            f'Analiza los siguientes datos de sensores de un huerto inteligente:\n'
            f'- Humedad del suelo: {sensor_data.get(\'humidity\', \'N/A\')}%\n'
            f'- Temperatura: {sensor_data.get(\'temperature\', \'N/A\')}°C\n'
            f'- Luz: {sensor_data.get(\'light\', \'N/A\')} lux\n\n'
            f'Dime de forma breve, humana y cercana si el huerto está OK o si el usuario debe hacer algo '
            f'(como regar o mover la planta al sol). No uses lenguaje técnico aburrido.'
        )
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7
        )
        consejo = response.choices[0].message.content
        return jsonify({'status': 'success', 'data': sensor_data, 'consejo': consejo})
    except Exception as e:
        print(f'Error en el análisis: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'message': 'Botánico AI activo'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
