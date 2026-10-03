# -*- coding: utf-8 -*-
"""
=====================================================================
 REPORTE EN CONSOLA — Presentación de los 13 pasos
=====================================================================
Ningún valor está escrito a mano: todos provienen del objeto modelo.
=====================================================================
"""
from __future__ import annotations

import textwrap

import config as CFG
from modelo import ModeloDecision, dinero, num, pct

A = CFG.ANCHO_CONSOLA


# ---------------------------------------------------------------------
#  PRIMITIVAS DE DIBUJO
# ---------------------------------------------------------------------
def _linea(car: str = "─") -> str:
    return car * A


def marco(titulo: str, cuerpo: list[str], doble: bool = False) -> str:
    """Cuadro con borde para destacar bloques de texto."""
    tl, tr, bl, br, h, v = ("╔", "╗", "╚", "╝", "═", "║") if doble else ("┌", "┐", "└", "┘", "─", "│")
    ancho = A - 2
    out = [tl + h * ancho + tr]
    if titulo:
        out.append(v + titulo.center(ancho) + v)
        out.append(v + ("─" * (ancho - 2)).center(ancho) + v)
    for parrafo in cuerpo:
        if parrafo == "":
            out.append(v + " " * ancho + v)
            continue
        for ln in textwrap.wrap(parrafo, ancho - 4) or [""]:
            out.append(v + "  " + ln.ljust(ancho - 4) + "  " + v)
    out.append(bl + h * ancho + br)
    return "\n".join(out)


def titulo_paso(n: int, texto: str) -> str:
    etiqueta = f" PASO {n}: {texto.upper()} "
    return "\n" + "═" * A + f"\n{etiqueta.center(A, '═')}\n" + "═" * A


def tabla(encabezados: list[str], filas: list[list[str]], alinear_izq: int = 1) -> str:
    """Tabla de ancho automático."""
    cols = list(zip(*([encabezados] + filas))) if filas else [encabezados]
    anchos = [max(len(str(c)) for c in col) + 2 for col in cols]

    def fmt(fila, relleno=" "):
        celdas = []
        for i, (c, w) in enumerate(zip(fila, anchos)):
            celdas.append(str(c).ljust(w) if i < alinear_izq else str(c).rjust(w))
        return "│" + "│".join(celdas) + "│"

    sep_top = "┌" + "┬".join("─" * w for w in anchos) + "┐"
    sep_mid = "├" + "┼".join("─" * w for w in anchos) + "┤"
    sep_bot = "└" + "┴".join("─" * w for w in anchos) + "┘"
    out = [sep_top, fmt(encabezados), sep_mid]
    out += [fmt(f) for f in filas]
    out.append(sep_bot)
    return "\n".join(out)


def parrafo(texto: str, sangria: str = "  ") -> str:
    return textwrap.fill(texto, A - len(sangria), initial_indent=sangria,
                         subsequent_indent=sangria)


# ---------------------------------------------------------------------
#  CONTEXTO INICIAL (portada)
# ---------------------------------------------------------------------
def portada(m: ModeloDecision) -> str:
    c = m.cfg
    fuentes = [p["nombre"] for p in c.EQUIPO if p.get("fuente")]
    nombres = ", ".join(fuentes) if fuentes else "el equipo de trabajo"

    cuerpo = [
        "¿QUÉ ES ESTE ESTUDIO?",
        (f"Se analiza la operación logística de los días sábado en la franja crítica de "
         f"despachos de una empresa real de transporte intermunicipal, en la ruta "
         f"{c.SUBTITULO.split('·')[0].split('Caso Operativo')[-1].strip()}."),
        "",
        "LA PREGUNTA QUE SE RESUELVE",
        (f"Bajo el marco del {c.MARCO_LEGAL}, la empresa debe decidir entre "
         + " y ".join(f"{a['id']} ({a['nombre']}: {a['descripcion'].lower()})"
                      for a in c.ALTERNATIVAS)
         + ". El resultado económico de esa decisión depende de un factor que la empresa "
           "no controla: el estado regulatorio."),
        "",
        "LOS ESCENARIOS POSIBLES (estados de la naturaleza)",
    ]
    for e in c.ESTADOS:
        cuerpo.append(f"• {e['id']} — {e['nombre']} ({pct(e['prior'], 0)}): {e['descripcion']}.")
    cuerpo += [
        "",
        "LO QUE SE BUSCA",
        "• Determinar la alternativa que maximiza la utilidad monetaria esperada.",
        "• Evaluar qué tan estable es esa decisión si cambian las probabilidades (sensibilidad y punto de corte).",
        "• Medir cuánto vale reducir la incertidumbre: información perfecta (EVPI) e información muestral (EVSI).",
        "• Concluir, con cifras, si conviene o no pagar una consultoría jurídica previa.",
        "",
        "ORIGEN DE LOS DATOS — IMPORTANTE",
        (f"Los datos utilizados en este estudio NO son inventados ni simulados con fines "
         f"académicos. {nombres} hace parte del equipo de trabajo y labora actualmente en "
         f"la empresa de transporte analizada, por lo que cuenta con acceso directo y "
         f"autorizado a la información operativa real: utilidades por despacho, niveles de "
         f"ocupación de los sábados y condiciones regulatorias vigentes de la ruta. Las "
         f"cifras de la matriz de pagos provienen de esa fuente primaria, lo que hace que "
         f"las conclusiones de este modelo sean directamente aplicables a la operación."),
        "",
        "CÓMO LEER LAS CIFRAS",
        (f"Todos los pagos están expresados en {c.UNIDAD_CORTA}: un valor de "
         f"{num(c.MATRIZ_PAGOS[0][0], 0)} equivale a {dinero(c.MATRIZ_PAGOS[0][0])}."),
    ]
    encabezado = (f"{c.TITULO}\n{c.SUBTITULO}\n{c.CURSO}")
    return (marco(c.TITULO.upper(), [c.SUBTITULO, c.CURSO], doble=True) + "\n\n"
            + marco("CONTEXTO DEL PROBLEMA", cuerpo))


# ---------------------------------------------------------------------
#  LOS 13 PASOS
# ---------------------------------------------------------------------
def paso1(m: ModeloDecision) -> str:
    enc = ["Alternativa"] + [f"{e['id']} · {e['nombre']}" for e in m.estados]
    filas = [[f"{a} · {m.nombre_alt[a]}"] + [num(m.pagos[a][s], 0) for s in m.ids_est]
             for a in m.ids_alt]
    filas.append(["Probabilidad a priori"] + [num(m.prior[s]) for s in m.ids_est])
    txt = [titulo_paso(1, "Matriz de pagos"),
           parrafo("Utilidad operativa del sábado para cada combinación de decisión y "
                   f"estado regulatorio, en {m.cfg.UNIDAD_CORTA}."), "",
           tabla(enc, filas)]
    txt.append("")
    txt.append(parrafo(f"Suma de probabilidades = {num(sum(m.prior.values()))} ✔  "
                       f"Objetivo del modelo: {'MAXIMIZAR utilidad' if m.objetivo == 'max' else 'MINIMIZAR costo'}."))
    return "\n".join(txt)


def paso2(m: ModeloDecision) -> str:
    txt = [titulo_paso(2, "Criterios bajo incertidumbre (sin probabilidades)")]
    for c in m.criterios:
        txt += ["", f"» {c.nombre}", parrafo(c.descripcion)]
        filas = [[f"{a} · {m.nombre_alt[a]}", num(c.valores[a], 0),
                  "◄ ELEGIDA" if a == c.elegida else ""] for a in m.ids_alt]
        txt.append(tabla(["Alternativa", "Valor del criterio", ""], filas))
        txt.append(parrafo(f"Decisión por este criterio: {c.elegida} — "
                           f"{m.nombre_alt[c.elegida]} (valor {num(c.valor_elegido, 0)})."))

    txt += ["", "» Matriz de arrepentimiento utilizada en el tercer criterio"]
    enc = ["Alternativa"] + [m.nombre_est[s] for s in m.ids_est] + ["Máximo arrepentimiento"]
    filas = [[f"{a} · {m.nombre_alt[a]}"]
             + [num(m.matriz_arrepentimiento[a][s], 0) for s in m.ids_est]
             + [num(max(m.matriz_arrepentimiento[a].values()), 0)] for a in m.ids_alt]
    txt.append(tabla(enc, filas))

    coinciden = len({c.elegida for c in m.criterios}) == 1
    txt.append("")
    txt.append(parrafo(
        "Los tres criterios coinciden en la misma alternativa, lo que refuerza la robustez "
        "de la decisión." if coinciden else
        "Los criterios NO coinciden entre sí: " +
        "; ".join(f"{c.nombre.split('(')[0].strip()} → {c.elegida}" for c in m.criterios) +
        ". Esto es esperable, pues cada criterio refleja una actitud distinta frente al "
        "riesgo; por eso el estudio continúa incorporando las probabilidades, que sí "
        "permiten una decisión fundamentada."))
    return "\n".join(txt)


def paso3(m: ModeloDecision) -> str:
    txt = [titulo_paso(3, "Valor esperado con las probabilidades a priori"),
           parrafo("Se pondera cada pago por la probabilidad de su estado: "
                   "EV(d) = Σ P(s)·pago(d,s)."), ""]
    for a in m.ids_alt:
        txt.append(f"  {m.desarrollo_ev[a]}   →  {dinero(m.ev_prior[a])}")
    txt += ["", tabla(["Alternativa", "Valor esperado", "Equivalente", ""],
                      [[f"{a} · {m.nombre_alt[a]}", num(m.ev_prior[a]), dinero(m.ev_prior[a]),
                        "◄ ÓPTIMA" if a == m.alt_optima_prior else ""] for a in m.ids_alt])]
    txt.append("")
    txt.append(marco("DECISIÓN CON LA INFORMACIÓN DISPONIBLE",
                     [f"Alternativa óptima: {m.alt_optima_prior} — {m.nombre_alt[m.alt_optima_prior]}",
                      f"Valor esperado: {dinero(m.ev_optimo_prior)}"]))
    return "\n".join(txt)


def paso4(m: ModeloDecision, escenarios: list[float]) -> str:
    s1 = m.ids_est[0]
    txt = [titulo_paso(4, "Análisis de sensibilidad"),
           parrafo(f"Se somete a cambio la variable P({s1}) = p (por lo tanto "
                   f"P({m.ids_est[1]}) = 1 − p) y se observa cómo se comporta la decisión "
                   f"en todo su recorrido."), ""]
    for a in m.ids_alt:
        txt.append(f"  {a}:")
        for ln in m.rectas[a]["pasos"]:
            txt.append(f"      {ln}")
        txt.append("")
    enc = [f"P({s1})"] + [f"EV({a})" for a in m.ids_alt] + ["Decisión óptima", "Valor"]
    filas = []
    for p in escenarios:
        e = m.escenario(p)
        etiqueta = ("INDIFERENTE (" + " = ".join(e["empatadas"]) + ")" if e["empate"]
                    else f"{e['elegida']} · {m.nombre_alt[e['elegida']]}")
        filas.append([pct(p, 2 if e["empate"] else 0)]
                     + [num(e["ev"][a]) for a in m.ids_alt]
                     + [etiqueta, num(e["valor"])])
    txt.append(tabla(enc, filas))
    txt.append("")
    for t in m.tramos:
        txt.append(parrafo(f"• Si {pct(t.p_ini, 2)} ≤ P({s1}) ≤ {pct(t.p_fin, 2)} → "
                           f"la decisión óptima es {t.dominante} · {m.nombre_alt[t.dominante]}."))
    return "\n".join(txt)


def paso5(m: ModeloDecision, archivos: dict) -> str:
    s1 = m.ids_est[0]
    txt = [titulo_paso(5, "Análisis gráfico"),
           parrafo(f"Cada alternativa es una recta EV(d) = m·p + b sobre el eje "
                   f"p = P({s1}) ∈ [0, 1]. Con dos puntos por recta basta para graficarla."), ""]
    enc = ["Alternativa", "Ecuación", "Punto p = 0", "Punto p = 1"]
    filas = [[a, m.rectas[a]["ecuacion"],
              f"(0 , {num(m.rectas[a]['punto_p0'][1], 0)})",
              f"(1 , {num(m.rectas[a]['punto_p1'][1], 0)})"] for a in m.ids_alt]
    txt.append(tabla(enc, filas, alinear_izq=4))
    txt.append("")
    txt.append(parrafo(f"Gráfica generada automáticamente en: {archivos.get('sensibilidad', '—')}"))
    return "\n".join(txt)


def paso6(m: ModeloDecision) -> str:
    txt = [titulo_paso(6, "Puntos de corte (igualación de ecuaciones)")]
    for c in m.cortes:
        txt += ["", f"» {c.a} vs {c.b}"]
        for ln in c.algebra:
            txt.append(f"      {ln}")
        if c.valido:
            txt.append(parrafo(f"Punto de corte válido en p = {num(c.p, 4)} ({pct(c.p)}), "
                               f"con un valor esperado común de {dinero(c.valor)}."))
        elif c.p == c.p:
            txt.append(parrafo(f"El corte cae en p = {num(c.p, 4)}, fuera del intervalo "
                               f"[0, 1]; no tiene sentido práctico: una alternativa domina "
                               f"a la otra en todo el recorrido."))
    u = m.umbral_decisorio
    if u:
        otra = u.b if u.a == m.alt_optima_prior else u.a
        p1 = m.prior[m.ids_est[0]]
        txt += ["", marco("INTERPRETACIÓN DEL UMBRAL", [
            f"P({m.ids_est[0]}) debe {'superar' if p1 < u.p else 'caer por debajo de'} "
            f"{pct(u.p)} para que convenga cambiar a {otra} · {m.nombre_alt[otra]}.",
            f"Valor actual estimado: {pct(p1, 0)} → margen de "
            f"{num(abs(p1 - u.p) * 100)} puntos porcentuales.",
            f"Conclusión: la decisión {m.alt_optima_prior} es "
            f"{'estable' if abs(p1 - u.p) > 0.10 else 'sensible a pequeños cambios'}."])]
    return "\n".join(txt)


def paso7(m: ModeloDecision) -> str:
    txt = [titulo_paso(7, "Valor esperado de la información perfecta (EVPI)"),
           parrafo("Si se supiera con certeza qué estado va a ocurrir, se elegiría la "
                   "mejor alternativa en cada caso."), ""]
    filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
              f"{m.mejor_decision_por_estado[s]} · {m.nombre_alt[m.mejor_decision_por_estado[s]]}",
              num(m.mejor_por_estado[s], 0)] for s in m.ids_est]
    txt.append(tabla(["Estado", "Probabilidad", "Mejor decisión si ocurre", "Pago"], filas, 3))
    txt.append("")
    for ln in m.desarrollo_evpi:
        txt.append(f"      {ln}")
    txt += ["", marco("LECTURA GERENCIAL DEL EVPI", [
        f"EVPI = {dinero(m.evpi)}.",
        f"Es el máximo que la empresa debería pagar por eliminar por completo la "
        f"incertidumbre regulatoria. Ningún estudio, consultoría o asesoría puede "
        f"valer más que esta cifra."])]
    return "\n".join(txt)


def paso8(m: ModeloDecision) -> str:
    txt = [titulo_paso(8, "Análisis de decisiones con información muestral"),
           parrafo("Antes de decidir se puede contratar una consultoría jurídica/operativa "
                   "cuyo concepto es un indicador imperfecto del estado real. Su "
                   "confiabilidad se expresa como P(indicador | estado)."), ""]
    enc = ["Indicador"] + [f"P(·|{s})" for s in m.ids_est]
    filas = [[f"{i} · {m.nombre_ind[i]}"] + [num(m.verosimilitud[i][s]) for s in m.ids_est]
             for i in m.ids_ind]
    filas.append(["Suma por columna"] + [num(sum(m.verosimilitud[i][s] for i in m.ids_ind))
                                         for s in m.ids_est])
    txt.append(tabla(enc, filas))
    txt += ["", "» Probabilidades marginales de cada resultado del estudio:"]
    for r in m.ramas:
        det = " + ".join(f"{num(m.verosimilitud[r.indicador][s])}·{num(m.prior[s])}"
                         for s in m.ids_est)
        txt.append(f"      P({r.indicador}) = {det} = {num(r.prob_indicador, 4)}")
    txt.append(f"      Suma = {num(sum(r.prob_indicador for r in m.ramas), 4)} ✔")
    return "\n".join(txt)


def paso9(m: ModeloDecision) -> str:
    txt = [titulo_paso(9, "Teorema de Bayes — probabilidades posteriores"),
           parrafo("P(s | indicador) = [ P(indicador | s) · P(s) ] / P(indicador)"), ""]
    for r in m.ramas:
        txt.append(f"» Resultado {r.nombre} ({r.indicador}) — P({r.indicador}) = {num(r.prob_indicador, 4)}")
        filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
                  num(m.verosimilitud[r.indicador][s]), num(r.conjuntas[s], 4),
                  num(r.posteriores[s], 4), pct(r.posteriores[s])] for s in m.ids_est]
        filas.append(["Total", num(sum(m.prior.values())), "—",
                      num(r.prob_indicador, 4), num(sum(r.posteriores.values()), 4), "100,00%"])
        txt.append(tabla(["Estado", "P(s) previa", f"P({r.indicador}|s)",
                          "Conjunta", "P(s|ind.)", "%"], filas))
        txt.append("  Valores esperados revisados con estas probabilidades:")
        for a in m.ids_alt:
            det = " + ".join(f"{num(r.posteriores[s], 4)}·({num(m.pagos[a][s], 0)})"
                             for s in m.ids_est)
            marca = "  ◄ ÓPTIMA" if a == r.elegida else ""
            txt.append(f"      EV({a}|{r.indicador}) = {det} = {num(r.ev[a])}{marca}")
        txt.append(parrafo(f"Si el estudio resulta {r.nombre}, la decisión "
                           f"{'CAMBIA a' if r.elegida != m.alt_optima_prior else 'se RATIFICA en'} "
                           f"{r.elegida} · {m.nombre_alt[r.elegida]} con {dinero(r.valor)}."))
        txt.append("")
    return "\n".join(txt)


def paso10(m: ModeloDecision, archivos: dict) -> str:
    txt = [titulo_paso(10, "Árboles de decisión"),
           parrafo("Se construyen dos árboles: el de la decisión inicial (sin estudio) y el "
                   "de la decisión condicionada al resultado del estudio. Los nodos "
                   "cuadrados son decisiones (controla la empresa) y los circulares son "
                   "nodos de azar (controla el entorno regulatorio). La resolución es por "
                   "inducción hacia atrás: se promedia en los nodos de azar y se optimiza "
                   "en los nodos de decisión."), ""]
    txt.append(f"  • Árbol sin información muestral   → valor en la raíz: {dinero(m.ev_optimo_prior)}")
    txt.append(f"  • Árbol con información muestral   → valor en la raíz: {dinero(m.ev_con_info_muestral)}")
    txt += ["", parrafo(f"Archivos generados: {archivos.get('arbol_prior', '—')} y "
                        f"{archivos.get('arbol_muestral', '—')}")]
    return "\n".join(txt)


def paso11(m: ModeloDecision) -> str:
    txt = [titulo_paso(11, "Valor de la información muestral (EVSI)"), ""]
    filas = [[f"{r.indicador} · {r.nombre}", num(r.prob_indicador, 4),
              f"{r.elegida} · {m.nombre_alt[r.elegida]}", num(r.valor),
              num(r.prob_indicador * r.valor)] for r in m.ramas]
    txt.append(tabla(["Resultado del estudio", "P(resultado)", "Decisión óptima",
                      "Valor esperado", "Aporte ponderado"], filas, 3))
    txt.append("")
    for ln in m.desarrollo_evsi[:2]:
        txt.append(f"      {ln}")
    txt += ["", tabla(["Concepto", "Valor", "Equivalente"], [
        ["Valor esperado SIN información muestral (decisión a priori)",
         num(m.ev_sin_info_muestral), dinero(m.ev_sin_info_muestral)],
        ["Valor esperado CON información muestral (estudio)",
         num(m.ev_con_info_muestral), dinero(m.ev_con_info_muestral)],
        ["EVSI = diferencia entre ambos", num(m.evsi), dinero(m.evsi)],
    ], alinear_izq=1)]
    txt.append("")
    txt.append(parrafo(f"Interpretación: contratar la consultoría solo tiene sentido si su "
                       f"honorario es inferior a {dinero(m.evsi)}."))
    return "\n".join(txt)


def paso12(m: ModeloDecision) -> str:
    txt = [titulo_paso(12, "Eficiencia del estudio de mercado"), "",
           f"      {m.desarrollo_evsi[2]}", "",
           tabla(["Concepto", "Valor", "Equivalente"], [
               ["EVSI — información muestral (imperfecta)", num(m.evsi), dinero(m.evsi)],
               ["EVPI — información perfecta", num(m.evpi), dinero(m.evpi)],
               ["Eficiencia = EVSI / EVPI", pct(m.eficiencia), m.calificacion_eficiencia.upper()],
           ])]
    barra_len = 40
    llenos = int(round(min(max(m.eficiencia, 0), 1) * barra_len)) if m.eficiencia == m.eficiencia else 0
    txt += ["", f"      Eficiencia: [{'█' * llenos}{'░' * (barra_len - llenos)}] {pct(m.eficiencia)}"]
    txt.append("")
    txt.append(parrafo(
        f"Una eficiencia del {pct(m.eficiencia)} significa que el estudio solo captura esa "
        f"fracción del beneficio que aportaría saber con certeza el estado regulatorio. "
        f"La calificación es {m.calificacion_eficiencia.upper()}, por lo que "
        f"{'SÍ se recomienda' if m.recomienda_estudio else 'NO se recomienda'} contratarlo."))
    return "\n".join(txt)


def paso13(m: ModeloDecision) -> str:
    txt = [titulo_paso(13, "Decisión final del tomador de decisiones")]
    txt.append(marco("CONCLUSIÓN GERENCIAL", m.texto_decision_final(), doble=True))
    return "\n".join(txt)


def resumen_ejecutivo(m: ModeloDecision) -> str:
    filas = [
        ["Alternativa óptima (a priori)", f"{m.alt_optima_prior} · {m.nombre_alt[m.alt_optima_prior]}"],
        ["Valor esperado óptimo", dinero(m.ev_optimo_prior)],
        ["Criterio optimista", f"{m.criterio_optimista.elegida}"],
        ["Criterio conservador", f"{m.criterio_conservador.elegida}"],
        ["Criterio mínimo arrepentimiento", f"{m.criterio_arrepentimiento.elegida}"],
        ["Punto de corte", pct(m.umbral_decisorio.p) if m.umbral_decisorio else "—"],
        ["EVPI", dinero(m.evpi)],
        ["EVSI", dinero(m.evsi)],
        ["Eficiencia del estudio", f"{pct(m.eficiencia)} ({m.calificacion_eficiencia})"],
        ["¿Contratar el estudio?", "SÍ" if m.recomienda_estudio else "NO"],
    ]
    return "\n" + tabla(["Indicador", "Resultado"], filas, alinear_izq=1)