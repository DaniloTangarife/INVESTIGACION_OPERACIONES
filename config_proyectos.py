# -*- coding: utf-8 -*-
"""
=====================================================================
 CONFIGURACIÓN — DIRECCIÓN DE PROYECTOS (CPM / PERT)
=====================================================================
"""

TITULO_PROYECTO = "Dirección de Proyectos — Despacho de un bus"
SUBTITULO_PROYECTO = "Terminal de transportes Montebello · Proceso operativo dominical"

CONTEXTO_PROYECTO = (
    "El proceso de despacho de un bus en la terminal de Montebello involucra "
    "múltiples actividades que deben coordinarse para que el vehículo salga a tiempo. "
    "Algunas tareas son secuenciales (como el tanqueo que depende de la inspección), "
    "mientras que otras pueden ocurrir en paralelo (como la limpieza y la venta de "
    "tiquetes). Este modelo usa la red PERT/CPM para identificar la ruta crítica: "
    "la secuencia de actividades que determina el tiempo mínimo de despacho."
)

# Tiempo meta para calcular la probabilidad de cumplimiento (en minutos)
TIEMPO_META = 150

# ---------------------------------------------------------------------
# ACTIVIDADES DEL PROYECTO
# O = Optimista, M = Más probable, P = Pesimista (en minutos)
# ---------------------------------------------------------------------
ACTIVIDADES = [
    {"id": "A", "nombre": "Limpieza y alistamiento", "pre": [], "O": 20, "M": 30, "P": 40},
    {"id": "B", "nombre": "Venta y verificación de tiquetes", "pre": [], "O": 40, "M": 60, "P": 90},
    {"id": "C", "nombre": "Inspección mecánica y seguridad", "pre": [], "O": 15, "M": 20, "P": 30},
    {"id": "D", "nombre": "Revisión de documentos", "pre": [], "O": 5, "M": 10, "P": 15},
    {"id": "E", "nombre": "Tanqueo de combustible", "pre": ["C"], "O": 10, "M": 15, "P": 20},
    {"id": "F", "nombre": "Verificación de niveles", "pre": ["C"], "O": 10, "M": 15, "P": 25},
    {"id": "G", "nombre": "Cargue de equipaje", "pre": ["A"], "O": 15, "M": 25, "P": 35},
    {"id": "H", "nombre": "Registro de planilla", "pre": ["B", "C"], "O": 10, "M": 15, "P": 20},
    {"id": "I", "nombre": "Abordaje de pasajeros", "pre": ["B", "G", "H"], "O": 15, "M": 20, "P": 30},
    {"id": "J", "nombre": "Anuncio de salida", "pre": ["I"], "O": 3, "M": 5, "P": 10},
    {"id": "K", "nombre": "Salida del bus", "pre": ["E", "F", "J"], "O": 2, "M": 5, "P": 10},
]