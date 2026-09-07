# ?? Guía de Instalación: Huerto AI

Este proyecto conecta un Micro:bit con una App de React Native usando Firebase como puente.

## ?? Requisitos
- Node.js y Expo CLI
- Python 3.x
- Micro:bit v1 o v2
- Cuenta de Google (para Firebase)

## ??? Paso a Paso

### 1. Firebase (La Nube)
1. Crea un proyecto en [Firebase Console](https://console.firebase.google.com/).
2. Crea una **Realtime Database** en modo prueba (Test Mode).
3. En **Configuración del Proyecto** $\rightarrow$ **General**, añade una "Web App" y copia el irebaseConfig en App.js.
4. En **Configuración del Proyecto** $\rightarrow$ **Cuentas de Servicio**, genera una nueva clave privada (archivo .json). Renómbralo a servicio-firebase.json y ponlo en la carpeta del proyecto.

### 2. Micro:bit (El Hardware)
1. Abre [MakeCode Micro:bit](https://makecode.microbit.org/).
2. Cambia la vista de Bloques a **JavaScript**.
3. Pega el contenido de microbit_code.txt.
4. Descarga el código al Micro:bit.

### 3. El Puente (Python)
1. Instala las dependencias: pip install pyserial firebase-admin.
2. Abre ridge.py y pon tu DATABASE_URL y el puerto COM correcto.
3. Ejecuta: python bridge.py.

### 4. La App (Frontend)
1. Instala dependencias: 
pm install.
2. Ejecuta: 
px expo start -c.

## ?? Flujo de Datos
Micro:bit $\xrightarrow{Serial}$ Python $\xrightarrow{REST}$ Firebase $\xrightarrow{Realtime}$ App $\xrightarrow{API}$ IA
