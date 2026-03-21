"""Configuración de la aplicación Streamlit."""

import os

# API del agente
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Colores MeLi
MELI_YELLOW = "#FFE600"
MELI_DARK_BLUE = "#2D3277"
MELI_BLUE = "#3483FA"
MELI_BG = "#EEEEEE"
MELI_TEXT = "#333333"

# Preguntas sugeridas
SUGGESTED_QUESTIONS = [
    "¿Cuáles son los 5 países con más ventas?",
    "¿Cuál es el top 10 de productos por ingreso?",
    "¿Cómo está la calidad de los datos?",
    "¿Cuál es el ticket promedio por canal?",
    "¿Cuál es la tasa de cancelación?",
    "¿Qué columnas tiene la tabla de pedidos?",
    "¿Cuáles son los métodos de pago más usados en Colombia?",
    "¿Cómo se distribuyen los clientes por segmento?",
]
