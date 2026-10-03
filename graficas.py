# -*- coding: utf-8 -*-
"""
=====================================================================
 GENERACIÓN DE GRÁFICAS Y ÁRBOLES  (100% dinámicos)
=====================================================================
Todas las figuras se dibujan a partir del objeto ModeloDecision: número
de alternativas, de estados y de indicadores, posiciones, colores,
etiquetas y textos se calculan en tiempo de ejecución.
=====================================================================
"""
from __future__ import annotations

import os
from itertools import cycle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from matplotlib.textpath import TextPath

import config as CFG
from modelo import ModeloDecision, dinero, num, pct

# ---------------------------------------------------------------------
#  ESTILO
# ---------------------------------------------------------------------
PALETA = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2"]
GRIS_FONDO = "#f8fafc"
GRIS_BORDE = "#cbd5e1"
GRIS_TEXTO = "#0f172a"
VERDE = "#059669"
ROJO = "#dc2626"
AZUL = "#1e3a8a"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": GRIS_BORDE,
    "axes.labelcolor": GRIS_TEXTO,
    "text.color": GRIS_TEXTO,
    "xtick.color": GRIS_TEXTO,
    "ytick.color": GRIS_TEXTO,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _colores(ids: list[str]) -> dict[str, str]:
    c = cycle(PALETA)
    return {i: next(c) for i in ids}


def _guardar(fig, carpeta, nombre: str):
    """Guarda la figura y devuelve la ruta. Si carpeta es None, devuelve la
    figura sin guardarla (modo interfaz gráfica)."""
    if carpeta is None:
        return fig
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    fig.savefig(ruta, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _envolver(texto: str, ancho: int) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(texto, ancho))


# =====================================================================
#  1. PANEL DE CONTEXTO
# =====================================================================
def figura_contexto(m: ModeloDecision, carpeta: str) -> str:
    c = m.cfg
    fuentes = [p["nombre"] for p in c.EQUIPO if p.get("fuente")]
    nombres = ", ".join(fuentes) if fuentes else "un integrante del equipo"

    fig = plt.figure(figsize=(13.5, 9.6))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color=GRIS_FONDO, zorder=0))

    # Encabezado
    ax.add_patch(FancyBboxPatch((0.03, 0.845), 0.94, 0.125,
                                boxstyle="round,pad=0.012,rounding_size=0.015",
                                facecolor=AZUL, edgecolor="none", zorder=1))
    ax.text(0.5, 0.945, c.TITULO, ha="center", va="center", fontsize=16.5,
            fontweight="bold", color="white", zorder=2)
    ax.text(0.5, 0.905, c.SUBTITULO, ha="center", va="center", fontsize=11,
            color="#dbeafe", zorder=2)
    ax.text(0.5, 0.872, f"{c.CURSO}   ·   {c.MARCO_LEGAL}", ha="center", va="center",
            fontsize=9.5, color="#bfdbfe", style="italic", zorder=2)

    def bloque(x, y, w, h, titulo, lineas, color=AZUL, fs=8.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.010,rounding_size=0.012",
                                    facecolor="white", edgecolor=GRIS_BORDE, zorder=1))
        ax.add_patch(Rectangle((x, y + h - 0.006), w, 0.006, color=color, zorder=2))
        ax.text(x + 0.018, y + h - 0.038, titulo, fontsize=10.5, fontweight="bold",
                color=color, va="center", zorder=3)
        ax.text(x + 0.018, y + h - 0.062, "\n".join(lineas), fontsize=fs, va="top",
                color=GRIS_TEXTO, linespacing=1.55, zorder=3)

    # Pregunta central
    bloque(0.03, 0.600, 0.455, 0.232, "¿QUÉ DECISIÓN SE ESTÁ TOMANDO?",
           [_envolver("La empresa debe escoger UNA de estas alternativas para la operación "
                      "de los sábados:", 58), ""] +
           [_envolver(f"▪ {a['id']} — {a['nombre']}: {a['descripcion']}.", 64)
            for a in c.ALTERNATIVAS])

    # Escenarios
    bloque(0.515, 0.600, 0.455, 0.232, "¿QUÉ NO CONTROLA LA EMPRESA?",
           [_envolver("El resultado depende del estado regulatorio, un factor externo:", 64), ""] +
           [_envolver(f"▪ {e['id']} — {e['nombre']}  ({pct(e['prior'], 0)}): {e['descripcion']}.", 64)
            for e in c.ESTADOS], color="#7c3aed")

    # Objetivos
    bloque(0.03, 0.322, 0.455, 0.252, "¿QUÉ SE BUSCA CON ESTE ESTUDIO?",
           [_envolver(t, 62) for t in [
               "1. Determinar la alternativa que maximiza la utilidad esperada.",
               "2. Medir qué tan estable es esa decisión si cambian las probabilidades "
               "(análisis de sensibilidad y punto de corte).",
               "3. Calcular cuánto valdría eliminar la incertidumbre (EVPI).",
               "4. Evaluar, vía Teorema de Bayes, si una consultoría jurídica previa "
               "cambiaría la decisión (EVSI).",
               "5. Concluir con cifras si conviene o no pagar esa consultoría."]],
           color="#059669", fs=8.9)

    # Origen de los datos — énfasis
    ax.add_patch(FancyBboxPatch((0.515, 0.322), 0.455, 0.252,
                                boxstyle="round,pad=0.010,rounding_size=0.012",
                                facecolor="#fffbeb", edgecolor="#f59e0b",
                                linewidth=1.8, zorder=1))
    ax.add_patch(Rectangle((0.515, 0.568), 0.455, 0.006, color="#d97706", zorder=2))
    ax.text(0.533, 0.546, "LOS DATOS NO SON INVENTADOS", fontsize=11,
            fontweight="bold", color="#b45309", va="center", zorder=3)
    ax.text(0.533, 0.522, _envolver(
        f"{nombres} hace parte de este equipo de trabajo y labora actualmente en la "
        f"empresa de transporte intermunicipal analizada. Gracias a ello cuenta con "
        f"acceso directo y autorizado a la información operativa real de la ruta: "
        f"utilidades por despacho, niveles de ocupación de los sábados y condiciones "
        f"regulatorias vigentes.", 66) + "\n\n" + _envolver(
        "Las cifras de la matriz de pagos provienen de esa fuente primaria, no de "
        "supuestos académicos. Por eso las conclusiones de este modelo son "
        "directamente aplicables a la operación real de la empresa.", 66),
        fontsize=8.7, va="top", color="#78350f", linespacing=1.55, zorder=3)

    # Franja de lectura de cifras
    ax.add_patch(FancyBboxPatch((0.03, 0.055), 0.94, 0.255,
                                boxstyle="round,pad=0.010,rounding_size=0.012",
                                facecolor="white", edgecolor=GRIS_BORDE, zorder=1))
    ax.add_patch(Rectangle((0.03, 0.304), 0.94, 0.006, color="#dc2626", zorder=2))
    ax.text(0.048, 0.282, "MATRIZ DE PAGOS — PUNTO DE PARTIDA DE TODO EL MODELO",
            fontsize=10.5, fontweight="bold", color="#b91c1c", va="center", zorder=3)

    # Mini tabla de pagos dentro del panel
    n_e, n_a = len(m.ids_est), len(m.ids_alt)
    x0, y0, cw, ch = 0.06, 0.225, 0.20, 0.042
    ax.text(x0, y0 + ch / 2, "Alternativa \\ Estado", fontsize=9, fontweight="bold",
            va="center", zorder=3)
    for j, s in enumerate(m.ids_est):
        ax.text(x0 + 0.24 + j * cw, y0 + ch / 2, f"{s} · {m.nombre_est[s]}",
                fontsize=9, fontweight="bold", ha="center", va="center", zorder=3)
        ax.text(x0 + 0.24 + j * cw, y0 + ch / 2 - 0.022, f"P = {num(m.prior[s])}",
                fontsize=8.2, ha="center", va="center", color="#64748b", zorder=3)
    for i, a in enumerate(m.ids_alt):
        yy = y0 - 0.055 - i * ch
        ax.text(x0, yy, f"{a} · {m.nombre_alt[a]}", fontsize=9, va="center", zorder=3)
        for j, s in enumerate(m.ids_est):
            ax.text(x0 + 0.24 + j * cw, yy, dinero(m.pagos[a][s]), fontsize=9.5,
                    ha="center", va="center", fontweight="bold", zorder=3)

    ax.text(0.615, 0.205, _envolver(
        f"Todos los valores están expresados en {c.UNIDAD_CORTA} de utilidad operativa por "
        f"jornada de sábado. A partir ÚNICAMENTE de esta matriz y de las probabilidades "
        f"mostradas, el programa calcula de forma automática los 13 pasos del estudio: "
        f"criterios, ecuaciones, sensibilidad, puntos de corte, EVPI, Bayes, árboles de "
        f"decisión, EVSI, eficiencia y la recomendación final.", 60),
        fontsize=8.9, va="top", color=GRIS_TEXTO, linespacing=1.5, zorder=3)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return _guardar(fig, carpeta, "01_contexto.png")


# =====================================================================
#  2. MATRIZ DE PAGOS Y CRITERIOS
# =====================================================================
def figura_matriz_criterios(m: ModeloDecision, carpeta: str) -> str:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12.5, 8),
                                   gridspec_kw={"height_ratios": [1, 1.15]})
    fig.suptitle("Pasos 1 y 2 — Matriz de pagos y criterios bajo incertidumbre",
                 fontsize=14, fontweight="bold", y=0.985)

    # --- Matriz de pagos como heatmap anotado ---
    datos = [[m.pagos[a][s] for s in m.ids_est] for a in m.ids_alt]
    im = ax1.imshow(datos, cmap="RdYlGn" if m.objetivo == "max" else "RdYlGn_r",
                    aspect="auto", alpha=0.75)
    ax1.set_xticks(range(len(m.ids_est)))
    ax1.set_xticklabels([f"{s}\n{m.nombre_est[s]}\nP = {num(m.prior[s])}" for s in m.ids_est],
                        fontsize=10)
    ax1.set_yticks(range(len(m.ids_alt)))
    ax1.set_yticklabels([f"{a}\n{m.nombre_alt[a]}" for a in m.ids_alt], fontsize=10)
    for i, a in enumerate(m.ids_alt):
        for j, s in enumerate(m.ids_est):
            ax1.text(j, i, dinero(m.pagos[a][s]), ha="center", va="center",
                     fontsize=12, fontweight="bold")
    ax1.set_title("Matriz de pagos (utilidad del sábado)", fontsize=11, pad=10)
    fig.colorbar(im, ax=ax1, fraction=0.025, pad=0.02)

    # --- Criterios como barras agrupadas ---
    ancho = 0.8 / len(m.criterios)
    xs = range(len(m.ids_alt))
    for k, crit in enumerate(m.criterios):
        vals = [crit.valores[a] for a in m.ids_alt]
        pos = [x + k * ancho - 0.4 + ancho / 2 for x in xs]
        barras = ax2.bar(pos, vals, ancho * 0.92, label=crit.nombre.split("(")[0].strip(),
                         color=PALETA[k % len(PALETA)], alpha=0.88,
                         edgecolor="white", linewidth=1.2)
        for a, b in zip(m.ids_alt, barras):
            elegida = a == crit.elegida
            ax2.text(b.get_x() + b.get_width() / 2, b.get_height(),
                     f"{num(b.get_height(), 0)}" + ("\n★" if elegida else ""),
                     ha="center", va="bottom", fontsize=8.5,
                     fontweight="bold" if elegida else "normal",
                     color=VERDE if elegida else GRIS_TEXTO)
    ax2.set_xticks(list(xs))
    ax2.set_xticklabels([f"{a} · {m.nombre_alt[a]}" for a in m.ids_alt], fontsize=10)
    ax2.set_ylabel(f"Valor del criterio ({CFG.UNIDAD_CORTA})")
    ax2.set_title("Comparación de criterios — ★ marca la alternativa elegida por cada criterio",
                  fontsize=11, pad=10)
    ax2.legend(fontsize=9, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    ax2.grid(axis="y", alpha=0.3, linestyle=":")
    ax2.set_axisbelow(True)
    for lado in ("top", "right"):
        ax2.spines[lado].set_visible(False)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return _guardar(fig, carpeta, "02_matriz_criterios.png")


# =====================================================================
#  3. ANÁLISIS GRÁFICO Y PUNTOS DE CORTE  (pasos 4, 5 y 6)
# =====================================================================
def figura_sensibilidad(m: ModeloDecision, carpeta: str) -> str:
    if len(m.estados) != 2:
        return ""
    s1, s2 = m.ids_est
    col = _colores(m.ids_alt)

    fig, ax = plt.subplots(figsize=(12.5, 7.4))
    ps = [i / 500 for i in range(501)]

    # Regiones de dominancia
    for t in m.tramos:
        ax.axvspan(t.p_ini, t.p_fin, color=col[t.dominante], alpha=0.07, zorder=0)
        ax.text((t.p_ini + t.p_fin) / 2, 0.035,
                f"Óptima: {t.dominante} · {m.nombre_alt[t.dominante]}",
                transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=col[t.dominante],
                bbox=dict(boxstyle="round,pad=0.35", fc="white",
                          ec=col[t.dominante], alpha=0.9))

    # Rectas
    for a in m.ids_alt:
        ys = [m.ev_en(a, p) for p in ps]
        ax.plot(ps, ys, lw=2.8, color=col[a], zorder=3,
                label=f"EV({a}) = {m.rectas[a]['ecuacion'].split('= ')[1]}   ·   {m.nombre_alt[a]}")
        for p_ext in (0.0, 1.0):
            v = m.ev_en(a, p_ext)
            ax.plot(p_ext, v, "o", ms=7, color=col[a], zorder=4)
            ax.annotate(f"({int(p_ext)} , {num(v, 0)})",
                        (p_ext, v), textcoords="offset points",
                        xytext=(8 if p_ext == 0 else -8, 10),
                        ha="left" if p_ext == 0 else "right",
                        fontsize=9, color=col[a], fontweight="bold")

    # Puntos de corte
    for c in m.cortes_validos:
        ax.plot(c.p, c.valor, "o", ms=11, mfc="white", mec="black", mew=2.2, zorder=6)
        ax.axvline(c.p, color="black", ls="--", lw=1.2, alpha=0.6, zorder=2)
        ax.annotate(f"PUNTO DE CORTE\n{c.a} = {c.b}\np = {num(c.p, 4)}  ({pct(c.p)})\n"
                    f"EV = {dinero(c.valor)}",
                    (c.p, c.valor), textcoords="offset points", xytext=(18, -62),
                    fontsize=9.5, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.5", fc="#fef9c3", ec="#ca8a04", lw=1.5),
                    arrowprops=dict(arrowstyle="->", color="#ca8a04", lw=1.6))

    # Situación actual
    p_act = m.prior[s1]
    ax.axvline(p_act, color=VERDE, lw=2.2, alpha=0.85, zorder=5)
    y_act = m.ev_en(m.alt_optima_prior, p_act)
    ax.plot(p_act, y_act, "*", ms=20, color=VERDE, zorder=7)
    ax.annotate(f"SITUACIÓN ACTUAL\nP({s1}) = {pct(p_act, 0)}\n"
                f"Óptima: {m.alt_optima_prior} · {dinero(y_act)}",
                (p_act, y_act), textcoords="offset points", xytext=(-150, 40),
                fontsize=9.5, fontweight="bold", color="#065f46",
                bbox=dict(boxstyle="round,pad=0.5", fc="#d1fae5", ec=VERDE, lw=1.5),
                arrowprops=dict(arrowstyle="->", color=VERDE, lw=1.6))

    ax.set_xlabel(f"p = P({s1}) — {m.nombre_est[s1]}        [ P({s2}) = 1 − p ]",
                  fontsize=11.5, labelpad=10)
    ax.set_ylabel(f"Valor esperado ({CFG.UNIDAD_CORTA})", fontsize=11.5)
    ax.set_title("Pasos 4, 5 y 6 — Análisis de sensibilidad, análisis gráfico y punto de corte",
                 fontsize=14, fontweight="bold", pad=16)
    ax.set_xlim(-0.02, 1.02)
    ax.grid(alpha=0.3, linestyle=":")
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(fontsize=10, loc="upper left", framealpha=0.95)

    u = m.umbral_decisorio
    if u:
        otra = u.b if u.a == m.alt_optima_prior else u.a
        direccion = "superar" if p_act < u.p else "caer por debajo de"
        fig.text(0.5, -0.015,
                 f"Lectura: la decisión óptima solo cambiaría a {otra} ({m.nombre_alt[otra]}) "
                 f"si P({s1}) llegara a {direccion} {pct(u.p)}. "
                 f"Con el {pct(p_act, 0)} estimado, la decisión {m.alt_optima_prior} se mantiene "
                 f"con un margen de {num(abs(p_act - u.p) * 100)} puntos porcentuales.",
                 ha="center", fontsize=10.5, style="italic", color="#334155")
    fig.tight_layout()
    return _guardar(fig, carpeta, "03_sensibilidad.png")


# =====================================================================
#  4. ÁRBOLES DE DECISIÓN  (paso 10)
# =====================================================================
def _layout(nodo: dict, prof: int, contador: list[int],
            pos: dict, niveles: dict) -> float:
    """Asigna coordenadas (x = profundidad, y = orden de hojas)."""
    niveles.setdefault(prof, []).append(id(nodo))
    hijos = nodo.get("hijos") or []
    if not hijos:
        y = float(contador[0]); contador[0] += 1
    else:
        ys = [_layout(h, prof + 1, contador, pos, niveles) for h in hijos]
        y = sum(ys) / len(ys)
    pos[id(nodo)] = (prof, y)
    return y


def _hojas(nodo: dict) -> int:
    hijos = nodo.get("hijos") or []
    return 1 if not hijos else sum(_hojas(h) for h in hijos)


def _prof_max(nodo: dict) -> int:
    hijos = nodo.get("hijos") or []
    return 0 if not hijos else 1 + max(_prof_max(h) for h in hijos)


def figura_arbol(m: ModeloDecision, arbol: dict, titulo: str, subtitulo: str,
                 carpeta: str, nombre: str) -> str:
    pos: dict = {}
    niveles: dict = {}
    _layout(arbol, 0, [0], pos, niveles)
    n_hojas, n_niv = _hojas(arbol), _prof_max(arbol) + 1

    alto = max(6.0, n_hojas * 1.05 + 2.2)
    ancho = max(12.0, n_niv * 3.6)
    fig, ax = plt.subplots(figsize=(ancho, alto))
    ax.axis("off")

    dx = 1.0                       # separación horizontal entre niveles
    radio = 0.17                   # "radio" lógico de los nodos en X
    W_HOJA, H_HOJA = 0.34, 0.34    # tamaño de las hojas

    def borde_der(nodo, x):
        return x * dx + radio

    def borde_izq(nodo, x):
        return x * dx - (W_HOJA / 2 if nodo["tipo"] == "hoja" else radio)

    def dibujar(nodo: dict, padre: dict | None = None):
        x, y = pos[id(nodo)]
        tipo = nodo["tipo"]
        optimo = nodo.get("optimo", False)

        # ---------- Conexión ortogonal con el padre ----------
        if padre is not None:
            px, py = pos[id(padre)]
            color_l = VERDE if optimo else "#94a3b8"
            grosor = 2.8 if optimo else 1.5
            z = 3 if optimo else 2
            x_ini = borde_der(padre, px)
            x_fin = borde_izq(nodo, x)
            x_codo = x_ini + (x_fin - x_ini) * 0.42
            ax.plot([x_ini, x_codo], [py, py], color=color_l, lw=grosor,
                    solid_capstyle="round", zorder=z)
            ax.plot([x_codo, x_codo], [py, y], color=color_l, lw=grosor,
                    solid_capstyle="round", zorder=z)
            ax.plot([x_codo, x_fin], [y, y], color=color_l, lw=grosor,
                    solid_capstyle="round", zorder=z)

            # Etiqueta de la rama
            partes = [p for p in (nodo.get("rama", ""),
                                  nodo["etiqueta"] if tipo != "azar" else "") if p]
            etiqueta = "\n".join(partes) if tipo == "hoja" else nodo.get("rama", "")
            if tipo == "azar":
                etiqueta = f"{nodo.get('rama', '')} · {nodo['etiqueta']}"
            if etiqueta:
                ax.text((x_codo + x_fin) / 2, y - 0.09, etiqueta, ha="center",
                        va="bottom", fontsize=8.0,
                        fontweight="bold" if optimo else "normal",
                        color="#065f46" if optimo else "#334155",
                        bbox=dict(boxstyle="round,pad=0.24", fc="white",
                                  ec=VERDE if optimo else "#e2e8f0",
                                  lw=1.1 if optimo else 0.8, alpha=0.96), zorder=5)

        # ---------- Nodo ----------
        if tipo == "decision":
            ax.plot(x * dx, y, marker="s", ms=26, mfc="#dbeafe", mec=AZUL,
                    mew=2.2, ls="", zorder=6)
            ax.text(x * dx, y + 0.27, nodo["etiqueta"].replace("\n", " "),
                    ha="center", va="top", fontsize=8.8, fontweight="bold",
                    color=AZUL, zorder=6)
        elif tipo == "azar":
            ax.plot(x * dx, y, marker="o", ms=26, mfc="#fef3c7", mec="#b45309",
                    mew=2.2, ls="", zorder=6)
        else:   # hoja
            ax.add_patch(FancyBboxPatch((x * dx - W_HOJA / 2, y - H_HOJA / 2),
                                        W_HOJA, H_HOJA,
                                        boxstyle="round,pad=0.015,rounding_size=0.05",
                                        facecolor="#f1f5f9", edgecolor="#64748b",
                                        lw=1.3, zorder=6))
            ax.text(x * dx, y, num(nodo["valor"], 0), ha="center", va="center",
                    fontsize=9.2, fontweight="bold", zorder=7)

        # ---------- Valor calculado bajo el nodo ----------
        if tipo != "hoja":
            destacar = optimo or padre is None
            ax.text(x * dx, y - 0.26, num(nodo["valor"], 2), ha="center", va="bottom",
                    fontsize=9.0, fontweight="bold",
                    color=VERDE if destacar else "#475569",
                    bbox=dict(boxstyle="round,pad=0.20",
                              fc="#ecfdf5" if destacar else "white",
                              ec=VERDE if destacar else "#e2e8f0", lw=1.0),
                    zorder=6)

        for h in (nodo.get("hijos") or []):
            dibujar(h, nodo)

    dibujar(arbol)

    ax.set_xlim(-0.55, (n_niv - 1) * dx + 0.55)
    ax.set_ylim(-0.95, n_hojas - 0.05)
    ax.invert_yaxis()
    ax.set_title(titulo, fontsize=14.5, fontweight="bold", pad=26)
    ax.text(0.5, 1.018, subtitulo, transform=ax.transAxes, ha="center",
            fontsize=10.2, color="#475569")

    leyenda = [
        Line2D([], [], marker="s", ls="", ms=11, mfc="#dbeafe", mec=AZUL,
               label="Nodo de decisión (lo controla la empresa)"),
        Line2D([], [], marker="o", ls="", ms=11, mfc="#fef3c7", mec="#b45309",
               label="Nodo de azar (lo controla el entorno regulatorio)"),
        Line2D([], [], color=VERDE, lw=2.6, label="Rama óptima (inducción hacia atrás)"),
    ]
    ax.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=3, fontsize=9, frameon=False)
    fig.tight_layout()
    return _guardar(fig, carpeta, nombre)


def figura_arbol_prior(m: ModeloDecision, carpeta: str) -> str:
    return figura_arbol(
        m, m.arbol_prior(), "Paso 10 — Árbol de decisión SIN información muestral",
        f"Decisión inicial con las probabilidades a priori · Valor en la raíz: "
        f"{dinero(m.ev_optimo_prior)} · Alternativa óptima: {m.alt_optima_prior}",
        carpeta, "04_arbol_prior.png")


def figura_arbol_muestral(m: ModeloDecision, carpeta: str) -> str:
    return figura_arbol(
        m, m.arbol_muestral(), "Paso 10 — Árbol de decisión CON información muestral",
        f"Decisión condicionada al resultado del estudio (probabilidades de Bayes) · "
        f"Valor en la raíz: {dinero(m.ev_con_info_muestral)}",
        carpeta, "05_arbol_muestral.png")


# =====================================================================
#  5. REVISIÓN BAYESIANA  (paso 9)
# =====================================================================
def figura_bayes(m: ModeloDecision, carpeta: str) -> str:
    n = len(m.ramas)
    fig, axes = plt.subplots(1, n + 1, figsize=(4.3 * (n + 1), 5.4), sharey=True)
    axes = list(axes) if n + 1 > 1 else [axes]
    col = _colores(m.ids_est)

    # Panel de probabilidades a priori
    ax = axes[0]
    ax.bar([m.nombre_est[s] for s in m.ids_est], [m.prior[s] for s in m.ids_est],
           color=[col[s] for s in m.ids_est], alpha=0.85, edgecolor="white", lw=1.5)
    for i, s in enumerate(m.ids_est):
        ax.text(i, m.prior[s], pct(m.prior[s], 1), ha="center", va="bottom",
                fontsize=11, fontweight="bold")
    ax.set_title("A PRIORI\n(sin estudio)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Probabilidad")
    ax.set_ylim(0, 1.1)

    # Paneles posteriores
    for k, r in enumerate(m.ramas, start=1):
        ax = axes[k]
        ax.bar([m.nombre_est[s] for s in m.ids_est],
               [r.posteriores[s] for s in m.ids_est],
               color=[col[s] for s in m.ids_est], alpha=0.85, edgecolor="white", lw=1.5)
        for i, s in enumerate(m.ids_est):
            delta = r.posteriores[s] - m.prior[s]
            flecha = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
            ax.text(i, r.posteriores[s], f"{pct(r.posteriores[s], 1)}\n{flecha} {pct(abs(delta), 1)}",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")
        cambia = r.elegida != m.alt_optima_prior
        ax.set_title(f"POSTERIOR · Estudio {r.nombre.upper()}\n"
                     f"P({r.indicador}) = {num(r.prob_indicador, 4)}",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel(f"Decisión: {r.elegida} · {m.nombre_alt[r.elegida]}\n"
                      f"EV = {dinero(r.valor)}\n"
                      + ("↺ LA DECISIÓN CAMBIA" if cambia else "✔ SE RATIFICA"),
                      fontsize=9.5, fontweight="bold",
                      color=ROJO if cambia else VERDE, labelpad=10)

    for ax in axes:
        ax.grid(axis="y", alpha=0.3, ls=":")
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.tick_params(labelsize=9)

    fig.suptitle("Pasos 8 y 9 — Revisión bayesiana de las probabilidades",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return _guardar(fig, carpeta, "06_bayes.png")


# =====================================================================
#  6. TABLERO FINAL  (pasos 7, 11, 12 y 13)
# =====================================================================
def figura_resumen(m: ModeloDecision, carpeta: str) -> str:
    fig = plt.figure(figsize=(13.5, 8.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.42, wspace=0.26)

    # --- Escalera de valores esperados ---
    ax = fig.add_subplot(gs[0, 0])
    etiquetas = ["EV sin\ninformación", "EV con estudio\n(muestral)", "EV con información\nperfecta"]
    valores = [m.ev_sin_info_muestral, m.ev_con_info_muestral, m.ev_con_info_perfecta]
    barras = ax.bar(etiquetas, valores, color=["#64748b", "#2563eb", "#059669"],
                    alpha=0.9, edgecolor="white", lw=1.5)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, v, dinero(v), ha="center",
                va="bottom", fontsize=9.5, fontweight="bold")
    lo, hi = min(valores), max(valores)
    ax.set_ylim(lo - (hi - lo) * 0.8 - 1, hi + (hi - lo) * 0.35 + 1)
    ax.set_title("Paso 11 — Escalera del valor de la información", fontsize=11.5,
                 fontweight="bold")
    ax.set_ylabel(CFG.UNIDAD_CORTA)
    ax.grid(axis="y", alpha=0.3, ls=":"); ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    # --- EVSI vs EVPI ---
    ax = fig.add_subplot(gs[0, 1])
    ax.barh(["EVPI\n(información perfecta)", "EVSI\n(información muestral)"],
            [m.evpi, m.evsi], color=["#059669", "#2563eb"], alpha=0.9,
            edgecolor="white", lw=1.5)
    for i, v in enumerate([m.evpi, m.evsi]):
        ax.text(v + m.evpi * 0.02, i, dinero(v), va="center", fontsize=10,
                fontweight="bold")
    ax.set_xlim(0, m.evpi * 1.35)
    ax.set_title(f"Paso 12 — Eficiencia del estudio = {pct(m.eficiencia)} "
                 f"({m.calificacion_eficiencia})", fontsize=11.5, fontweight="bold")
    ax.grid(axis="x", alpha=0.3, ls=":"); ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    # --- Conclusión ---
    ax = fig.add_subplot(gs[1, :]); ax.axis("off")
    recomienda = m.recomienda_estudio
    ax.add_patch(FancyBboxPatch((0.005, 0.02), 0.99, 0.96,
                                boxstyle="round,pad=0.012,rounding_size=0.02",
                                transform=ax.transAxes,
                                facecolor="#ecfdf5" if not recomienda else "#eff6ff",
                                edgecolor=VERDE if not recomienda else "#2563eb",
                                lw=2, zorder=1))
    ax.text(0.5, 0.90, "PASO 13 — DECISIÓN FINAL DEL TOMADOR DE DECISIONES",
            transform=ax.transAxes, ha="center", fontsize=12.5, fontweight="bold",
            color="#065f46" if not recomienda else "#1e3a8a", zorder=3)

    izq = [
        f"Alternativa seleccionada:  {m.alt_optima_prior} — {m.nombre_alt[m.alt_optima_prior]}",
        f"Utilidad esperada:  {dinero(m.ev_optimo_prior)}",
        f"Umbral de cambio de decisión:  "
        + (pct(m.umbral_decisorio.p) if m.umbral_decisorio else "no aplica"),
    ]
    der = [
        f"EVPI (información perfecta):  {dinero(m.evpi)}",
        f"EVSI (estudio/consultoría):  {dinero(m.evsi)}",
        f"Eficiencia:  {pct(m.eficiencia)}  ·  ¿Contratar la consultoría?:  "
        f"{'SÍ' if recomienda else 'NO'}",
    ]
    ax.text(0.04, 0.76, "\n\n".join(izq), transform=ax.transAxes, fontsize=10,
            va="top", linespacing=1.3, zorder=3)
    ax.text(0.53, 0.76, "\n\n".join(der), transform=ax.transAxes, fontsize=10,
            va="top", linespacing=1.3, zorder=3)
    ax.text(0.04, 0.40, "Criterios bajo incertidumbre:  "
            + "   ·   ".join(f"{c.nombre.split('(')[0].strip()} → {c.elegida}"
                             for c in m.criterios),
            transform=ax.transAxes, fontsize=9.6, va="top", zorder=3)

    veredicto = m.texto_decision_final()[-1] if not m.cambia_decision_con_estudio \
        else m.texto_decision_final()[-2]
    ax.text(0.04, 0.29, _envolver(veredicto.split(". ", 1)[-1], 150),
            transform=ax.transAxes, fontsize=9.3, va="top", style="italic",
            color="#334155", linespacing=1.5, zorder=3)

    fig.suptitle("Pasos 7, 11, 12 y 13 — Valor de la información y conclusión gerencial",
                 fontsize=14, fontweight="bold", y=0.985)
    return _guardar(fig, carpeta, "07_resumen.png")


# =====================================================================
#  ORQUESTADOR
# =====================================================================
def generar_todas(m: ModeloDecision, carpeta: str) -> dict[str, str]:
    return {
        "contexto": figura_contexto(m, carpeta),
        "matriz": figura_matriz_criterios(m, carpeta),
        "sensibilidad": figura_sensibilidad(m, carpeta),
        "arbol_prior": figura_arbol_prior(m, carpeta),
        "arbol_muestral": figura_arbol_muestral(m, carpeta),
        "bayes": figura_bayes(m, carpeta),
        "resumen": figura_resumen(m, carpeta),
    }