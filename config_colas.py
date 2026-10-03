# -*- coding: utf-8 -*-
"""
=====================================================================
 CONFIGURACIÓN — TEORÍA DE COLAS (M/M/1)
=====================================================================
Tercera parte del estudio. Misma filosofía que config.py y
config_Juegos.py: este archivo es la ÚNICA fuente de datos del tema.
Todos los cálculos, gráficas y textos se derivan de aquí.
=====================================================================
"""

# ---------------------------------------------------------------------
# 1. IDENTIDAD DEL SISTEMA
# ---------------------------------------------------------------------
TITULO_COLAS = "Teoría de Colas — Sistema de venta de tiquetes"
SUBTITULO_COLAS = ("Terminal de transportes Montebello · Venta de pasajes "
                   "dominicales en el corredor Terminal del Sur")

CONTEXTO_COLAS = (
    "El sistema de venta de tiquetes de la terminal de Montebello atiende a los "
    "pasajeros que llegan a comprar su pasaje para los buses que salen los "
    "domingos. El servicio es realizado por un único vendedor (servidor) y "
    "consiste en: recibir la solicitud del pasajero, verificar su documento de "
    "identidad (o digitarlo si ya está registrado), imprimir el tiquete y "
    "entregarlo. El tiempo de servicio es de aproximadamente 1 minuto por "
    "pasajero. Se quiere analizar el comportamiento de la cola y proponer una "
    "mejora que NO implique contratar más personal."
)

# ---------------------------------------------------------------------
# 2. DATOS OPERATIVOS (fuente primaria: trabajo de campo del equipo)
# ---------------------------------------------------------------------
# Rango de ventas diarias observadas (COP)
VENTAS_MIN_DIA = 400_000
VENTAS_MAX_DIA = 750_000

# Precios de los pasajes ofrecidos (COP) — se promedian
PRECIOS_PASAJE = [20_000, 19_000, 18_000, 16_000]

# Buses que salen por día (domingos)
BUSES_POR_DIA = 12

# Horas de operación de la ventanilla (6:00 a 18:00)
HORAS_OPERACION = 12

# ---------------------------------------------------------------------
# 3. TIEMPO DE SERVICIO ACTUAL
# ---------------------------------------------------------------------
# Tiempo promedio de atención por pasajero, en segundos
TIEMPO_SERVICIO_ACTUAL = 60

# ---------------------------------------------------------------------
# 4. MEJORA PROPUESTA (SIN CONTRATAR PERSONAL)
# ---------------------------------------------------------------------
MEJORA_DESCRIPCION = (
    "Digitalización del proceso de venta: (a) instalación de un lector de "
    "cédula que reemplaza la digitación manual del documento, y (b) "
    "habilitación de pago electrónico (QR o transferencia) que reemplaza el "
    "manejo de efectivo y la devolución de cambio. El mismo vendedor sigue "
    "atendiendo, pero con mejores herramientas."
)

MEJORA_JUSTIFICACION = (
    "Se eligió esta mejora porque (1) no requiere contratar personal ni abrir "
    "una nueva ventanilla, (2) reduce el tiempo de servicio en un 25% al "
    "eliminar los dos pasos más lentos del proceso (digitación y manejo de "
    "efectivo), (3) tiene un costo de implementación muy bajo (un lector de "
    "cédula cuesta alrededor de 100.000 COP y el software ya existe), (4) "
    "disminuye los errores de digitación y (5) mejora la experiencia del "
    "pasajero con métodos de pago modernos."
)

# Factor de reducción del tiempo de servicio (0.75 = reduce 25%)
FACTOR_MEJORA = 0.75

# ---------------------------------------------------------------------
# 5. UNIDADES Y PRESENTACIÓN
# ---------------------------------------------------------------------
UNIDAD_TIEMPO = "minutos"
UNIDAD_TASA = "clientes/hora"

# Número máximo de clientes para el cálculo de Pn
N_PN = 10

# ---------------------------------------------------------------------
# 6. SALIDA
# ---------------------------------------------------------------------
CARPETA_SALIDA = "salida"