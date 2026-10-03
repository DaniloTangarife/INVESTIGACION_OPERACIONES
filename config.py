# -*- coding: utf-8 -*-
"""
=====================================================================
 CONFIGURACIÓN DEL MODELO  ---  ÚNICA FUENTE DE VERDAD DEL PROYECTO
=====================================================================
TODO el estudio (matriz de pagos, criterios, ecuaciones, sensibilidad,
puntos de corte, EVPI, Bayes, árboles, EVSI, eficiencia, decisión final,
gráficas y textos narrativos) se deriva EXCLUSIVAMENTE de este archivo.

Si el profesor pide cambiar un valor, se cambia AQUÍ y únicamente aquí:
el resto del programa se recalcula solo, incluidos los textos.
=====================================================================
"""

# ---------------------------------------------------------------------
# 1. IDENTIDAD DEL ESTUDIO
# ---------------------------------------------------------------------
TITULO = ("Optimización de Decisiones Bajo Incertidumbre y Análisis de "
          "Información Muestral")
SUBTITULO = ("Caso Operativo Ruta Medellín (Terminal del Sur) – Montebello "
             "· Franja de despachos de los sábados")
CURSO = "Investigación de Operaciones — Ingeniería Informática"
MARCO_LEGAL = "Decreto 1079 de 2015 (Reglamento del Sector Transporte, Colombia)"

# Integrantes del equipo. El primero de la lista marcado como fuente
# es quien aporta la información primaria de la empresa.
EQUIPO = [
    {"nombre": "Danilo Tangarife",
     "rol": "Fuente primaria de datos — trabaja en la empresa de transporte",
     "fuente": True},
]

# ---------------------------------------------------------------------
# 2. UNIDADES MONETARIAS
# ---------------------------------------------------------------------
# Los pagos se escriben en MILES de pesos: 1400 -> 1.400.000 COP
MONEDA = "COP"
FACTOR_MONEDA = 1_000
UNIDAD_CORTA = "miles COP"

# ---------------------------------------------------------------------
# 3. ALTERNATIVAS DE DECISIÓN (d_i)
# ---------------------------------------------------------------------
ALTERNATIVAS = [
    {"id": "d1",
     "nombre": "Invertir en flota",
     "descripcion": ("Adecuar despachos y flota con proyección directa al "
                     "corredor turístico del corregimiento de Sabaletas")},
    {"id": "d2",
     "nombre": "Mantener la ruta",
     "descripcion": ("Conservar estrictamente la ruta tradicional "
                     "Terminal del Sur – Casco Urbano de Montebello")},
]

# ---------------------------------------------------------------------
# 4. ESTADOS DE LA NATURALEZA (s_j)  +  PROBABILIDADES A PRIORI
# ---------------------------------------------------------------------
ESTADOS = [
    {"id": "s1",
     "nombre": "Regulación Permisiva",
     "descripcion": ("Aprobación / flexibilidad regulatoria para la "
                     "extensión de la ruta hacia Sabaletas"),
     "prior": 0.30},
    {"id": "s2",
     "nombre": "Regulación Estricta",
     "descripcion": ("Restricción legal estricta de ruta fija, limitada a "
                     "la cabecera municipal"),
     "prior": 0.70},
]

# ---------------------------------------------------------------------
# 5. MATRIZ DE PAGOS  (filas = alternativas, columnas = estados)
#    Utilidad operativa esperada del sábado, en miles de COP.
# ---------------------------------------------------------------------
MATRIZ_PAGOS = [
    # s1      s2
    [1400,   300],   # d1  Invertir en flota
    [950,    700],   # d2  Mantener la ruta
]

# ---------------------------------------------------------------------
# 6. INFORMACIÓN MUESTRAL — CONSULTORÍA JURÍDICA / ESTUDIO PREVIO
#    Verosimilitudes P(indicador | estado).
#    Cada FILA es un indicador; cada COLUMNA un estado (mismo orden que
#    ESTADOS). Las columnas deben sumar 1.0.
# ---------------------------------------------------------------------
INDICADORES = [
    {"id": "F", "nombre": "Favorable",
     "descripcion": "El concepto jurídico/operativo respalda la extensión de ruta"},
    {"id": "U", "nombre": "Desfavorable",
     "descripcion": "El concepto jurídico/operativo advierte restricción de ruta"},
]

# P(indicador | estado)
VEROSIMILITUDES = [
    # P(·|s1)  P(·|s2)
    [0.65,     0.30],   # Favorable
    [0.35,     0.70],   # Desfavorable
]

# ---------------------------------------------------------------------
# 7. OBJETIVO DEL PROBLEMA
# ---------------------------------------------------------------------
# "max" -> los pagos son utilidades (se maximiza)
# "min" -> los pagos son costos      (se minimiza)
OBJETIVO = "max"

# ---------------------------------------------------------------------
# 8. SALIDA
# ---------------------------------------------------------------------
CARPETA_SALIDA = "salida"
ANCHO_CONSOLA = 100