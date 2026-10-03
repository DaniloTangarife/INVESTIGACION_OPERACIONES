# -*- coding: utf-8 -*-
"""
=====================================================================
 GRÁFICAS — TEORÍA DE JUEGOS
=====================================================================
Todas las figuras se dibujan a partir del objeto JuegoSumaCero: número
de estrategias, posiciones, tachados, flechas y textos se calculan en
tiempo de ejecución.
=====================================================================
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from graficas import (AZUL, GRIS_BORDE, GRIS_FONDO, GRIS_TEXTO, ROJO, VERDE,
                      _envolver, _guardar)
from juegos import JuegoSumaCero
from modelo import num, pct

AMBAR = "#d97706"
MORADO = "#7c3aed"
CELDA_VIVA = "#ffffff"
CELDA_MUERTA = "#f1f5f9"


# =====================================================================
#  DIBUJO GENÉRICO DE UNA MATRIZ DE PAGOS
# =====================================================================
def _matriz(ax, j: JuegoSumaCero, filas: list[str], cols: list[str],
            x0: float = 0.0, y0: float = 0.0, cw: float = 1.0, ch: float = 0.72,
            eliminadas_f: set = None, eliminadas_c: set = None,
            resaltar: set = None, titulo: str = "",
            mostrar_ids: bool = True, fs: float = 11.5) -> dict:
    """Dibuja la matriz y devuelve las coordenadas de cada celda."""
    eliminadas_f = eliminadas_f or set()
    eliminadas_c = eliminadas_c or set()
    resaltar = resaltar or set()
    pos = {}

    if titulo:
        ax.text(x0 + len(cols) * cw / 2, y0 - ch * 0.85, titulo, ha="center",
                va="bottom", fontsize=fs, fontweight="bold", color=GRIS_TEXTO)

    if mostrar_ids:
        for jx, c in enumerate(cols):
            muerta = c in eliminadas_c
            ax.text(x0 + jx * cw + cw / 2, y0 - ch * 0.18, c, ha="center", va="bottom",
                    fontsize=fs - 0.5, fontweight="bold",
                    color="#94a3b8" if muerta else AZUL)
        for iy, f in enumerate(filas):
            muerta = f in eliminadas_f
            ax.text(x0 - cw * 0.16, y0 + iy * ch + ch / 2, f, ha="right", va="center",
                    fontsize=fs - 0.5, fontweight="bold",
                    color="#94a3b8" if muerta else AZUL)

    for iy, f in enumerate(filas):
        for jx, c in enumerate(cols):
            muerta = f in eliminadas_f or c in eliminadas_c
            x, y = x0 + jx * cw, y0 + iy * ch
            pos[(f, c)] = (x + cw / 2, y + ch / 2)
            destacada = (f, c) in resaltar
            ax.add_patch(Rectangle(
                (x, y), cw, ch,
                facecolor=("#d1fae5" if destacada else
                           (CELDA_MUERTA if muerta else CELDA_VIVA)),
                edgecolor=VERDE if destacada else GRIS_BORDE,
                lw=2.2 if destacada else 1.1, zorder=2))
            ax.text(x + cw / 2, y + ch / 2, num(j.pagos[f][c], 0), ha="center",
                    va="center", fontsize=fs,
                    fontweight="bold" if destacada or not muerta else "normal",
                    color="#94a3b8" if muerta else (
                        "#065f46" if destacada else GRIS_TEXTO), zorder=3)

    # Tachado de filas y columnas eliminadas
    for f in eliminadas_f:
        if f in filas:
            iy = filas.index(f)
            y = y0 + iy * ch + ch / 2
            ax.plot([x0 - cw * 0.05, x0 + len(cols) * cw + cw * 0.05], [y, y],
                    color=ROJO, lw=3.2, alpha=0.9, solid_capstyle="round", zorder=6)
    for c in eliminadas_c:
        if c in cols:
            jx = cols.index(c)
            x = x0 + jx * cw + cw / 2
            ax.plot([x, x], [y0 - ch * 0.05, y0 + len(filas) * ch + ch * 0.05],
                    color=ROJO, lw=3.2, alpha=0.9, solid_capstyle="round", zorder=6)
    return pos


# =====================================================================
#  1. MATRIZ DEL JUEGO Y PUNTO DE SILLA
# =====================================================================
def figura_matriz_juego(j: JuegoSumaCero, carpeta):
    nf, nc = len(j.ids_f), len(j.ids_c)
    fig, ax = plt.subplots(figsize=(max(11, 2.2 * nc + 5), max(6.2, 1.1 * nf + 3.6)))
    ax.axis("off")
    cw, ch = 1.0, 0.72

    _matriz(ax, j, j.ids_f, j.ids_c, 0, 0, cw, ch,
            resaltar={(f, c) for f, c, _ in j.sillas})

    # Columna de mínimos de fila
    xm = nc * cw + cw * 0.35
    ax.text(xm + cw / 2, -ch * 0.18, "Mín. fila", ha="center", va="bottom",
            fontsize=11, fontweight="bold", color=ROJO)
    for iy, f in enumerate(j.ids_f):
        es_max = abs(j.min_fila[f] - j.maximin) < 1e-12
        ax.add_patch(Rectangle((xm, iy * ch), cw, ch,
                               facecolor="#fef2f2" if not es_max else "#fee2e2",
                               edgecolor=ROJO if es_max else GRIS_BORDE,
                               lw=2.2 if es_max else 1.1, zorder=2))
        ax.text(xm + cw / 2, iy * ch + ch / 2, num(j.min_fila[f], 0), ha="center",
                va="center", fontsize=11.5, fontweight="bold" if es_max else "normal",
                color=ROJO if es_max else GRIS_TEXTO, zorder=3)

    # Fila de máximos de columna
    ym = nf * ch + ch * 0.35
    ax.text(-cw * 0.16, ym + ch / 2, "Máx. columna", ha="right", va="center",
            fontsize=11, fontweight="bold", color=AZUL)
    for jx, c in enumerate(j.ids_c):
        es_min = abs(j.max_col[c] - j.minimax) < 1e-12
        ax.add_patch(Rectangle((jx * cw, ym), cw, ch,
                               facecolor="#eff6ff" if not es_min else "#dbeafe",
                               edgecolor=AZUL if es_min else GRIS_BORDE,
                               lw=2.2 if es_min else 1.1, zorder=2))
        ax.text(jx * cw + cw / 2, ym + ch / 2, num(j.max_col[c], 0), ha="center",
                va="center", fontsize=11.5, fontweight="bold" if es_min else "normal",
                color=AZUL if es_min else GRIS_TEXTO, zorder=3)

    # Veredicto
    if j.hay_silla:
        f, c, v = j.sillas[0]
        txt = (f"Maximin = {num(j.maximin, 0)}   =   Minimax = {num(j.minimax, 0)}\n"
               f"HAY PUNTO DE SILLA en ({f}, {c}) → valor del juego = {num(v, 0)}\n"
               f"El juego se resuelve con estrategias puras.")
        col, fondo = VERDE, "#ecfdf5"
    else:
        txt = (f"Maximin = {num(j.maximin, 0)}   ≠   Minimax = {num(j.minimax, 0)}\n"
               f"NO HAY PUNTO DE SILLA → no existe solución en estrategias puras.\n"
               f"Se continúa con la eliminación por dominancia.")
        col, fondo = AMBAR, "#fffbeb"
    ax.text((nc * cw + cw) / 2, ym + ch * 2.1, txt, ha="center", va="top",
            fontsize=12, fontweight="bold", color=col, linespacing=1.6,
            bbox=dict(boxstyle="round,pad=0.7", fc=fondo, ec=col, lw=2))

    ax.set_xlim(-2.4, xm + cw + 0.4)
    ax.set_ylim(-1.0, ym + ch * 3.6)
    ax.invert_yaxis()
    ax.set_title("Teoría de Juegos · Pasos 1 y 2 — Matriz de pagos y punto de silla",
                 fontsize=15, fontweight="bold", pad=20)
    ax.text(0.5, 1.015,
            f"Pagos: {j.unidad} que capta {j.cfg.JUGADOR_FILA['nombre']} "
            f"(jugador I, filas) frente a {j.cfg.JUGADOR_COLUMNA['nombre']} "
            f"(jugador II, columnas)",
            transform=ax.transAxes, ha="center", fontsize=10.5, color="#475569")
    fig.tight_layout()
    return _guardar(fig, carpeta, "08_juego_matriz.png")


# =====================================================================
#  2. ELIMINACIÓN POR DOMINANCIA, PASO A PASO
# =====================================================================
def figura_eliminacion(j: JuegoSumaCero, carpeta):
    if not j.pasos:
        return None
    n = len(j.pasos)
    cols_fig = min(2, n)
    filas_fig = (n + cols_fig - 1) // cols_fig
    nf, nc = len(j.ids_f), len(j.ids_c)

    fig, ejes = plt.subplots(filas_fig, cols_fig,
                             figsize=(7.4 * cols_fig, 4.6 * filas_fig))
    ejes = [ejes] if n == 1 else list(ejes.flat)

    cw, ch = 1.0, 0.72
    for k, paso in enumerate(j.pasos):
        ax = ejes[k]
        ax.axis("off")
        pos = _matriz(ax, j, paso.filas_antes, paso.columnas_antes, 0, 0, cw, ch,
                      eliminadas_f={paso.eliminada} if paso.tipo == "fila" else None,
                      eliminadas_c={paso.eliminada} if paso.tipo == "columna" else None,
                      fs=11)
        largo_c, largo_f = len(paso.columnas_antes), len(paso.filas_antes)

        # Flecha desde la estrategia dominante hacia la eliminada
        if paso.tipo == "fila":
            iy_d = paso.filas_antes.index(paso.dominante)
            iy_e = paso.filas_antes.index(paso.eliminada)
            x = largo_c * cw + cw * 0.55
            ax.add_patch(FancyArrowPatch(
                (x, iy_d * ch + ch / 2), (x, iy_e * ch + ch / 2),
                connectionstyle="arc3,rad=-0.45", arrowstyle="-|>,head_width=5,head_length=9",
                color=VERDE, lw=2.4, zorder=7))
            ax.text(x + cw * 0.55, (iy_d + iy_e) * ch / 2 + ch / 2,
                    f"{paso.dominante}\nelimina\n{paso.eliminada}", ha="left",
                    va="center", fontsize=10, fontweight="bold", color=VERDE,
                    linespacing=1.4)
            etiqueta = (f"Paso {paso.orden} · FILAS — la fila {paso.eliminada} está "
                        f"dominada por {paso.dominante}")
        else:
            jx_d = paso.columnas_antes.index(paso.dominante)
            jx_e = paso.columnas_antes.index(paso.eliminada)
            y = largo_f * ch + ch * 0.55
            ax.add_patch(FancyArrowPatch(
                (jx_d * cw + cw / 2, y), (jx_e * cw + cw / 2, y),
                connectionstyle="arc3,rad=0.45", arrowstyle="-|>,head_width=5,head_length=9",
                color=MORADO, lw=2.4, zorder=7))
            ax.text((jx_d + jx_e) * cw / 2 + cw / 2, y + ch * 0.85,
                    f"{paso.dominante} elimina {paso.eliminada}", ha="center",
                    va="top", fontsize=10, fontweight="bold", color=MORADO)
            etiqueta = (f"Paso {paso.orden} · COLUMNAS — la columna "
                        f"{paso.eliminada} está dominada por {paso.dominante}")

        ax.set_title(etiqueta, fontsize=11, fontweight="bold", pad=12,
                     color=VERDE if paso.tipo == "fila" else MORADO)
        regla = ("mayores pagos ⇒ elimina a la de menores"
                 if paso.tipo == "fila" else
                 "menores pagos ⇒ elimina a la de mayores")
        ax.text(largo_c * cw / 2, largo_f * ch + ch * 1.9, regla, ha="center",
                va="top", fontsize=9.5, style="italic", color="#64748b")
        ax.set_xlim(-1.5, largo_c * cw + cw * 2.6)
        ax.set_ylim(-1.2, largo_f * ch + ch * 2.6)
        ax.invert_yaxis()

    for ax in ejes[n:]:
        ax.axis("off")

    fig.suptitle("Teoría de Juegos · Paso 3 — Eliminación por dominancia",
                 fontsize=15, fontweight="bold")
    fig.text(0.5, 0.005,
             f"De la matriz {nf}×{nc} original quedan las estrategias "
             f"{' y '.join(j.filas_finales)} (jugador I) frente a "
             f"{' y '.join(j.columnas_finales)} (jugador II), conservando su "
             f"posición original.",
             ha="center", fontsize=11, style="italic", color="#334155")
    fig.tight_layout(rect=[0, 0.035, 1, 0.95])
    return _guardar(fig, carpeta, "09_juego_eliminacion.png")


# =====================================================================
#  3. MATRIZ REDUCIDA → MATRIZ DE PROBABILIDADES
# =====================================================================
def figura_probabilidades(j: JuegoSumaCero, carpeta):
    if not j.reduccion_completa:
        return None
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.axis("off")
    cw, ch = 1.15, 0.8
    ff, cc = j.filas_finales, j.columnas_finales

    _matriz(ax, j, ff, cc, 0, 0, cw, ch,
            titulo=f"Matriz reducida ({j.unidad})")

    # Flecha de conversión
    x_med = len(cc) * cw + cw * 0.55
    ax.add_patch(FancyArrowPatch((x_med, len(ff) * ch / 2),
                                 (x_med + cw * 1.1, len(ff) * ch / 2),
                                 arrowstyle="-|>,head_width=6,head_length=11",
                                 color=AZUL, lw=2.6))
    ax.text(x_med + cw * 0.55, len(ff) * ch / 2 - ch * 0.42,
            f"÷ {num(j.factor, 0)}", ha="center", va="bottom", fontsize=11.5,
            fontweight="bold", color=AZUL)

    # Matriz de probabilidades
    x2 = x_med + cw * 1.85
    ax.text(x2 + len(cc) * cw / 2, -ch * 0.85, "Matriz de probabilidades",
            ha="center", va="bottom", fontsize=11.5, fontweight="bold")
    for jx, c in enumerate(cc):
        ax.text(x2 + jx * cw + cw / 2, -ch * 0.18, c, ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=AZUL)
    for iy, f in enumerate(ff):
        ax.text(x2 - cw * 0.16, iy * ch + ch / 2, f, ha="right", va="center",
                fontsize=11, fontweight="bold", color=AZUL)
        for jx, c in enumerate(cc):
            ax.add_patch(Rectangle((x2 + jx * cw, iy * ch), cw, ch,
                                   facecolor="#eef2ff", edgecolor=MORADO, lw=1.6,
                                   zorder=2))
            ax.text(x2 + jx * cw + cw / 2, iy * ch + ch / 2,
                    num(j.matriz_prob[f][c], 2), ha="center", va="center",
                    fontsize=12, fontweight="bold", color=MORADO, zorder=3)

    ax.set_xlim(-1.6, x2 + len(cc) * cw + 0.5)
    ax.set_ylim(-1.5, len(ff) * ch + 0.7)
    ax.invert_yaxis()
    ax.set_title("Teoría de Juegos · Paso 4 — Conversión a matriz de probabilidades",
                 fontsize=15, fontweight="bold", pad=18)
    fig.tight_layout()
    return _guardar(fig, carpeta, "10_juego_probabilidades.png")


# =====================================================================
#  4. ANÁLISIS GRÁFICO DE LA SOLUCIÓN MIXTA
# =====================================================================
def figura_grafico_juego(j: JuegoSumaCero, carpeta):
    if not (j.reduccion_completa and j.solucion_fila):
        return None
    fig, ejes = plt.subplots(1, 2, figsize=(14.5, 6.2))
    ps = [i / 400 for i in range(401)]
    paletas = [("#2563eb", "#dc2626"), ("#059669", "#d97706")]

    for ax, sol, paleta, titulo in zip(
            ejes, [j.solucion_fila, j.solucion_columna], paletas,
            [f"Jugador I — {j.cfg.JUGADOR_FILA['nombre']}",
             f"Jugador II — {j.cfg.JUGADOR_COLUMNA['nombre']}"]):

        for (clave, recta), color in zip(sol.rectas.items(), paleta):
            ys = [recta["m"] * p + recta["b"] for p in ps]
            ax.plot(ps, ys, lw=2.8, color=color, zorder=3,
                    label=recta["ecuacion"])
            for pe in (0.0, 1.0):
                v = recta["m"] * pe + recta["b"]
                ax.plot(pe, v, "o", ms=6.5, color=color, zorder=4)
                ax.annotate(f"({int(pe)} , {num(v, 2)})", (pe, v),
                            textcoords="offset points",
                            xytext=(8 if pe == 0 else -8, 9),
                            ha="left" if pe == 0 else "right", fontsize=9,
                            color=color, fontweight="bold")

        ax.axvline(sol.p, color="#334155", ls="--", lw=1.4, alpha=0.8, zorder=2)
        ax.axhline(sol.valor, color="#334155", ls=":", lw=1.2, alpha=0.7, zorder=2)
        ax.plot(sol.p, sol.valor, "o", ms=12, mfc="white", mec=VERDE, mew=2.6, zorder=6)
        ax.annotate(f"SOLUCIÓN\np = {num(sol.p, 4)} ({pct(sol.p, 2)})\n"
                    f"q = {num(sol.q, 4)} ({pct(sol.q, 2)})\n"
                    f"Valor = {num(sol.valor, 4)}",
                    (sol.p, sol.valor), textcoords="offset points", xytext=(22, -70),
                    fontsize=9.8, fontweight="bold", color="#065f46",
                    bbox=dict(boxstyle="round,pad=0.55", fc="#ecfdf5", ec=VERDE, lw=1.7),
                    arrowprops=dict(arrowstyle="->", color=VERDE, lw=1.7))

        ax.set_title(titulo, fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel(_envolver(sol.etiqueta_p, 62), fontsize=10.5, labelpad=8)
        ax.set_ylabel("Valor esperado (matriz de probabilidades)", fontsize=10.5)
        ax.set_xlim(-0.02, 1.02)
        ax.grid(alpha=0.3, ls=":")
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.legend(fontsize=9.5, loc="best", framealpha=0.95)

    fig.suptitle("Teoría de Juegos · Paso 6 — Análisis gráfico de la solución mixta",
                 fontsize=15, fontweight="bold")
    fig.text(0.5, 0.005,
             f"El punto de corte de las dos rectas es la estrategia óptima: ahí el "
             f"rival queda indiferente entre sus alternativas. Ambos paneles "
             f"convergen al mismo valor del juego, {num(j.valor_normalizado, 4)} "
             f"({num(j.valor_juego, 2)} {j.unidad}).",
             ha="center", fontsize=10.5, style="italic", color="#334155")
    fig.tight_layout(rect=[0, 0.035, 1, 0.94])
    return _guardar(fig, carpeta, "11_juego_grafico.png")


# =====================================================================
#  5. RESUMEN DEL JUEGO
# =====================================================================
def figura_resumen_juego(j: JuegoSumaCero, carpeta):
    fig = plt.figure(figsize=(13.5, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.95], hspace=0.45, wspace=0.28)

    if j.reduccion_completa and j.solucion_fila:
        # Mezclas óptimas
        for k, (sol, etiquetas, nombre, colores) in enumerate([
            (j.solucion_fila, j.filas_finales, j.cfg.JUGADOR_FILA["nombre"],
             ["#2563eb", "#93c5fd"]),
            (j.solucion_columna, j.columnas_finales,
             j.cfg.JUGADOR_COLUMNA["nombre"], ["#dc2626", "#fca5a5"]),
        ]):
            ax = fig.add_subplot(gs[0, k])
            valores = [sol.p, sol.q]
            barras = ax.bar(etiquetas, valores, color=colores, alpha=0.92,
                            edgecolor="white", lw=1.6, width=0.55)
            for b, v in zip(barras, valores):
                ax.text(b.get_x() + b.get_width() / 2, v, pct(v, 2), ha="center",
                        va="bottom", fontsize=12, fontweight="bold")
            ax.set_ylim(0, 1.15)
            ax.set_ylabel("Probabilidad de uso")
            ax.set_title(f"Estrategia mixta óptima — {nombre}", fontsize=12,
                         fontweight="bold")
            ax.grid(axis="y", alpha=0.3, ls=":")
            ax.set_axisbelow(True)
            for lado in ("top", "right"):
                ax.spines[lado].set_visible(False)
    else:
        ax = fig.add_subplot(gs[0, :])
        ax.axis("off")
        ax.text(0.5, 0.5, "El juego se resuelve con estrategias puras", ha="center",
                va="center", fontsize=15, fontweight="bold", color=VERDE)

    # Panel de conclusión
    ax = fig.add_subplot(gs[1, :])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.005, 0.02), 0.99, 0.96,
                                boxstyle="round,pad=0.012,rounding_size=0.02",
                                transform=ax.transAxes, facecolor="#eff6ff",
                                edgecolor=AZUL, lw=2, zorder=1))
    ax.text(0.5, 0.90, "RESULTADO DEL JUEGO", transform=ax.transAxes, ha="center",
            fontsize=13, fontweight="bold", color=AZUL, zorder=3)

    izq = [f"Tipo de solución:  {j.tipo_solucion}",
           f"Maximin:  {num(j.maximin, 0)}      Minimax:  {num(j.minimax, 0)}",
           f"Estrategias sobrevivientes:  {', '.join(j.filas_finales)}  vs  "
           f"{', '.join(j.columnas_finales)}"]
    der = [f"Valor del juego:  {num(j.valor_juego, 2)} {j.unidad}",
           f"Para la competencia:  {num(j.factor - j.valor_juego, 2)} {j.unidad}",
           f"Eliminadas:  "
           + (", ".join(p.eliminada for p in j.pasos) if j.pasos else "ninguna")]
    ax.text(0.04, 0.74, "\n\n".join(izq), transform=ax.transAxes, fontsize=10.5,
            va="top", linespacing=1.3, zorder=3)
    ax.text(0.54, 0.74, "\n\n".join(der), transform=ax.transAxes, fontsize=10.5,
            va="top", linespacing=1.3, zorder=3)
    ax.text(0.04, 0.34, _envolver(j.texto_conclusion()[-1].split(". ", 1)[-1], 150),
            transform=ax.transAxes, fontsize=9.6, va="top", style="italic",
            color="#334155", linespacing=1.5, zorder=3)

    fig.suptitle("Teoría de Juegos · Paso 7 — Estrategias óptimas y valor del juego",
                 fontsize=15, fontweight="bold", y=0.985)
    return _guardar(fig, carpeta, "12_juego_resumen.png")


# =====================================================================
#  ORQUESTADOR
# =====================================================================
def generar_todas_juego(j: JuegoSumaCero, carpeta) -> dict:
    salida = {
        "juego_matriz": figura_matriz_juego(j, carpeta),
        "juego_eliminacion": figura_eliminacion(j, carpeta),
        "juego_probabilidades": figura_probabilidades(j, carpeta),
        "juego_grafico": figura_grafico_juego(j, carpeta),
        "juego_resumen": figura_resumen_juego(j, carpeta),
    }
    return {k: v for k, v in salida.items() if v is not None}