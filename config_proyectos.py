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

TIEMPO_META = 150

# ---------------------------------------------------------------------
# ACTIVIDADES DEL PROYECTO CON TIEMPOS Y COSTOS
# O, M, P = Tiempos (minutos)
# Tn = Tiempo Normal (se asume igual al TE calculado)
# Cn = Costo Normal (COP)
# Tc = Tiempo de Urgencia (mínimo tiempo posible)
# Cc = Costo de Urgencia (COP)
# ---------------------------------------------------------------------
ACTIVIDADES = [
    {"id": "A", "nombre": "Limpieza y alistamiento", "pre": [], "O": 20, "M": 30, "P": 40, "Cn": 40000, "Tc": 15.0, "Cc": 70000},
    {"id": "B", "nombre": "Venta y verificación de tiquetes", "pre": [], "O": 40, "M": 60, "P": 90, "Cn": 50000, "Tc": 35.0, "Cc": 80000},
    {"id": "C", "nombre": "Inspección mecánica y seguridad", "pre": [], "O": 15, "M": 20, "P": 30, "Cn": 60000, "Tc": 10.0, "Cc": 100000},
    {"id": "D", "nombre": "Revisión de documentos", "pre": [], "O": 5, "M": 10, "P": 15, "Cn": 20000, "Tc": 5.0, "Cc": 35000},
    {"id": "E", "nombre": "Tanqueo de combustible", "pre": ["C"], "O": 10, "M": 15, "P": 20, "Cn": 80000, "Tc": 8.0, "Cc": 110000},
    {"id": "F", "nombre": "Verificación de niveles", "pre": ["C"], "O": 10, "M": 15, "P": 25, "Cn": 30000, "Tc": 8.0, "Cc": 50000},
    {"id": "G", "nombre": "Cargue de equipaje", "pre": ["A"], "O": 15, "M": 25, "P": 35, "Cn": 45000, "Tc": 15.0, "Cc": 65000},
    {"id": "H", "nombre": "Registro de planilla", "pre": ["B", "C"], "O": 10, "M": 15, "P": 20, "Cn": 10000, "Tc": 8.0, "Cc": 20000},
    {"id": "I", "nombre": "Abordaje de pasajeros", "pre": ["B", "G", "H"], "O": 15, "M": 20, "P": 30, "Cn": 35000, "Tc": 12.0, "Cc": 55000},
    {"id": "J", "nombre": "Anuncio de salida", "pre": ["I"], "O": 3, "M": 5, "P": 10, "Cn": 5000, "Tc": 2.0, "Cc": 10000},
    {"id": "K", "nombre": "Salida del bus", "pre": ["E", "F", "J"], "O": 2, "M": 5, "P": 10, "Cn": 15000, "Tc": 3.0, "Cc": 25000},
]