# -*- coding: utf-8 -*-
"""
=====================================================================
 TABLERO GRÁFICO DEL ESTUDIO
=====================================================================
Convierte el reporte de consola en una aplicación visual que se abre
en el navegador: navegación lateral por los 13 pasos, tarjetas,
tablas, indicadores y todas las figuras embebidas.

Los datos del problema son editables desde la propia interfaz: al
pulsar «Recalcular», el modelo se rehace y todo el tablero se
actualiza (gráficas, árboles y textos de conclusión incluidos).

Uso:
    python tablero.py            → abre la aplicación en el navegador
    python tablero.py --html     → genera tablero.html (archivo suelto)
    python tablero.py --puerto 9000
    python tablero.py --no-abrir

Solo usa la biblioteca estándar de Python + matplotlib.
=====================================================================
"""
from __future__ import annotations

import argparse
import base64
import copy
import html
import io
import json
import os
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import config as CFG
import config_Juegos as CJ
import graficas
import graficas_Juegos
from juegos import JuegoSumaCero
from modelo import ModeloDecision, dinero, num, pct


# =====================================================================
#  UTILIDADES
# =====================================================================
def esc(x) -> str:
    return html.escape(str(x))


def figura_b64(fig) -> str:
    """Convierte una figura de matplotlib en un PNG embebible."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=145, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def datos_editables(base=CFG) -> SimpleNamespace:
    """Copia editable de la configuración; el archivo original no se toca."""
    return SimpleNamespace(
        TITULO=base.TITULO, SUBTITULO=base.SUBTITULO, CURSO=base.CURSO,
        MARCO_LEGAL=base.MARCO_LEGAL, EQUIPO=copy.deepcopy(base.EQUIPO),
        MONEDA=base.MONEDA, FACTOR_MONEDA=base.FACTOR_MONEDA,
        UNIDAD_CORTA=base.UNIDAD_CORTA,
        ALTERNATIVAS=copy.deepcopy(base.ALTERNATIVAS),
        ESTADOS=copy.deepcopy(base.ESTADOS),
        MATRIZ_PAGOS=copy.deepcopy(base.MATRIZ_PAGOS),
        INDICADORES=copy.deepcopy(base.INDICADORES),
        VEROSIMILITUDES=copy.deepcopy(base.VEROSIMILITUDES),
        OBJETIVO=base.OBJETIVO, CARPETA_SALIDA=base.CARPETA_SALIDA,
        ANCHO_CONSOLA=base.ANCHO_CONSOLA,
    )


def datos_juego_editables(base=CJ) -> SimpleNamespace:
    """Copia editable de config_juegos.py; el archivo original no se toca."""
    return SimpleNamespace(
        TITULO_JUEGO=base.TITULO_JUEGO, SUBTITULO_JUEGO=base.SUBTITULO_JUEGO,
        CONTEXTO_JUEGO=base.CONTEXTO_JUEGO,
        JUGADOR_FILA=copy.deepcopy(base.JUGADOR_FILA),
        JUGADOR_COLUMNA=copy.deepcopy(base.JUGADOR_COLUMNA),
        ESTRATEGIAS_FILA=copy.deepcopy(base.ESTRATEGIAS_FILA),
        ESTRATEGIAS_COLUMNA=copy.deepcopy(base.ESTRATEGIAS_COLUMNA),
        MATRIZ_JUEGO=copy.deepcopy(base.MATRIZ_JUEGO),
        UNIDAD_JUEGO=base.UNIDAD_JUEGO,
        FACTOR_PROBABILIDAD=base.FACTOR_PROBABILIDAD,
    )


# =====================================================================
#  COMPONENTES HTML
# =====================================================================
def tarjeta(titulo: str, cuerpo: str, color: str = "azul", extra: str = "") -> str:
    cab = f'<h3 class="t-tit">{esc(titulo)}</h3>' if titulo else ""
    return (f'<section class="tarjeta {color} {extra}">{cab}'
            f'<div class="t-cuerpo">{cuerpo}</div></section>')


def tabla(columnas: list[str], filas: list[list], destacar: list[int] = None,
          alinear_izq: int = 1) -> str:
    destacar = destacar or []
    th = "".join(f'<th{" class=izq" if i < alinear_izq else ""}>{esc(c)}</th>'
                 for i, c in enumerate(columnas))
    trs = []
    for k, f in enumerate(filas):
        cls = ' class="destacada"' if k in destacar else ""
        tds = "".join(f'<td{" class=izq" if i < alinear_izq else ""}>{esc(v)}</td>'
                      for i, v in enumerate(f))
        trs.append(f"<tr{cls}>{tds}</tr>")
    return (f'<div class="tabla-env"><table><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>')


def kpis(items: list[tuple[str, str, str]]) -> str:
    cajas = "".join(
        f'<div class="kpi {c}"><span class="kpi-et">{esc(e)}</span>'
        f'<strong class="kpi-va">{esc(v)}</strong></div>' for e, v, c in items)
    return f'<div class="kpis">{cajas}</div>'


def formula(lineas: list[str]) -> str:
    return ('<pre class="formula">'
            + "\n".join(esc(l) for l in lineas) + "</pre>")


def parrafo(texto: str, clase: str = "") -> str:
    return f'<p class="{clase}">{esc(texto)}</p>'


def figura(fig, pie: str = "") -> str:
    b64 = figura_b64(fig)
    cap = f'<figcaption>{esc(pie)}</figcaption>' if pie else ""
    return (f'<figure class="figura"><img src="data:image/png;base64,{b64}" '
            f'alt="{esc(pie)}">{cap}</figure>')


# =====================================================================
#  CONSTRUCCIÓN DE LAS SECCIONES
# =====================================================================
SECCIONES = [
    ("contexto", "Contexto del estudio", "◆"),
    ("datos", "Datos del problema", "⚙"),
    ("paso1", "1 · Matriz de pagos", "1"),
    ("paso2", "2 · Criterios bajo incertidumbre", "2"),
    ("paso3", "3 · Valor esperado a priori", "3"),
    ("paso4", "4 · Análisis de sensibilidad", "4"),
    ("paso5", "5 · Análisis gráfico", "5"),
    ("paso6", "6 · Puntos de corte", "6"),
    ("paso7", "7 · Información perfecta (EVPI)", "7"),
    ("paso8", "8 · Información muestral", "8"),
    ("paso9", "9 · Teorema de Bayes", "9"),
    ("paso10", "10 · Árboles de decisión", "10"),
    ("paso11", "11 · Valor de la información", "11"),
    ("paso12", "12 · Eficiencia del estudio", "12"),
    ("paso13", "13 · Decisión final", "13"),
    ("jt_contexto", "Teoría de Juegos — contexto", "◈"),
    ("jt1", "J1 · Matriz y punto de silla", "J1"),
    ("jt2", "J2 · Eliminación por dominancia", "J2"),
    ("jt3", "J3 · Matriz de probabilidades", "J3"),
    ("jt4", "J4 · Solución algebraica", "J4"),
    ("jt5", "J5 · Análisis gráfico", "J5"),
    ("jt6", "J6 · Estrategias y valor del juego", "J6"),
]


class Tablero:
    """Genera el HTML completo del estudio a partir del modelo."""

    def __init__(self, modelo: ModeloDecision, juego: JuegoSumaCero,
                 interactivo: bool = True):
        self.m = modelo
        self.d = modelo.cfg
        self.j = juego
        self.interactivo = interactivo

    # -----------------------------------------------------------------
    def html(self) -> str:
        secciones = "".join([
            self.sec_contexto(), self.sec_datos(), self.sec1(), self.sec2(),
            self.sec3(), self.sec4(), self.sec5(), self.sec6(), self.sec7(),
            self.sec8(), self.sec9(), self.sec10(), self.sec11(), self.sec12(),
            self.sec13(),
            self.jsec_contexto(), self.jsec1(), self.jsec2(), self.jsec3(),
            self.jsec4(), self.jsec5(), self.jsec6(),
        ])
        m = self.m
        nav = "".join(
            f'<a class="nav-it" data-ir="{k}"><span class="nav-ic">{esc(ic)}</span>'
            f'<span>{esc(t)}</span></a>' for k, t, ic in SECCIONES)
        resumen = (f'Óptima: <b>{esc(m.alt_optima_prior)}</b> · '
                   f'{esc(dinero(m.ev_optimo_prior))} &nbsp;|&nbsp; '
                   f'Corte: <b>{esc(pct(m.umbral_decisorio.p)) if m.umbral_decisorio else "—"}</b>'
                   f' &nbsp;|&nbsp; Eficiencia: <b>{esc(pct(m.eficiencia))}</b>'
                   f' &nbsp;|&nbsp; Valor del juego: '
                   f'<b>{esc(num(self.j.valor_juego, 2))}</b>')
        return PLANTILLA.format(
            titulo=esc(self.d.TITULO), subtitulo=esc(self.d.SUBTITULO),
            curso=esc(self.d.CURSO), nav=nav, secciones=secciones,
            resumen=resumen, css=CSS, js=JS)

    # =================================================================
    def sec_contexto(self) -> str:
        m, d = self.m, self.d
        fuentes = ", ".join(x["nombre"] for x in d.EQUIPO if x.get("fuente")) \
            or "un integrante del equipo"

        portada = (
            f'<div class="portada"><h1>{esc(d.TITULO)}</h1>'
            f'<p class="sub">{esc(d.SUBTITULO)}</p>'
            f'<p class="meta">{esc(d.CURSO)} &nbsp;·&nbsp; {esc(d.MARCO_LEGAL)}</p></div>')

        alts = "".join(
            f'<li><b>{esc(a["id"])} — {esc(a["nombre"])}</b>: {esc(a["descripcion"])}.</li>'
            for a in d.ALTERNATIVAS)
        c1 = tarjeta("¿Qué decisión se está tomando?",
                     parrafo("La empresa debe escoger UNA de estas alternativas para "
                             "la operación de los sábados:")
                     + f"<ul>{alts}</ul>", "azul")

        ests = "".join(
            f'<li><b>{esc(e["id"])} — {esc(e["nombre"])}</b> ({esc(pct(e["prior"], 0))}): '
            f'{esc(e["descripcion"])}.</li>' for e in d.ESTADOS)
        c2 = tarjeta("¿Qué no controla la empresa?",
                     parrafo("El resultado económico depende del estado regulatorio, "
                             "un factor externo a la empresa:")
                     + f"<ul>{ests}</ul>", "morado")

        objetivos = "".join(f"<li>{esc(t)}</li>" for t in [
            "Determinar la alternativa que maximiza la utilidad esperada.",
            "Medir qué tan estable es esa decisión si cambian las probabilidades "
            "(análisis de sensibilidad y punto de corte).",
            "Calcular cuánto valdría eliminar por completo la incertidumbre (EVPI).",
            "Evaluar, con el Teorema de Bayes, si una consultoría jurídica previa "
            "cambiaría la decisión (EVSI).",
            "Concluir con cifras si conviene o no pagar esa consultoría."])
        c3 = tarjeta("¿Qué se busca con este estudio?", f"<ol>{objetivos}</ol>", "verde")

        c4 = tarjeta(
            "Los datos no son inventados",
            parrafo(f"{fuentes} hace parte de este equipo de trabajo y labora "
                    f"actualmente en la empresa de transporte intermunicipal "
                    f"analizada. Gracias a ello cuenta con acceso directo y "
                    f"autorizado a la información operativa real de la ruta: "
                    f"utilidades por despacho, niveles de ocupación de los sábados y "
                    f"condiciones regulatorias vigentes.")
            + parrafo("Las cifras de la matriz de pagos provienen de esa fuente "
                      "primaria, no de supuestos académicos. Por eso las conclusiones "
                      "de este modelo son directamente aplicables a la operación real "
                      "de la empresa."), "ambar", "destacada")

        c5 = tarjeta("Matriz de pagos — punto de partida de todo el modelo",
                     self._tabla_pagos()
                     + parrafo(f"Todos los valores están expresados en "
                               f"{d.UNIDAD_CORTA} de utilidad operativa por jornada de "
                               f"sábado. A partir únicamente de esta matriz y de las "
                               f"probabilidades mostradas se calculan los 13 pasos.",
                               "suave"), "rojo")

        return self._envolver("contexto", "Contexto del estudio",
                              portada + '<div class="rejilla">' + c1 + c2 + c3 + c4
                              + "</div>" + c5)

    def _tabla_pagos(self) -> str:
        m = self.m
        cols = ["Alternativa"] + [f"{s} · {m.nombre_est[s]}" for s in m.ids_est]
        filas = [[f"{a} · {m.nombre_alt[a]}"]
                 + [dinero(m.pagos[a][s]) for s in m.ids_est] for a in m.ids_alt]
        filas.append(["Probabilidad a priori"] + [num(m.prior[s]) for s in m.ids_est])
        return tabla(cols, filas)

    # =================================================================
    def sec_datos(self) -> str:
        m = self.m
        if not self.interactivo:
            cuerpo = tarjeta("Modo archivo",
                             parrafo("Este tablero fue exportado como archivo suelto, "
                                     "por lo que los datos no son editables aquí. "
                                     "Ejecuta «python tablero.py» para la versión "
                                     "interactiva."), "ambar")
            return self._envolver("datos", "Datos del problema", cuerpo)

        f_pagos = ""
        for a in m.ids_alt:
            celdas = "".join(
                f'<td><input name="pago_{esc(a)}_{esc(s)}" value="{m.pagos[a][s]}" '
                f'inputmode="decimal"></td>' for s in m.ids_est)
            f_pagos += (f'<tr><td class="izq">{esc(a)} · {esc(m.nombre_alt[a])}</td>'
                        f'{celdas}</tr>')
        enc_pagos = "".join(f"<th>{esc(s)} · {esc(m.nombre_est[s])}</th>"
                            for s in m.ids_est)

        f_prior = "".join(
            f'<tr><td class="izq">P({esc(s)}) — {esc(m.nombre_est[s])}</td>'
            f'<td><input name="prior_{esc(s)}" value="{m.prior[s]}" '
            f'inputmode="decimal"></td></tr>' for s in m.ids_est)

        f_ver = ""
        for ind in m.ids_ind:
            celdas = "".join(
                f'<td><input name="ver_{esc(ind)}_{esc(s)}" '
                f'value="{m.verosimilitud[ind][s]}" inputmode="decimal"></td>'
                for s in m.ids_est)
            f_ver += (f'<tr><td class="izq">{esc(ind)} · {esc(m.nombre_ind[ind])}</td>'
                      f'{celdas}</tr>')
        enc_ver = "".join(f"<th>P( · | {esc(s)})</th>" for s in m.ids_est)

        deslizador = ""
        if len(m.ids_est) == 2:
            s1 = m.ids_est[0]
            deslizador = (
                f'<div class="deslizador"><label>Explorar P({esc(s1)}) rápidamente'
                f'</label><input type="range" id="rango" min="0" max="1" step="0.01" '
                f'value="{m.prior[s1]}"><div id="rango-txt" class="suave"></div></div>')

        j = self.j
        f_juego = ""
        for a in j.ids_f:
            celdas = "".join(
                f'<td><input name="jpago_{esc(a)}_{esc(c)}" '
                f'value="{j.pagos[a][c]}" inputmode="decimal"></td>' for c in j.ids_c)
            f_juego += (f'<tr><td class="izq">{esc(a)} · {esc(j.nombre_f[a])}</td>'
                        f'{celdas}</tr>')
        enc_juego = "".join(f"<th>{esc(c)} · {esc(j.nombre_c[c])}</th>"
                            for c in j.ids_c)

        formulario = (
            f'<form method="post" action="/recalcular" id="frm">'
            f'<h4>Matriz de pagos ({esc(self.d.UNIDAD_CORTA)})</h4>'
            f'<div class="tabla-env"><table><thead><tr><th class="izq">Alternativa</th>'
            f'{enc_pagos}</tr></thead><tbody>{f_pagos}</tbody></table></div>'
            f'<h4>Probabilidades a priori</h4>'
            f'<div class="tabla-env"><table><thead><tr><th class="izq">Estado</th>'
            f'<th>Probabilidad</th></tr></thead><tbody>{f_prior}</tbody></table></div>'
            f'{deslizador}'
            f'<h4>Confiabilidad del estudio — P(indicador | estado)</h4>'
            f'<div class="tabla-env"><table><thead><tr><th class="izq">Indicador</th>'
            f'{enc_ver}</tr></thead><tbody>{f_ver}</tbody></table></div>'
            f'<h4>Teoría de juegos — matriz de pagos ({esc(j.unidad)})</h4>'
            f'<div class="tabla-env"><table><thead><tr>'
            f'<th class="izq">Jugador I \\ II</th>{enc_juego}</tr></thead>'
            f'<tbody>{f_juego}</tbody></table></div>'
            f'<div class="acciones">'
            f'<button class="btn verde" type="submit">↻ Recalcular todo el estudio</button>'
            f'<button class="btn gris" type="submit" formaction="/restaurar">'
            f'⟲ Restaurar valores originales</button>'
            f'<a class="btn azul" href="/exportar">⤓ Exportar informe y figuras</a>'
            f'</div></form>')

        cuerpo = tarjeta(
            "Datos del problema — editables en vivo",
            parrafo("Toda la aplicación se alimenta únicamente de estos valores. "
                    "Al recalcular, los 13 pasos, las gráficas, los árboles y los "
                    "textos de conclusión se rehacen automáticamente.", "suave")
            + formulario, "ambar")
        return self._envolver("datos", "Datos del problema", cuerpo)

    # =================================================================
    def sec1(self) -> str:
        m = self.m
        c = tarjeta("Matriz de pagos",
                    parrafo(f"Utilidad operativa del sábado para cada combinación de "
                            f"decisión y estado regulatorio, en "
                            f"{self.d.UNIDAD_CORTA}.", "suave")
                    + self._tabla_pagos()
                    + parrafo(f"Suma de probabilidades = {num(sum(m.prior.values()))} ✔"
                              f"   ·   Objetivo: "
                              f"{'MAXIMIZAR utilidad' if m.objetivo == 'max' else 'MINIMIZAR costo'}",
                              "ok"), "rojo")
        c += tarjeta("", figura(graficas.figura_matriz_criterios(m, None)), "azul")
        return self._envolver("paso1", "Paso 1 · Matriz de pagos", c)

    def sec2(self) -> str:
        m = self.m
        out = ""
        colores = {"Optimista": "azul", "Conservador": "rojo"}
        for c in m.criterios:
            color = colores.get(c.nombre.split()[0], "verde")
            filas = [[f"{a} · {m.nombre_alt[a]}", num(c.valores[a], 0),
                      "◄ ELEGIDA" if a == c.elegida else ""] for a in m.ids_alt]
            out += tarjeta(
                c.nombre,
                parrafo(c.descripcion, "suave")
                + tabla(["Alternativa", "Valor del criterio", ""], filas,
                        [m.ids_alt.index(c.elegida)])
                + parrafo(f"Decisión por este criterio: {c.elegida} — "
                          f"{m.nombre_alt[c.elegida]} (valor {num(c.valor_elegido, 0)})",
                          "ok"), color)

        cols = ["Alternativa"] + [m.nombre_est[s] for s in m.ids_est] + \
               ["Máximo arrepentimiento"]
        filas = [[f"{a} · {m.nombre_alt[a]}"]
                 + [num(m.matriz_arrepentimiento[a][s], 0) for s in m.ids_est]
                 + [num(max(m.matriz_arrepentimiento[a].values()), 0)]
                 for a in m.ids_alt]
        out += tarjeta("Matriz de arrepentimiento", tabla(cols, filas), "morado")

        coinciden = len({c.elegida for c in m.criterios}) == 1
        texto = ("Los tres criterios coinciden en la misma alternativa, lo que refuerza "
                 "la robustez de la decisión." if coinciden else
                 "Los criterios no coinciden entre sí: "
                 + "; ".join(f"{c.nombre.split('(')[0].strip()} → {c.elegida}"
                             for c in m.criterios)
                 + ". Es esperable, porque cada criterio refleja una actitud distinta "
                   "frente al riesgo. Por eso el estudio continúa incorporando las "
                   "probabilidades, que sí permiten una decisión fundamentada.")
        out += tarjeta("Lectura", parrafo(texto), "verde" if coinciden else "ambar")
        return self._envolver("paso2", "Paso 2 · Criterios bajo incertidumbre", out)

    def sec3(self) -> str:
        m = self.m
        filas = [[f"{a} · {m.nombre_alt[a]}", num(m.ev_prior[a]), dinero(m.ev_prior[a]),
                  "◄ ÓPTIMA" if a == m.alt_optima_prior else ""] for a in m.ids_alt]
        segundo = sorted(m.ev_prior.values())[-2] if len(m.ids_alt) > 1 else None
        c = tarjeta(
            "Valor esperado con las probabilidades a priori",
            parrafo("Se pondera cada pago por la probabilidad de su estado: "
                    "EV(d) = Σ P(s) · pago(d, s)", "suave")
            + formula([m.desarrollo_ev[a] for a in m.ids_alt])
            + tabla(["Alternativa", "Valor esperado", "Equivalente", ""], filas,
                    [m.ids_alt.index(m.alt_optima_prior)]), "azul")
        c += tarjeta("Decisión con la información disponible", kpis([
            ("Alternativa óptima",
             f"{m.alt_optima_prior} · {m.nombre_alt[m.alt_optima_prior]}", "verde"),
            ("Valor esperado", dinero(m.ev_optimo_prior), "verde"),
            ("Ventaja sobre la siguiente",
             dinero(abs(m.ev_optimo_prior - segundo)) if segundo is not None else "—",
             "azul")]), "verde")
        return self._envolver("paso3", "Paso 3 · Valor esperado a priori", c)

    def sec4(self) -> str:
        m = self.m
        if len(m.ids_est) != 2:
            return self._envolver("paso4", "Paso 4 · Análisis de sensibilidad",
                                  tarjeta("No aplica", parrafo(
                                      "Requiere exactamente 2 estados."), "ambar"))
        s1, s2 = m.ids_est
        ecs = "".join(f'<h4>{esc(a)} · {esc(m.nombre_alt[a])}</h4>'
                      + formula(m.rectas[a]["pasos"]) for a in m.ids_alt)
        c = tarjeta("Se somete a cambio la probabilidad",
                    parrafo(f"Se hace variar P({s1}) = p (por lo tanto P({s2}) = 1 − p) "
                            f"y se observa cómo se comporta la decisión en todo su "
                            f"recorrido.", "suave") + ecs, "azul")

        escenarios = sorted(set([x / 10 for x in range(11)] + [m.prior[s1]]
                                + [k.p for k in m.cortes_validos]))
        filas, destacar = [], []
        for k, pp in enumerate(escenarios):
            e = m.escenario(pp)
            etiqueta = ("INDIFERENTE (" + " = ".join(e["empatadas"]) + ")"
                        if e["empate"] else
                        f"{e['elegida']} · {m.nombre_alt[e['elegida']]}")
            if e["empate"] or abs(pp - m.prior[s1]) < 1e-12:
                destacar.append(k)
            filas.append([pct(pp, 2 if e["empate"] else 0)]
                         + [num(e["ev"][a]) for a in m.ids_alt]
                         + [etiqueta, num(e["valor"])])
        c += tarjeta("Comportamiento de la decisión",
                     tabla([f"P({s1})"] + [f"EV({a})" for a in m.ids_alt]
                           + ["Decisión óptima", "Valor"], filas, destacar), "morado")

        tramos = "".join(
            f'<li>Si {esc(pct(t.p_ini, 2))} ≤ P({esc(s1)}) ≤ {esc(pct(t.p_fin, 2))} → '
            f'la decisión óptima es <b>{esc(t.dominante)} · '
            f'{esc(m.nombre_alt[t.dominante])}</b></li>' for t in m.tramos)
        c += tarjeta("Tramos de dominancia", f"<ul>{tramos}</ul>", "verde")
        return self._envolver("paso4", "Paso 4 · Análisis de sensibilidad", c)

    def sec5(self) -> str:
        m = self.m
        if len(m.ids_est) != 2:
            return self._envolver("paso5", "Paso 5 · Análisis gráfico",
                                  tarjeta("No aplica", parrafo(
                                      "Requiere exactamente 2 estados."), "ambar"))
        filas = [[a, m.rectas[a]["ecuacion"],
                  f"(0 , {num(m.rectas[a]['punto_p0'][1], 0)})",
                  f"(1 , {num(m.rectas[a]['punto_p1'][1], 0)})"] for a in m.ids_alt]
        c = tarjeta("Rectas del modelo",
                    parrafo("Cada alternativa es una recta EV(d) = m·p + b sobre el "
                            "eje p = P(s1) ∈ [0, 1]. Con dos puntos por recta basta "
                            "para graficarla.", "suave")
                    + tabla(["Alternativa", "Ecuación", "Punto p = 0", "Punto p = 1"],
                            filas, alinear_izq=2), "azul")
        c += tarjeta("", figura(graficas.figura_sensibilidad(m, None)), "azul")
        return self._envolver("paso5", "Paso 5 · Análisis gráfico", c)

    def sec6(self) -> str:
        m = self.m
        c = ""
        for k in m.cortes:
            cuerpo = formula(k.algebra)
            if k.valido:
                cuerpo += kpis([("Punto de corte", pct(k.p), "ambar"),
                                ("Valor esperado común", dinero(k.valor), "azul")])
            else:
                cuerpo += parrafo("El corte cae fuera del intervalo [0, 1]: una "
                                  "alternativa domina a la otra en todo el recorrido.",
                                  "aviso")
            c += tarjeta(f"Igualación  {k.a} = {k.b}", cuerpo,
                         "verde" if k.valido else "ambar")
        u = m.umbral_decisorio
        if u:
            p1 = m.prior[m.ids_est[0]]
            otra = u.b if u.a == m.alt_optima_prior else u.a
            estable = abs(p1 - u.p) > 0.10
            c += tarjeta(
                "Interpretación del umbral",
                parrafo(f"P({m.ids_est[0]}) debe "
                        f"{'superar' if p1 < u.p else 'caer por debajo de'} {pct(u.p)} "
                        f"para que convenga cambiar a {otra} · {m.nombre_alt[otra]}.")
                + kpis([("Valor actual estimado", pct(p1, 0), "azul"),
                        ("Umbral de cambio", pct(u.p), "ambar"),
                        ("Margen", f"{num(abs(p1 - u.p) * 100)} p.p.",
                         "verde" if estable else "rojo"),
                        ("Decisión", "ESTABLE" if estable else "SENSIBLE",
                         "verde" if estable else "rojo")]),
                "verde" if estable else "ambar")
        return self._envolver("paso6", "Paso 6 · Puntos de corte", c)

    def sec7(self) -> str:
        m = self.m
        filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
                  f"{m.mejor_decision_por_estado[s]} · "
                  f"{m.nombre_alt[m.mejor_decision_por_estado[s]]}",
                  dinero(m.mejor_por_estado[s])] for s in m.ids_est]
        c = tarjeta(
            "Valor esperado de la información perfecta",
            parrafo("Si se supiera con certeza qué estado va a ocurrir, se elegiría la "
                    "mejor alternativa en cada caso.", "suave")
            + tabla(["Estado", "Probabilidad", "Mejor decisión si ocurre", "Pago"],
                    filas)
            + formula(m.desarrollo_evpi)
            + kpis([("EV con información perfecta", dinero(m.ev_con_info_perfecta),
                     "verde"),
                    ("EV de la decisión actual", dinero(m.ev_optimo_prior), "azul"),
                    ("EVPI", dinero(m.evpi), "ambar")]), "verde")
        c += tarjeta("Lectura gerencial",
                     parrafo(f"El EVPI de {dinero(m.evpi)} es el máximo que la empresa "
                             f"debería pagar por eliminar por completo la "
                             f"incertidumbre regulatoria. Ningún estudio, consultoría "
                             f"o asesoría puede valer más que esta cifra."), "ambar")
        return self._envolver("paso7", "Paso 7 · Información perfecta (EVPI)", c)

    def sec8(self) -> str:
        m = self.m
        cols = ["Indicador"] + [f"P( · | {s})" for s in m.ids_est]
        filas = [[f"{i} · {m.nombre_ind[i]}"]
                 + [num(m.verosimilitud[i][s]) for s in m.ids_est] for i in m.ids_ind]
        filas.append(["Suma por columna"]
                     + [num(sum(m.verosimilitud[i][s] for i in m.ids_ind))
                        for s in m.ids_est])
        c = tarjeta("Confiabilidad del estudio",
                    parrafo("Antes de decidir se puede contratar una consultoría cuyo "
                            "concepto es un indicador imperfecto del estado real. Su "
                            "confiabilidad se expresa como P(indicador | estado).",
                            "suave") + tabla(cols, filas), "azul")
        lineas = []
        for r in m.ramas:
            det = " + ".join(f"{num(m.verosimilitud[r.indicador][s])}·{num(m.prior[s])}"
                             for s in m.ids_est)
            lineas.append(f"P({r.indicador}) = {det} = {num(r.prob_indicador, 4)}")
        lineas.append(f"Suma = {num(sum(r.prob_indicador for r in m.ramas), 4)}  ✔")
        c += tarjeta("Probabilidades marginales de cada resultado", formula(lineas),
                     "morado")
        return self._envolver("paso8", "Paso 8 · Información muestral", c)

    def sec9(self) -> str:
        m = self.m
        c = tarjeta("Teorema de Bayes",
                    formula(["P(s | indicador) = [ P(indicador | s) · P(s) ] / P(indicador)"]),
                    "azul")
        for r in m.ramas:
            cambia = r.elegida != m.alt_optima_prior
            filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
                      num(m.verosimilitud[r.indicador][s]), num(r.conjuntas[s], 4),
                      num(r.posteriores[s], 4), pct(r.posteriores[s])]
                     for s in m.ids_est]
            filas.append(["Total", num(sum(m.prior.values())), "—",
                          num(r.prob_indicador, 4),
                          num(sum(r.posteriores.values()), 4), "100,00%"])
            lineas = []
            for a in m.ids_alt:
                det = " + ".join(f"{num(r.posteriores[s], 4)}·({num(m.pagos[a][s], 0)})"
                                 for s in m.ids_est)
                lineas.append(f"EV({a}|{r.indicador}) = {det} = {num(r.ev[a])}"
                              + ("   ◄ ÓPTIMA" if a == r.elegida else ""))
            c += tarjeta(
                f"Resultado {r.nombre} ({r.indicador}) · "
                f"P({r.indicador}) = {num(r.prob_indicador, 4)}",
                tabla(["Estado", "P(s) previa", f"P({r.indicador}|s)", "Conjunta",
                       "P(s | ind.)", "%"], filas)
                + formula(lineas)
                + parrafo(f"Si el estudio resulta {r.nombre}, la decisión "
                          f"{'CAMBIA a' if cambia else 'se RATIFICA en'} {r.elegida} · "
                          f"{m.nombre_alt[r.elegida]} con {dinero(r.valor)}.",
                          "aviso" if cambia else "ok"),
                "rojo" if cambia else "verde")
        c += tarjeta("", figura(graficas.figura_bayes(m, None)), "azul")
        return self._envolver("paso9", "Paso 9 · Teorema de Bayes", c)

    def sec10(self) -> str:
        m = self.m
        c = tarjeta(
            "Árboles de decisión",
            parrafo("Los nodos cuadrados son decisiones (las controla la empresa) y "
                    "los circulares son nodos de azar (los controla el entorno "
                    "regulatorio). La resolución es por inducción hacia atrás: se "
                    "promedia en los nodos de azar y se optimiza en los de decisión.",
                    "suave")
            + kpis([("Raíz del árbol sin estudio", dinero(m.ev_optimo_prior), "azul"),
                    ("Raíz del árbol con estudio", dinero(m.ev_con_info_muestral),
                     "verde")]), "azul")
        c += tarjeta("", figura(graficas.figura_arbol_prior(m, None)), "azul")
        c += tarjeta("", figura(graficas.figura_arbol_muestral(m, None)), "verde")
        return self._envolver("paso10", "Paso 10 · Árboles de decisión", c)

    def sec11(self) -> str:
        m = self.m
        filas = [[f"{r.indicador} · {r.nombre}", num(r.prob_indicador, 4),
                  f"{r.elegida} · {m.nombre_alt[r.elegida]}", num(r.valor),
                  num(r.prob_indicador * r.valor)] for r in m.ramas]
        c = tarjeta(
            "Valor esperado de la información muestral",
            tabla(["Resultado del estudio", "P(resultado)", "Decisión óptima",
                   "Valor esperado", "Aporte ponderado"], filas)
            + formula(m.desarrollo_evsi[:2])
            + kpis([("EV sin información muestral", dinero(m.ev_sin_info_muestral),
                     "gris"),
                    ("EV con información muestral", dinero(m.ev_con_info_muestral),
                     "azul"),
                    ("EVSI", dinero(m.evsi), "verde")])
            + parrafo(f"Contratar la consultoría solo tiene sentido si su honorario es "
                      f"inferior a {dinero(m.evsi)}.", "aviso"), "azul")
        return self._envolver("paso11", "Paso 11 · Valor de la información", c)

    def sec12(self) -> str:
        m = self.m
        frac = min(max(m.eficiencia, 0), 1) if m.eficiencia == m.eficiencia else 0
        clase = "rojo" if frac < 0.2 else ("ambar" if frac < 0.5 else "verde")
        barra = (f'<div class="barra"><div class="barra-in {clase}" '
                 f'style="width:{frac * 100:.2f}%"></div>'
                 f'<span class="barra-tx">{esc(pct(m.eficiencia))} · '
                 f'{esc(m.calificacion_eficiencia.upper())}</span></div>')
        rec = m.recomienda_estudio
        c = tarjeta(
            "Eficiencia del estudio de mercado",
            formula([m.desarrollo_evsi[2]])
            + tabla(["Concepto", "Valor", "Equivalente"], [
                ["EVSI — información muestral (imperfecta)", num(m.evsi),
                 dinero(m.evsi)],
                ["EVPI — información perfecta", num(m.evpi), dinero(m.evpi)],
                ["Eficiencia = EVSI / EVPI", pct(m.eficiencia),
                 m.calificacion_eficiencia.upper()]])
            + barra, "verde")
        c += tarjeta("Lectura",
                     parrafo(f"Una eficiencia del {pct(m.eficiencia)} significa que el "
                             f"estudio solo captura esa fracción del beneficio que "
                             f"aportaría saber con certeza el estado regulatorio. La "
                             f"calificación es {m.calificacion_eficiencia.upper()}, "
                             f"por lo que {'SÍ se recomienda' if rec else 'NO se recomienda'} "
                             f"contratarlo.", "ok" if rec else "aviso"),
                     "verde" if rec else "rojo")
        return self._envolver("paso12", "Paso 12 · Eficiencia del estudio", c)

    def sec13(self) -> str:
        m = self.m
        rec = m.recomienda_estudio
        c = tarjeta("Resumen ejecutivo",
                    kpis([("Alternativa seleccionada",
                           f"{m.alt_optima_prior} · {m.nombre_alt[m.alt_optima_prior]}",
                           "verde"),
                          ("Utilidad esperada", dinero(m.ev_optimo_prior), "verde"),
                          ("¿Contratar consultoría?", "SÍ" if rec else "NO",
                           "verde" if rec else "rojo")])
                    + kpis([("Umbral de cambio",
                             pct(m.umbral_decisorio.p) if m.umbral_decisorio else "—",
                             "ambar"),
                            ("EVPI", dinero(m.evpi), "azul"),
                            ("EVSI", dinero(m.evsi), "azul"),
                            ("Eficiencia", pct(m.eficiencia), "morado")]), "azul")
        colores = ["azul", "morado", "verde", "ambar", "rojo", "azul"]
        for k, texto in enumerate(m.texto_decision_final()):
            titulo, _, cuerpo = texto.partition(". ")
            c += tarjeta(titulo if len(titulo) < 70 else "",
                         parrafo(cuerpo or texto), colores[k % len(colores)])
        c += tarjeta("", figura(graficas.figura_resumen(m, None)), "verde")
        return self._envolver("paso13", "Paso 13 · Decisión final", c)


    # =================================================================
    #  SECCIONES DE TEORÍA DE JUEGOS
    # =================================================================
    def jsec_contexto(self) -> str:
        j = self.j
        cfg = j.cfg
        portada = (f'<div class="portada"><h1>{esc(cfg.TITULO_JUEGO)}</h1>'
                   f'<p class="sub">{esc(cfg.SUBTITULO_JUEGO)}</p>'
                   f'<p class="meta">Segunda parte del estudio · el rival ahora '
                   f'responde</p></div>')

        c = tarjeta("¿Por qué un segundo modelo?",
                    parrafo(cfg.CONTEXTO_JUEGO), "azul")

        jug = (f'<li><b>Jugador I — {esc(cfg.JUGADOR_FILA["nombre"])}</b>: '
               f'{esc(cfg.JUGADOR_FILA["descripcion"])}</li>'
               f'<li><b>Jugador II — {esc(cfg.JUGADOR_COLUMNA["nombre"])}</b>: '
               f'{esc(cfg.JUGADOR_COLUMNA["descripcion"])}</li>')
        c += tarjeta("Los jugadores", f"<ul>{jug}</ul>", "morado")

        ef = "".join(f'<li><b>{esc(e["id"])} — {esc(e["nombre"])}</b>: '
                     f'{esc(e["descripcion"])}.</li>' for e in cfg.ESTRATEGIAS_FILA)
        ec = "".join(f'<li><b>{esc(e["id"])} — {esc(e["nombre"])}</b>: '
                     f'{esc(e["descripcion"])}.</li>' for e in cfg.ESTRATEGIAS_COLUMNA)
        c += ('<div class="rejilla">'
              + tarjeta(f"Estrategias de {cfg.JUGADOR_FILA['nombre']} (filas)",
                        f"<ul>{ef}</ul>", "verde")
              + tarjeta(f"Estrategias de {cfg.JUGADOR_COLUMNA['nombre']} (columnas)",
                        f"<ul>{ec}</ul>", "rojo")
              + "</div>")

        c += tarjeta("Cómo leer la matriz",
                     parrafo(f"Cada celda es el {cfg.UNIDAD_JUEGO} que capta el "
                             f"jugador I; el complemento hasta {num(j.factor, 0)} lo "
                             f"capta el jugador II. Por eso es un juego de suma cero: "
                             f"lo que gana uno es exactamente lo que pierde el otro.")
                     + parrafo("El procedimiento es el visto en clase: punto de silla; "
                               "si no lo hay, eliminación por dominancia (primero "
                               "filas, luego columnas); conversión a matriz de "
                               "probabilidades; igualar y resolver para p; y por "
                               "último el análisis gráfico.", "suave"), "ambar")
        return self._envolver("jt_contexto", "Teoría de Juegos — contexto",
                              portada + c)

    def _tabla_juego(self, con_margenes: bool = True) -> str:
        j = self.j
        cols = ["Jugador I \\ II"] + [f"{c} · {j.nombre_c[c]}" for c in j.ids_c]
        if con_margenes:
            cols += ["Mín. fila"]
        filas = []
        for f in j.ids_f:
            fila = [f"{f} · {j.nombre_f[f]}"] + [num(j.pagos[f][c], 0) for c in j.ids_c]
            if con_margenes:
                fila += [num(j.min_fila[f], 0)]
            filas.append(fila)
        if con_margenes:
            filas.append(["Máx. columna"] + [num(j.max_col[c], 0) for c in j.ids_c]
                         + [""])
        return tabla(cols, filas)

    def jsec1(self) -> str:
        j = self.j
        c = tarjeta("Matriz de pagos del juego",
                    parrafo(f"Valores en {j.unidad} para el jugador I. La última "
                            f"columna es el mínimo de cada fila y la última línea el "
                            f"máximo de cada columna.", "suave")
                    + self._tabla_juego(), "rojo")

        if j.hay_silla:
            f, cc, v = j.sillas[0]
            cuerpo = (formula([f"Maximin = máx(mín. fila) = {num(j.maximin, 0)}",
                               f"Minimax = mín(máx. columna) = {num(j.minimax, 0)}",
                               f"Maximin = Minimax  →  hay punto de silla"])
                      + kpis([("Punto de silla", f"({f}, {cc})", "verde"),
                              ("Valor del juego", f"{num(v, 0)} {j.unidad}", "verde"),
                              ("Tipo de solución", "Estrategias puras", "azul")])
                      + parrafo(f"El jugador I juega siempre {f} y el jugador II "
                                f"siempre {cc}. Ninguno gana desviándose: el "
                                f"equilibrio es estable y el juego termina aquí.",
                                "ok"))
            color = "verde"
        else:
            cuerpo = (formula([f"Maximin = máx(mín. fila) = {num(j.maximin, 0)}   "
                               f"(fila {j.fila_maximin})",
                               f"Minimax = mín(máx. columna) = {num(j.minimax, 0)}   "
                               f"(columna {j.col_minimax})",
                               f"{num(j.maximin, 0)} ≠ {num(j.minimax, 0)}  →  "
                               f"NO hay punto de silla"])
                      + kpis([("Maximin", num(j.maximin, 0), "rojo"),
                              ("Minimax", num(j.minimax, 0), "azul"),
                              ("Punto de silla", "NO EXISTE", "ambar")])
                      + parrafo("Sin punto de silla no hay solución en estrategias "
                                "puras: si un jugador se fija en una sola estrategia, "
                                "el otro siempre encuentra cómo aprovecharlo. Se "
                                "continúa con la eliminación por dominancia.",
                                "aviso"))
            color = "ambar"
        c += tarjeta("Prueba del punto de silla", cuerpo, color)
        c += tarjeta("", figura(graficas_Juegos.figura_matriz_juego(j, None)), "azul")
        return self._envolver("jt1", "Juegos · Paso 1 — Matriz y punto de silla", c)

    def jsec2(self) -> str:
        j = self.j
        if not j.pasos:
            return self._envolver(
                "jt2", "Juegos · Paso 2 — Eliminación por dominancia",
                tarjeta("No se requiere",
                        parrafo("El juego quedó resuelto con el punto de silla, así "
                                "que no hace falta eliminar filas ni columnas."),
                        "verde"))
        c = tarjeta(
            "Regla de eliminación",
            parrafo("Se empieza por las filas y luego se pasa a las columnas, de "
                    "forma iterativa hasta dejar una matriz 2×2.")
            + "<ul><li><b>Filas</b>: el jugador I maximiza, así que la fila con "
              "mayores pagos elimina a la de menores.</li>"
              "<li><b>Columnas</b>: el jugador II minimiza lo que gana el jugador I, "
              "así que la columna con menores pagos elimina a la de mayores.</li></ul>"
            + parrafo("Los valores que sobreviven conservan siempre su posición "
                      "original dentro de la matriz.", "suave"), "azul")

        for p in j.pasos:
            nombre = (j.nombre_f if p.tipo == "fila" else j.nombre_c)
            cuerpo = (parrafo(p.explicacion)
                      + formula(p.comparacion)
                      + self._matriz_paso(p))
            c += tarjeta(f"Paso {p.orden} · {p.tipo.upper()} — {p.dominante} elimina "
                         f"a {p.eliminada} ({nombre[p.eliminada]})", cuerpo,
                         "verde" if p.tipo == "fila" else "morado")

        c += tarjeta("Matriz resultante",
                     kpis([("Tamaño original",
                            f"{len(j.ids_f)}×{len(j.ids_c)}", "gris"),
                           ("Tamaño final",
                            f"{len(j.filas_finales)}×{len(j.columnas_finales)}",
                            "verde"),
                           ("Sobreviven",
                            f"{', '.join(j.filas_finales)} vs "
                            f"{', '.join(j.columnas_finales)}", "azul")]), "verde")
        c += tarjeta("", figura(graficas_Juegos.figura_eliminacion(j, None)), "rojo")
        return self._envolver("jt2", "Juegos · Paso 2 — Eliminación por dominancia", c)

    def _matriz_paso(self, p) -> str:
        """Matriz HTML del paso, con la fila o columna eliminada tachada."""
        j = self.j
        th = '<th class="izq">I \\ II</th>' + "".join(
            f'<th class="{"muerta" if (p.tipo == "columna" and c == p.eliminada) else ""}">'
            f'{esc(c)}</th>' for c in p.columnas_antes)
        trs = []
        for f in p.filas_antes:
            muerta_f = p.tipo == "fila" and f == p.eliminada
            tds = "".join(
                f'<td class="{"muerta" if muerta_f or (p.tipo == "columna" and c == p.eliminada) else ""}">'
                f'{esc(num(j.pagos[f][c], 0))}</td>' for c in p.columnas_antes)
            marca = ' class="fila-muerta"' if muerta_f else ""
            etiqueta = (f'{esc(f)} <span class="tache">← eliminada</span>'
                        if muerta_f else esc(f))
            trs.append(f'<tr{marca}><td class="izq">{etiqueta}</td>{tds}</tr>')
        if p.tipo == "columna":
            pie = "".join(
                f'<td class="senal">{"↑ eliminada" if c == p.eliminada else ""}</td>'
                for c in p.columnas_antes)
            trs.append(f'<tr><td class="izq"></td>{pie}</tr>')
        return (f'<div class="tabla-env"><table class="juego"><thead><tr>{th}</tr>'
                f'</thead><tbody>{"".join(trs)}</tbody></table></div>')

    def jsec3(self) -> str:
        j = self.j
        if not j.reduccion_completa:
            return self._envolver(
                "jt3", "Juegos · Paso 3 — Matriz de probabilidades",
                tarjeta("No aplica", parrafo(
                    "La reducción no llegó a una matriz 2×2."), "ambar"))
        ff, cc = j.filas_finales, j.columnas_finales
        c = tarjeta(
            "De la matriz reducida a la matriz de probabilidades",
            parrafo(f"Los valores que sobrevivieron se dividen por "
                    f"{num(j.factor, 0)} para expresarlos como proporciones.")
            + tabla(["Matriz reducida"] + list(cc),
                    [[f] + [num(j.matriz_reducida[f][c], 0) for c in cc] for f in ff])
            + tabla(["Matriz de probabilidades"] + list(cc),
                    [[f] + [num(j.matriz_prob[f][c], 2) for c in cc] for f in ff]),
            "morado")
        c += tarjeta("", figura(graficas_Juegos.figura_probabilidades(j, None)), "azul")
        return self._envolver("jt3", "Juegos · Paso 3 — Matriz de probabilidades", c)

    def jsec4(self) -> str:
        j = self.j
        if not (j.reduccion_completa and j.solucion_fila):
            return self._envolver(
                "jt4", "Juegos · Paso 4 — Solución algebraica",
                tarjeta("No aplica", parrafo(
                    "El método algebraico de dos ecuaciones requiere una matriz 2×2."),
                    "ambar"))
        c = ""
        for sol, quien, color in [
                (j.solucion_fila, f"Jugador I — {j.cfg.JUGADOR_FILA['nombre']}", "azul"),
                (j.solucion_columna,
                 f"Jugador II — {j.cfg.JUGADOR_COLUMNA['nombre']}", "rojo")]:
            c += tarjeta(
                quien,
                parrafo(sol.etiqueta_p) + parrafo(sol.etiqueta_q, "suave")
                + formula(sol.ecuaciones)
                + parrafo("Igualar y resolver para p:", "ok")
                + formula(sol.algebra)
                + kpis([("p", f"{num(sol.p, 4)} ({pct(sol.p, 2)})", "verde"),
                        ("q = 1 − p", f"{num(sol.q, 4)} ({pct(sol.q, 2)})", "azul"),
                        ("Valor del juego", num(sol.valor, 4), "morado")]), color)
        c += tarjeta("Comprobación",
                     formula([
                         f"Valor desde el jugador I  = {num(j.solucion_fila.valor, 4)}",
                         f"Valor desde el jugador II = {num(j.solucion_columna.valor, 4)}",
                         f"p + q (jugador I)  = {num(j.solucion_fila.p + j.solucion_fila.q, 4)}",
                         f"p + q (jugador II) = {num(j.solucion_columna.p + j.solucion_columna.q, 4)}"])
                     + parrafo("Los dos caminos algebraicos conducen al mismo valor y "
                               "las probabilidades suman 1 en ambos casos.", "ok"),
                     "verde")
        return self._envolver("jt4", "Juegos · Paso 4 — Solución algebraica", c)

    def jsec5(self) -> str:
        j = self.j
        if not (j.reduccion_completa and j.solucion_fila):
            return self._envolver(
                "jt5", "Juegos · Paso 5 — Análisis gráfico",
                tarjeta("No aplica", parrafo("Requiere una matriz 2×2."), "ambar"))
        c = tarjeta("Rectas del juego",
                    parrafo("Primero lo algebraico y después el gráfico: cada "
                            "ecuación es una recta sobre p ∈ [0, 1] y el punto de "
                            "corte es la estrategia óptima.", "suave"), "azul")
        for sol, quien in [(j.solucion_fila, "Jugador I"),
                           (j.solucion_columna, "Jugador II")]:
            filas = [[k, r["ecuacion"], f"(0 , {num(r['b'], 2)})",
                      f"(1 , {num(r['m'] + r['b'], 2)})"]
                     for k, r in sol.rectas.items()]
            c += tarjeta(quien, tabla(["Recta", "Ecuación", "Punto p = 0",
                                       "Punto p = 1"], filas, alinear_izq=2), "morado")
        c += tarjeta("", figura(graficas_Juegos.figura_grafico_juego(j, None)), "verde")
        return self._envolver("jt5", "Juegos · Paso 5 — Análisis gráfico", c)

    def jsec6(self) -> str:
        j = self.j
        indicadores = [("Tipo de solución", j.tipo_solucion, "azul"),
                       ("Valor del juego",
                        f"{num(j.valor_juego, 2)} {j.unidad}", "verde"),
                       ("Para la competencia",
                        f"{num(j.factor - j.valor_juego, 2)} {j.unidad}", "rojo")]
        c = tarjeta("Resumen del juego", kpis(indicadores), "azul")
        if j.solucion_fila:
            f1, f2 = j.filas_finales
            c1, c2 = j.columnas_finales
            c += tarjeta("Estrategias mixtas óptimas", kpis([
                (f"{f1} · {j.nombre_f[f1]}", pct(j.solucion_fila.p, 2), "verde"),
                (f"{f2} · {j.nombre_f[f2]}", pct(j.solucion_fila.q, 2), "verde"),
                (f"{c1} · {j.nombre_c[c1]}", pct(j.solucion_columna.p, 2), "rojo"),
                (f"{c2} · {j.nombre_c[c2]}", pct(j.solucion_columna.q, 2), "rojo"),
            ]), "morado")
        colores = ["azul", "morado", "verde", "rojo", "ambar", "azul"]
        for k, texto in enumerate(j.texto_conclusion()):
            titulo, _, cuerpo = texto.partition(". ")
            c += tarjeta(titulo if len(titulo) < 70 else "",
                         parrafo(cuerpo or texto), colores[k % len(colores)])
        c += tarjeta("", figura(graficas_Juegos.figura_resumen_juego(j, None)), "verde")
        return self._envolver("jt6", "Juegos · Paso 6 — Estrategias y valor del juego", c)

    # -----------------------------------------------------------------
    def _envolver(self, clave: str, titulo: str, cuerpo: str) -> str:
        return (f'<div class="seccion" id="{esc(clave)}">'
                f'<h2 class="seccion-tit">{esc(titulo)}</h2>{cuerpo}</div>')


# =====================================================================
#  PLANTILLA, CSS Y JS
# =====================================================================
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI','DejaVu Sans',system-ui,sans-serif;background:#f1f5f9;
color:#0f172a;display:flex;min-height:100vh;font-size:15px}
aside{width:290px;background:#1e293b;color:#e2e8f0;position:fixed;top:0;bottom:0;
display:flex;flex-direction:column}
.marca{background:#1e3a8a;padding:22px 20px}
.marca h1{font-size:15px;letter-spacing:.5px;line-height:1.35}
.marca p{font-size:11px;color:#bfdbfe;margin-top:6px;line-height:1.4}
nav{overflow-y:auto;flex:1;padding:10px 0}
.nav-it{display:flex;align-items:center;gap:10px;padding:9px 18px;cursor:pointer;
font-size:13.5px;color:#cbd5e1;border-left:4px solid transparent;user-select:none}
.nav-it:hover{background:#334155;color:#fff}
.nav-it.on{background:#334155;color:#fff;border-left-color:#3b82f6;font-weight:600}
.nav-ic{width:26px;height:26px;border-radius:7px;background:#0f172a;color:#93c5fd;
display:grid;place-items:center;font-size:11px;font-weight:700;flex:none}
.nav-it.on .nav-ic{background:#2563eb;color:#fff}
main{margin-left:290px;flex:1;display:flex;flex-direction:column;min-width:0}
header{background:#fff;border-bottom:1px solid #e2e8f0;padding:16px 30px;
display:flex;justify-content:space-between;align-items:center;gap:20px;
position:sticky;top:0;z-index:5}
header h2{font-size:19px}
header .res{font-size:13px;color:#64748b}
.cont{padding:22px 30px 60px;max-width:1180px}
.seccion{display:none}
.seccion.on{display:block;animation:ap .25s ease}
@keyframes ap{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.seccion-tit{display:none}
.portada{background:#1e3a8a;color:#fff;border-radius:14px;padding:30px;text-align:center;
margin-bottom:18px}
.portada h1{font-size:23px;line-height:1.3}
.portada .sub{color:#dbeafe;margin-top:8px;font-size:14px}
.portada .meta{color:#bfdbfe;margin-top:6px;font-size:12px;font-style:italic}
.rejilla{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:16px}
.rejilla .tarjeta{margin:0}
.tarjeta{background:#fff;border-radius:12px;overflow:hidden;margin-bottom:16px;
box-shadow:0 1px 3px rgba(15,23,42,.08);border:1px solid #e2e8f0}
.tarjeta::before{content:"";display:block;height:4px}
.tarjeta.azul::before{background:#1e3a8a}.tarjeta.verde::before{background:#059669}
.tarjeta.rojo::before{background:#dc2626}.tarjeta.ambar::before{background:#d97706}
.tarjeta.morado::before{background:#7c3aed}.tarjeta.gris::before{background:#64748b}
.tarjeta.destacada{background:#fffbeb;border-color:#f59e0b}
.t-tit{padding:18px 22px 0;font-size:14.5px;letter-spacing:.3px;text-transform:uppercase}
.tarjeta.azul .t-tit{color:#1e3a8a}.tarjeta.verde .t-tit{color:#059669}
.tarjeta.rojo .t-tit{color:#b91c1c}.tarjeta.ambar .t-tit{color:#b45309}
.tarjeta.morado .t-tit{color:#7c3aed}
.t-cuerpo{padding:14px 22px 22px}
.t-cuerpo p{line-height:1.65;margin-bottom:8px}
.t-cuerpo ul,.t-cuerpo ol{margin:8px 0 8px 22px;line-height:1.7}
.t-cuerpo li{margin-bottom:5px}
.t-cuerpo h4{margin:16px 0 4px;font-size:13.5px;color:#334155}
p.suave{color:#64748b;font-size:13.5px}
p.ok{color:#047857;font-weight:600}
p.aviso{color:#b45309;font-weight:600}
.tabla-env{overflow-x:auto;margin:12px 0;border-radius:10px;border:1px solid #e2e8f0}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{background:#1e3a8a;color:#fff;padding:11px 12px;text-align:center;font-weight:600;
white-space:nowrap}
th.izq,td.izq{text-align:left}
td{padding:10px 12px;text-align:center;border-top:1px solid #f1f5f9}
tbody tr:nth-child(even){background:#f8fafc}
tbody tr.destacada{background:#ecfdf5!important;color:#065f46;font-weight:700}
table.juego td.muerta,table.juego th.muerta{color:#cbd5e1;background:#f8fafc;
text-decoration:line-through;text-decoration-color:#dc2626;text-decoration-thickness:2px}
table.juego tr.fila-muerta{background:#fef2f2}
table.juego tr.fila-muerta td{color:#cbd5e1}
.tache{color:#dc2626;font-size:11.5px;font-weight:700;text-decoration:none;
display:inline-block;margin-left:6px}
table.juego td.senal{color:#7c3aed;font-size:11.5px;font-weight:700;border-top:0}
.formula{background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;padding:14px 16px;
font-family:'DejaVu Sans Mono',Consolas,monospace;font-size:13px;line-height:1.85;
overflow-x:auto;margin:10px 0;white-space:pre-wrap}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0 4px}
.kpi{flex:1 1 180px;background:#f8fafc;border-radius:10px;padding:13px 16px;
border:2px solid #e2e8f0}
.kpi-et{display:block;font-size:11.5px;color:#64748b;margin-bottom:5px}
.kpi-va{font-size:17px;font-weight:700}
.kpi.verde{border-color:#059669}.kpi.verde .kpi-va{color:#059669}
.kpi.azul{border-color:#2563eb}.kpi.azul .kpi-va{color:#1e3a8a}
.kpi.rojo{border-color:#dc2626}.kpi.rojo .kpi-va{color:#dc2626}
.kpi.ambar{border-color:#d97706}.kpi.ambar .kpi-va{color:#b45309}
.kpi.morado{border-color:#7c3aed}.kpi.morado .kpi-va{color:#7c3aed}
.kpi.gris{border-color:#94a3b8}.kpi.gris .kpi-va{color:#475569}
.figura{margin:6px 0}
.figura img{width:100%;height:auto;border-radius:10px;border:1px solid #e2e8f0}
.figura figcaption{font-size:12.5px;color:#64748b;text-align:center;margin-top:8px}
.barra{position:relative;height:34px;background:#e2e8f0;border-radius:9px;
overflow:hidden;margin:14px 0}
.barra-in{height:100%}
.barra-in.verde{background:#059669}.barra-in.ambar{background:#d97706}
.barra-in.rojo{background:#dc2626}
.barra-tx{position:absolute;inset:0;display:grid;place-items:center;font-weight:700;
font-size:13.5px}
input[type=text],input:not([type]){width:120px;padding:7px 9px;border:1px solid #cbd5e1;
border-radius:7px;text-align:center;font-family:'DejaVu Sans Mono',monospace;
font-size:13.5px}
input:focus{outline:2px solid #2563eb;border-color:#2563eb}
.deslizador{margin:16px 0}
.deslizador label{display:block;font-weight:600;margin-bottom:6px;font-size:13.5px}
.deslizador input[type=range]{width:100%;max-width:560px}
.acciones{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{border:0;border-radius:9px;padding:11px 20px;font-size:14px;font-weight:600;
cursor:pointer;color:#fff;text-decoration:none;display:inline-block}
.btn.verde{background:#059669}.btn.verde:hover{background:#047857}
.btn.azul{background:#2563eb}.btn.azul:hover{background:#1d4ed8}
.btn.gris{background:#e2e8f0;color:#0f172a}.btn.gris:hover{background:#cbd5e1}
.pie{display:flex;justify-content:space-between;gap:12px;padding:10px 30px 30px;
max-width:1180px}
@media print{aside{display:none}main{margin:0}.seccion{display:block!important;
page-break-after:always}header{position:static}.pie{display:none}}
@media(max-width:1000px){aside{display:none}main{margin:0}}
"""

JS = """
const items=[...document.querySelectorAll('.nav-it')];
const secs=[...document.querySelectorAll('.seccion')];
function ir(id){
  secs.forEach(s=>s.classList.toggle('on',s.id===id));
  items.forEach(a=>a.classList.toggle('on',a.dataset.ir===id));
  const it=items.find(a=>a.dataset.ir===id);
  document.getElementById('tit').textContent=it?it.innerText.trim():'';
  window.scrollTo({top:0,behavior:'instant'});
  location.hash=id;
}
items.forEach(a=>a.addEventListener('click',()=>ir(a.dataset.ir)));
document.getElementById('ant').addEventListener('click',()=>salto(-1));
document.getElementById('sig').addEventListener('click',()=>salto(1));
function salto(d){
  const i=items.findIndex(a=>a.classList.contains('on'));
  const j=Math.min(Math.max(i+d,0),items.length-1);
  ir(items[j].dataset.ir);
}
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT')return;
  if(e.key==='ArrowRight')salto(1);
  if(e.key==='ArrowLeft')salto(-1);
});
ir((location.hash||'#contexto').slice(1));

const rango=document.getElementById('rango');
if(rango){
  const campos=[...document.querySelectorAll('input[name^=prior_]')];
  const txt=document.getElementById('rango-txt');
  const pinta=()=>{
    const p=parseFloat(rango.value);
    if(campos[0])campos[0].value=p.toFixed(4).replace(/0+$/,'').replace(/\\.$/,'');
    if(campos[1])campos[1].value=(1-p).toFixed(4).replace(/0+$/,'').replace(/\\.$/,'');
    txt.textContent='P(s1) = '+(p*100).toFixed(0)+'%  ·  P(s2) = '+((1-p)*100).toFixed(0)
      +'%   — pulsa «Recalcular» para aplicar el cambio a todo el estudio.';
  };
  rango.addEventListener('input',pinta);pinta();
}
"""

PLANTILLA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title><style>{css}</style></head><body>
<aside>
  <div class="marca"><h1>INVESTIGACIÓN<br>DE OPERACIONES</h1>
  <p>Decisiones bajo incertidumbre e información muestral</p></div>
  <nav>{nav}</nav>
</aside>
<main>
  <header><h2 id="tit"></h2><div class="res">{resumen}</div></header>
  <div class="cont">{secciones}</div>
  <div class="pie">
    <button class="btn gris" id="ant">◀ Anterior</button>
    <button class="btn azul" id="sig">Siguiente ▶</button>
  </div>
</main>
<script>{js}</script></body></html>"""


# =====================================================================
#  SERVIDOR
# =====================================================================
class Estado:
    """Mantiene los datos y el modelo vivos entre peticiones."""

    def __init__(self):
        self.datos = datos_editables()
        self.modelo = ModeloDecision(self.datos)
        self.datos_juego = datos_juego_editables()
        self.juego = JuegoSumaCero(self.datos_juego)
        self.mensaje = ""

    def recalcular(self, campos: dict) -> None:
        d, m, jd, j = self.datos, self.modelo, self.datos_juego, self.juego
        for clave, valor in campos.items():
            valor = valor.strip().replace(",", ".")
            if clave.startswith("pago_"):
                _, a, s = clave.split("_", 2)
                d.MATRIZ_PAGOS[m.ids_alt.index(a)][m.ids_est.index(s)] = float(valor)
            elif clave.startswith("prior_"):
                s = clave.split("_", 1)[1]
                d.ESTADOS[m.ids_est.index(s)]["prior"] = float(valor)
            elif clave.startswith("ver_"):
                _, ind, s = clave.split("_", 2)
                d.VEROSIMILITUDES[m.ids_ind.index(ind)][m.ids_est.index(s)] = float(valor)
            elif clave.startswith("jpago_"):
                _, f, c = clave.split("_", 2)
                jd.MATRIZ_JUEGO[j.ids_f.index(f)][j.ids_c.index(c)] = float(valor)
        self.modelo = ModeloDecision(d)
        self.juego = JuegoSumaCero(jd)

    def restaurar(self) -> None:
        self.datos = datos_editables()
        self.modelo = ModeloDecision(self.datos)
        self.datos_juego = datos_juego_editables()
        self.juego = JuegoSumaCero(self.datos_juego)


ESTADO = Estado()


def pagina_error(titulo: str, detalle: str) -> bytes:
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
            f'<title>{esc(titulo)}</title><style>{CSS}</style></head><body>'
            f'<main style="margin:0"><div class="cont">'
            f'{tarjeta(titulo, parrafo(detalle) + formula(detalle.splitlines()) + chr(10) + "<a class=\'btn azul\' href=\'/#datos\'>Volver a los datos</a>", "rojo")}'
            f'</div></main></body></html>').encode("utf-8")


class Manejador(BaseHTTPRequestHandler):

    def log_message(self, *a):        # silencia el log de peticiones
        pass

    def _enviar(self, cuerpo: bytes, codigo: int = 200,
                tipo: str = "text/html; charset=utf-8") -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _redirigir(self, destino: str = "/") -> None:
        self.send_response(303)
        self.send_header("Location", destino)
        self.end_headers()

    def do_GET(self):
        ruta = urllib.parse.urlparse(self.path).path
        if ruta in ("/", "/index.html"):
            self._enviar(Tablero(ESTADO.modelo, ESTADO.juego).html().encode("utf-8"))
        elif ruta == "/exportar":
            try:
                carpeta = os.path.abspath(ESTADO.datos.CARPETA_SALIDA)
                import main as prog
                archivos = graficas.generar_todas(ESTADO.modelo, carpeta)
                archivos.update(graficas_Juegos.generar_todas_juego(
                    ESTADO.juego, carpeta))
                with open(os.path.join(carpeta, "reporte.txt"), "w",
                          encoding="utf-8") as fh:
                    fh.write(prog.construir_reporte(ESTADO.modelo, archivos,
                                                    ESTADO.juego))
                with open(os.path.join(carpeta, "tablero.html"), "w",
                          encoding="utf-8") as fh:
                    fh.write(Tablero(ESTADO.modelo, ESTADO.juego,
                                     interactivo=False).html())
                cuerpo = tarjeta(
                    "Exportación completada",
                    parrafo(f"Se guardaron las figuras, el informe de texto y una "
                            f"copia del tablero en:")
                    + formula([carpeta])
                    + "<a class='btn azul' href='/'>Volver al tablero</a>", "verde")
                self._enviar((f'<!DOCTYPE html><html lang="es"><head>'
                              f'<meta charset="utf-8"><style>{CSS}</style></head>'
                              f'<body><main style="margin:0"><div class="cont">'
                              f'{cuerpo}</div></main></body></html>').encode("utf-8"))
            except Exception as err:
                self._enviar(pagina_error("Error al exportar", str(err)), 500)
        else:
            self._enviar(b"No encontrado", 404, "text/plain; charset=utf-8")

    def do_POST(self):
        ruta = urllib.parse.urlparse(self.path).path
        largo = int(self.headers.get("Content-Length", 0))
        crudo = self.rfile.read(largo).decode("utf-8")
        campos = {k: v[0] for k, v in urllib.parse.parse_qs(crudo).items()}
        try:
            if ruta == "/restaurar":
                ESTADO.restaurar()
            elif ruta == "/recalcular":
                ESTADO.recalcular(campos)
            else:
                self._enviar(b"No encontrado", 404, "text/plain; charset=utf-8")
                return
        except ValueError as err:
            self._enviar(pagina_error("Datos inconsistentes", str(err)), 400)
            return
        self._redirigir("/#datos")


def servir(puerto: int = 8000, abrir: bool = True) -> None:
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    url = f"http://127.0.0.1:{puerto}/"
    print(f"\n  Tablero disponible en  {url}")
    print("  Pulsa Ctrl+C para detenerlo.\n")
    if abrir:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Tablero detenido.")
        servidor.shutdown()


def main() -> int:
    ap = argparse.ArgumentParser(description="Tablero gráfico del estudio")
    ap.add_argument("--html", action="store_true",
                    help="genera tablero.html sin levantar el servidor")
    ap.add_argument("--salida", default="tablero.html")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--no-abrir", action="store_true",
                    help="no abre el navegador automáticamente")
    args = ap.parse_args()

    if args.html:
        modelo = ModeloDecision(datos_editables())
        juego = JuegoSumaCero(datos_juego_editables())
        with open(args.salida, "w", encoding="utf-8") as fh:
            fh.write(Tablero(modelo, juego, interactivo=False).html())
        print(f"✔ Tablero generado: {os.path.abspath(args.salida)}")
        return 0

    servir(args.puerto, not args.no_abrir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())