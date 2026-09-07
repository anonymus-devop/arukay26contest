# ??? Guía de Interfaz con PySide6 para Huerto AI

Si quieres convertir el bridge.py en una app de escritorio profesional, PySide6 es la opción.

## ?? Instalación

pm install PySide6

## ??? Conceptos Clave
- QMainWindow: Ventana principal.
- Layouts: QVBoxLayout (Vertical), QHBoxLayout (Horizontal).
- Widgets: QLabel (Texto), QPushButton (Botón), QProgressBar (Barra de progreso).

## ?? Tip Pro: QThread
Usa QThread para que el bucle de lectura del Micro:bit no congele la UI.
