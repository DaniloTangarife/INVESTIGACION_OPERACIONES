# -*- coding: utf-8 -*-
"""
=====================================================================
 CONFIGURACIÓN — TEORÍA DE JUEGOS
=====================================================================
Segunda parte del estudio. Misma filosofía que config.py: este archivo
es la ÚNICA fuente de datos del tema. Punto de silla, eliminación por
dominancia, matriz de probabilidades, solución algebraica y análisis
gráfico se derivan por completo de la matriz de pagos de abajo.
=====================================================================
"""

# ---------------------------------------------------------------------
# 1. IDENTIDAD DEL JUEGO
# ---------------------------------------------------------------------
TITULO_JUEGO = "Teoría de Juegos — Competencia por el mercado sabatino"
SUBTITULO_JUEGO = ("Corredor Terminal del Sur – Montebello · Nuestra empresa "
                   "frente a la empresa competidora de la ruta")

CONTEXTO_JUEGO = (
    "En la primera parte del estudio la empresa decidió frente a un entorno que "
    "no responde: la regulación no reacciona a lo que haga la compañía. En la "
    "operación real del sábado existe además un segundo frente, y ese sí "
    "reacciona: la otra empresa habilitada en el mismo corredor. Cada sábado "
    "ambas compañías fijan su estrategia de despachos sin saber la del rival, y "
    "los pasajeros del corredor son un total fijo: cada punto porcentual de "
    "mercado que gana una empresa es exactamente el que pierde la otra. Eso lo "
    "convierte en un juego de suma cero de dos jugadores.")

# ---------------------------------------------------------------------
# 2. JUGADORES
# ---------------------------------------------------------------------
JUGADOR_FILA = {
    "id": "I",
    "nombre": "Nuestra empresa",
    "descripcion": "La compañía analizada en la primera parte del estudio. "
                   "Maximiza su participación (jugador maximizador).",
}
JUGADOR_COLUMNA = {
    "id": "II",
    "nombre": "Empresa competidora",
    "descripcion": "La otra compañía habilitada en el corredor. Busca reducir "
                   "la participación de nuestra empresa (jugador minimizador).",
}

# ---------------------------------------------------------------------
# 3. ESTRATEGIAS
# ---------------------------------------------------------------------
ESTRATEGIAS_FILA = [
    {"id": "E1", "nombre": "Extensión a Sabaletas",
     "descripcion": "Despachos prolongados hacia el corredor turístico del "
                    "corregimiento de Sabaletas"},
    {"id": "E2", "nombre": "Refuerzo de frecuencias",
     "descripcion": "Más salidas por hora en la franja crítica de la mañana"},
    {"id": "E3", "nombre": "Tarifa promocional",
     "descripcion": "Descuento sabatino sobre el pasaje del corredor"},
    {"id": "E4", "nombre": "Operación conservadora",
     "descripcion": "Se mantiene la programación habitual sin movimientos"},
]

ESTRATEGIAS_COLUMNA = [
    {"id": "C1", "nombre": "Extensión a Sabaletas",
     "descripcion": "La competencia prolonga sus despachos al corredor turístico"},
    {"id": "C2", "nombre": "Refuerzo de frecuencias",
     "descripcion": "La competencia aumenta salidas en la franja crítica"},
    {"id": "C3", "nombre": "Tarifa promocional",
     "descripcion": "La competencia descuenta el pasaje los sábados"},
    {"id": "C4", "nombre": "Operación conservadora",
     "descripcion": "La competencia mantiene su programación habitual"},
]

# ---------------------------------------------------------------------
# 4. MATRIZ DE PAGOS DEL JUEGO
#    Filas = estrategias de nuestra empresa · Columnas = de la competencia.
#    Cada celda es el PORCENTAJE del mercado sabatino del corredor que
#    capta NUESTRA empresa; el complemento hasta 100 lo capta la
#    competencia (juego de suma cero).
# ---------------------------------------------------------------------
MATRIZ_JUEGO = [
    # C1   C2   C3   C4
    [65,  58,  46,  70],   # E1  Extensión a Sabaletas
    [55,  50,  40,  52],   # E2  Refuerzo de frecuencias
    [60,  44,  62,  64],   # E3  Tarifa promocional
    [42,  30,  35,  48],   # E4  Operación conservadora
]

# ---------------------------------------------------------------------
# 5. UNIDADES
# ---------------------------------------------------------------------
UNIDAD_JUEGO = "% del mercado sabatino"
# Factor con el que la matriz reducida se convierte en matriz de
# probabilidades (participación porcentual → proporción).
FACTOR_PROBABILIDAD = 100