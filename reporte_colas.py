# -*- coding: utf-8 -*-
"""
=====================================================================
 REPORTE EN CONSOLA — TEORÍA DE COLAS
=====================================================================
Reutiliza las primitivas de reporte.py. Ningún valor está escrito a
mano: todo proviene del objeto ModeloColas.
=====================================================================
"""
from __future__ import annotations

from colas import ModeloColas, _num as num, _pct as pct, _dinero as dinero
from reporte import marco, parrafo, tabla


def _seccion(titulo: str) -> str:
    A = 100
    return ("\n" + "═" * A + "\n"
            + f" {titulo.upper()} ".center(A, "═") + "\n"
            + "═" * A)


def encabezado_colas(m: ModeloColas) -> str:
    cfg = m.cfg
    cuerpo = [
        "¿POR QUÉ UN TERCER MODELO?",
        cfg.CONTEXTO_COLAS,
        "",
        "SUPUESTOS DEL MODELO M/M/1",
        "• Llegadas según un proceso de Poisson (una cola, un servidor).",
        "• Tiempos de servicio exponenciales.",
        "• Disciplina de atención FIFO (primero en llegar, primero en ser atendido).",
        "• Capacidad de la cola: infinita.",
        "",
        "¿CÓMO SE OBTIENEN λ Y μ?",
    ]
    cuerpo += ["   " + ln for ln in m.actual.desarrollo["lambda"]]
    cuerpo += [""]
    cuerpo += ["   " + ln for ln in m.actual.desarrollo["mu"]]
    cuerpo += [""]
    cuerpo += ["   " + ln for ln in m.actual.desarrollo["rho"]]
    return ("\n" + marco(cfg.TITULO_COLAS.upper(), [cfg.SUBTITULO_COLAS], doble=True)
            + "\n\n" + marco("CONTEXTO DEL SISTEMA DE COLAS", cuerpo))


def reporte_actual(m: ModeloColas) -> str:
    a = m.actual
    txt = [_seccion("Teoría de Colas · Cálculo del sistema actual")]
    txt += ["",
            tabla(["Parámetro", "Valor", "Unidad"], [
                ["λ — tasa de llegada", num(a.lambda_, 4), "clientes/hora"],
                ["μ — tasa de servicio", num(a.mu, 4), "clientes/hora"],
                ["ρ — utilización", f"{num(a.rho, 4)} ({pct(a.rho)})", "adimensional"],
            ])]

    txt += ["", "» Desarrollo algebraico de los 7 pasos:", ""]
    for clave, titulo in [
        ("p0", "1. P0 — probabilidad de sistema vacío"),
        ("lq", "2. Lq — clientes promedio en cola"),
        ("l",  "3. L  — clientes promedio en el sistema"),
        ("wq", "4. Wq — tiempo promedio en cola"),
        ("w",  "5. W  — tiempo promedio en el sistema"),
        ("pw", "6. Pw — probabilidad de esperar"),
    ]:
        txt.append(f"   {titulo}")
        for ln in a.desarrollo[clave]:
            txt.append(f"      {ln}")
        txt.append("")

    filas = [[n, num(a.pn[n], 6), pct(a.pn[n])] for n in sorted(a.pn.keys())]
    txt += ["  7. Pn — probabilidad de n clientes en el sistema",
            tabla(["n", "P(n)", "%"], filas)]
    return "\n".join(txt)


def reporte_mejora(m: ModeloColas) -> str:
    b = m.mejorado
    txt = [_seccion("Teoría de Colas · Cálculo del sistema mejorado"),
           "",
           parrafo(b.descripcion, "   "),
           ""]
    txt += [tabla(["Parámetro", "Valor", "Unidad"], [
        ["λ — tasa de llegada", num(b.lambda_, 4), "clientes/hora"],
        ["μ — tasa de servicio", num(b.mu, 4), "clientes/hora"],
        ["ρ — utilización", f"{num(b.rho, 4)} ({pct(b.rho)})", "adimensional"],
    ])]
    txt += ["", "» Desarrollo algebraico de los 7 pasos:", ""]
    for clave, titulo in [
        ("p0", "1. P0"), ("lq", "2. Lq"), ("l", "3. L"),
        ("wq", "4. Wq"), ("w", "5. W"), ("pw", "6. Pw"),
    ]:
        txt.append(f"   {titulo}")
        for ln in b.desarrollo[clave]:
            txt.append(f"      {ln}")
        txt.append("")
    filas = [[n, num(b.pn[n], 6), pct(b.pn[n])] for n in sorted(b.pn.keys())]
    txt += ["  7. Pn", tabla(["n", "P(n)", "%"], filas)]
    return "\n".join(txt)


def reporte_comparacion(m: ModeloColas) -> str:
    a, b = m.actual, m.mejorado
    txt = [_seccion("Teoría de Colas · Comparación y conclusión")]
    filas = [
        ["λ (clientes/hora)", num(a.lambda_, 4), num(b.lambda_, 4), "—"],
        ["μ (clientes/hora)", num(a.mu, 4), num(b.mu, 4),
         f"+{num(b.mu - a.mu, 4)}"],
        ["Tiempo servicio (s)", num(a.tiempo_servicio, 0),
         num(b.tiempo_servicio, 0),
         f"−{num(a.tiempo_servicio - b.tiempo_servicio, 0)}"],
        ["ρ — utilización", pct(a.rho), pct(b.rho), f"−{pct(a.rho - b.rho)}"],
        ["P0 — sistema vacío", pct(a.p0), pct(b.p0), f"+{pct(b.p0 - a.p0)}"],
        ["Lq — clientes en cola", num(a.lq, 4), num(b.lq, 4),
         f"−{num(m.mejora_lq, 2)}%"],
        ["L — clientes en sistema", num(a.l, 4), num(b.l, 4),
         f"−{num(m.mejora_l, 2)}%"],
        ["Wq — min en cola", num(a.wq * 60, 2), num(b.wq * 60, 2),
         f"−{num(m.mejora_wq, 2)}%"],
        ["W — min en sistema", num(a.w * 60, 2), num(b.w * 60, 2),
         f"−{num(m.mejora_w, 2)}%"],
        ["Pw — prob. de esperar", pct(a.pw), pct(b.pw),
         f"−{pct(a.pw - b.pw)}"],
    ]
    txt += ["", tabla(["Indicador", "Actual", "Mejorado", "Cambio"], filas,
                      alinear_izq=1), ""]
    txt += [marco("CONCLUSIÓN DEL ESTUDIO DE COLAS", m.texto_conclusion(), doble=True)]
    return "\n".join(txt)


def reporte_colas(m: ModeloColas, archivos: dict) -> str:
    return "\n".join([
        encabezado_colas(m),
        reporte_actual(m),
        reporte_mejora(m),
        reporte_comparacion(m),
    ])