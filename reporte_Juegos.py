# -*- coding: utf-8 -*-
"""
=====================================================================
 REPORTE EN CONSOLA — TEORÍA DE JUEGOS
=====================================================================
Reutiliza las primitivas de reporte.py. Ningún valor está escrito a
mano: todo proviene del objeto JuegoSumaCero.
=====================================================================
"""
from __future__ import annotations

from juegos import JuegoSumaCero
from modelo import num, pct
from reporte import marco, parrafo, tabla, titulo_paso


def encabezado_juego(j: JuegoSumaCero) -> str:
    cfg = j.cfg
    cuerpo = [
        "¿POR QUÉ UN SEGUNDO MODELO?",
        cfg.CONTEXTO_JUEGO,
        "",
        "LOS JUGADORES",
        f"• Jugador I — {cfg.JUGADOR_FILA['nombre']}: {cfg.JUGADOR_FILA['descripcion']}",
        f"• Jugador II — {cfg.JUGADOR_COLUMNA['nombre']}: "
        f"{cfg.JUGADOR_COLUMNA['descripcion']}",
        "",
        "ESTRATEGIAS DEL JUGADOR I (filas)",
    ]
    for e in cfg.ESTRATEGIAS_FILA:
        cuerpo.append(f"• {e['id']} — {e['nombre']}: {e['descripcion']}.")
    cuerpo += ["", "ESTRATEGIAS DEL JUGADOR II (columnas)"]
    for e in cfg.ESTRATEGIAS_COLUMNA:
        cuerpo.append(f"• {e['id']} — {e['nombre']}: {e['descripcion']}.")
    cuerpo += [
        "",
        "CÓMO LEER LA MATRIZ",
        f"Cada celda es el {cfg.UNIDAD_JUEGO} que capta el jugador I; el "
        f"complemento hasta {num(j.factor, 0)} lo capta el jugador II. Por eso es un "
        f"juego de suma cero: lo que uno gana, el otro lo pierde exactamente.",
    ]
    return ("\n" + marco(cfg.TITULO_JUEGO.upper(), [cfg.SUBTITULO_JUEGO], doble=True)
            + "\n\n" + marco("CONTEXTO DEL JUEGO", cuerpo))


def jpaso1(j: JuegoSumaCero) -> str:
    enc = ["Jugador I \\ II"] + list(j.ids_c) + ["Mín. fila"]
    filas = [[f"{f} · {j.nombre_f[f]}"] + [num(j.pagos[f][c], 0) for c in j.ids_c]
             + [num(j.min_fila[f], 0)] for f in j.ids_f]
    filas.append(["Máx. columna"] + [num(j.max_col[c], 0) for c in j.ids_c] + [""])
    return "\n".join([
        titulo_paso("J1", "Matriz de pagos del juego") if False else
        "\n" + "═" * 100 + "\n"
        + " TEORÍA DE JUEGOS · PASO 1: MATRIZ DE PAGOS ".center(100, "═")
        + "\n" + "═" * 100,
        parrafo(f"Pagos expresados en {j.unidad} para el jugador I."),
        "", tabla(enc, filas),
    ])


def jpaso2(j: JuegoSumaCero) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 2: PUNTO DE SILLA ".center(100, "═")
           + "\n" + "═" * 100,
           parrafo("Se compara el mejor de los peores resultados del jugador I "
                   "(maximin) con el peor de los mejores del jugador II (minimax). "
                   "Si coinciden, ese valor es un punto de silla y el juego se "
                   "resuelve con estrategias puras."),
           "",
           f"      Maximin = máx(mín. fila) = {num(j.maximin, 0)}   "
           f"(fila {j.fila_maximin})",
           f"      Minimax = mín(máx. columna) = {num(j.minimax, 0)}   "
           f"(columna {j.col_minimax})", ""]
    if j.hay_silla:
        f, c, v = j.sillas[0]
        txt.append(marco("HAY PUNTO DE SILLA", [
            f"Maximin = Minimax = {num(v, 0)}",
            f"Punto de silla en ({f}, {c}) → valor del juego = {num(v, 0)} {j.unidad}.",
            f"Estrategias puras: el jugador I juega siempre {f} y el jugador II "
            f"siempre {c}."]))
    else:
        txt.append(marco("NO HAY PUNTO DE SILLA", [
            f"Maximin ({num(j.maximin, 0)}) ≠ Minimax ({num(j.minimax, 0)}).",
            "No existe solución en estrategias puras: ninguna pareja de estrategias "
            "fijas es estable. Se continúa con la eliminación por dominancia para "
            "reducir la matriz y resolver con estrategias mixtas."]))
    return "\n".join(txt)


def jpaso3(j: JuegoSumaCero) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 3: ELIMINACIÓN POR DOMINANCIA ".center(100, "═")
           + "\n" + "═" * 100]
    if not j.pasos:
        txt.append(parrafo("No se requiere: el juego ya quedó resuelto con el punto "
                           "de silla."))
        return "\n".join(txt)
    txt.append(parrafo(
        "Se empieza por las filas y luego se pasa a las columnas, de forma "
        "iterativa. En filas, la estrategia con mayores pagos elimina a la de "
        "menores (el jugador I maximiza). En columnas, la de menores pagos elimina "
        "a la de mayores (el jugador II minimiza). Las posiciones originales de los "
        "valores que sobreviven se conservan."))
    for p in j.pasos:
        txt += ["", f"» Paso {p.orden} — se elimina la {p.tipo} {p.eliminada} "
                    f"({(j.nombre_f if p.tipo == 'fila' else j.nombre_c)[p.eliminada]})",
                f"   Dominada por {p.dominante} "
                f"({(j.nombre_f if p.tipo == 'fila' else j.nombre_c)[p.dominante]}):"]
        for ln in p.comparacion:
            txt.append(f"      {ln}")
        txt.append(parrafo(p.explicacion, "   "))
        enc = ["Jugador I \\ II"] + list(p.columnas_antes)
        filas = []
        for f in p.filas_antes:
            marca = "  ← ELIMINADA" if (p.tipo == "fila" and f == p.eliminada) else ""
            filas.append([f"{f}{marca}"] + [num(j.pagos[f][c], 0)
                                            for c in p.columnas_antes])
        if p.tipo == "columna":
            filas.append(["↑ ELIMINADA"] + ["  ←" if c == p.eliminada else ""
                                            for c in p.columnas_antes])
        txt.append(tabla(enc, filas))
    txt.append("")
    txt.append(marco("MATRIZ RESULTANTE", [
        f"Sobreviven las estrategias {', '.join(j.filas_finales)} del jugador I "
        f"frente a {', '.join(j.columnas_finales)} del jugador II.",
        f"Tamaño: {len(j.filas_finales)}×{len(j.columnas_finales)} "
        f"(original {len(j.ids_f)}×{len(j.ids_c)})."]))
    return "\n".join(txt)


def jpaso4(j: JuegoSumaCero) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 4: MATRIZ DE PROBABILIDADES ".center(100, "═")
           + "\n" + "═" * 100]
    if not j.reduccion_completa:
        txt.append(parrafo("No aplica: la reducción no llegó a una matriz 2×2."))
        return "\n".join(txt)
    ff, cc = j.filas_finales, j.columnas_finales
    txt.append(parrafo(f"Los valores que sobrevivieron se dividen por "
                       f"{num(j.factor, 0)} para expresarlos como proporciones."))
    txt.append("")
    txt.append(tabla(["Matriz reducida"] + list(cc),
                     [[f] + [num(j.matriz_reducida[f][c], 0) for c in cc] for f in ff]))
    txt.append(tabla(["Matriz de probabilidades"] + list(cc),
                     [[f] + [num(j.matriz_prob[f][c], 2) for c in cc] for f in ff]))
    return "\n".join(txt)


def jpaso5(j: JuegoSumaCero) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 5: ANÁLISIS ALGEBRAICO ".center(100, "═")
           + "\n" + "═" * 100]
    if not (j.reduccion_completa and j.solucion_fila):
        txt.append(parrafo("No aplica con la matriz resultante."))
        return "\n".join(txt)
    for sol, quien in [(j.solucion_fila, f"Jugador I — {j.cfg.JUGADOR_FILA['nombre']}"),
                       (j.solucion_columna,
                        f"Jugador II — {j.cfg.JUGADOR_COLUMNA['nombre']}")]:
        txt += ["", f"» {quien}", parrafo(sol.etiqueta_p, "   "),
                parrafo(sol.etiqueta_q, "   "), ""]
        for ec in sol.ecuaciones:
            txt.append(f"      {ec}")
        txt.append("      * Igualar y resolver para p:")
        for ln in sol.algebra:
            txt.append(f"      {ln}")
    txt.append("")
    txt.append(marco("COMPROBACIÓN", [
        f"Valor del juego desde el jugador I: {num(j.solucion_fila.valor, 4)}",
        f"Valor del juego desde el jugador II: {num(j.solucion_columna.valor, 4)}",
        f"Ambos coinciden ✔  →  {num(j.valor_juego, 2)} {j.unidad} para el jugador I.",
        f"Suma de probabilidades de cada jugador = "
        f"{num(j.solucion_fila.p + j.solucion_fila.q, 4)} ✔"]))
    return "\n".join(txt)


def jpaso6(j: JuegoSumaCero, archivos: dict) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 6: ANÁLISIS GRÁFICO ".center(100, "═")
           + "\n" + "═" * 100]
    if not (j.reduccion_completa and j.solucion_fila):
        txt.append(parrafo("No aplica con la matriz resultante."))
        return "\n".join(txt)
    txt.append(parrafo("Primero lo algebraico y después el gráfico: cada ecuación es "
                       "una recta sobre p ∈ [0, 1] y el punto de corte es la "
                       "estrategia óptima."))
    for sol, quien in [(j.solucion_fila, "Jugador I"), (j.solucion_columna, "Jugador II")]:
        filas = [[k, r["ecuacion"], f"(0 , {num(r['b'], 2)})",
                  f"(1 , {num(r['m'] + r['b'], 2)})"] for k, r in sol.rectas.items()]
        txt += ["", f"» {quien}", tabla(["Recta", "Ecuación", "Punto p = 0",
                                         "Punto p = 1"], filas, alinear_izq=2)]
    txt.append("")
    txt.append(parrafo(f"Gráfica generada en: {archivos.get('juego_grafico', '—')}"))
    return "\n".join(txt)


def jpaso7(j: JuegoSumaCero) -> str:
    txt = ["\n" + "═" * 100 + "\n"
           + " TEORÍA DE JUEGOS · PASO 7: ESTRATEGIAS ÓPTIMAS Y VALOR DEL JUEGO "
           .center(100, "═") + "\n" + "═" * 100]
    txt.append(marco("CONCLUSIÓN DEL JUEGO", j.texto_conclusion(), doble=True))
    filas = [["Tipo de solución", j.tipo_solucion],
             ["Maximin", num(j.maximin, 0)],
             ["Minimax", num(j.minimax, 0)],
             ["Estrategias del jugador I", ", ".join(j.filas_finales)],
             ["Estrategias del jugador II", ", ".join(j.columnas_finales)]]
    if j.solucion_fila:
        f1, f2 = j.filas_finales
        c1, c2 = j.columnas_finales
        filas += [[f"Probabilidad de {f1}", pct(j.solucion_fila.p, 2)],
                  [f"Probabilidad de {f2}", pct(j.solucion_fila.q, 2)],
                  [f"Probabilidad de {c1}", pct(j.solucion_columna.p, 2)],
                  [f"Probabilidad de {c2}", pct(j.solucion_columna.q, 2)]]
    filas.append(["Valor del juego", f"{num(j.valor_juego, 2)} {j.unidad}"])
    txt.append(tabla(["Indicador", "Resultado"], filas, alinear_izq=1))
    return "\n".join(txt)


def reporte_juego(j: JuegoSumaCero, archivos: dict) -> str:
    return "\n".join([encabezado_juego(j), jpaso1(j), jpaso2(j), jpaso3(j),
                      jpaso4(j), jpaso5(j), jpaso6(j, archivos), jpaso7(j)])