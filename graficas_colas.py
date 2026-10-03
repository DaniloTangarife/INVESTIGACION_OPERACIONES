# -*- coding: utf-8 -*-
"""
=====================================================================
 GRÁFICAS — TEORÍA DE COLAS
=====================================================================
Todas las figuras se dibujan a partir del objeto ModeloColas.
=====================================================================
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from colas import ModeloColas, _num as num, _pct as pct

from graficas import _guardar, GRIS_BORDE, GRIS_TEXTO, AZUL, VERDE, ROJO

AMBAR = "#d97706"
MORADO = "#7c3aed"


# =====================================================================
#  1. COMPARACIÓN DE LOS 7 INDICADORES
# =====================================================================
def figura_comparacion(m: ModeloColas, carpeta):
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.5))
    axes = axes.flatten()

    indicadores = [
        ("P0", "Prob. sistema vacío", "p0", "%"),
        ("Lq", "Clientes en cola", "lq", "clientes"),
        ("L", "Clientes en sistema", "l", "clientes"),
        ("Wq", "Tiempo en cola", "wq", "minutos"),
        ("W", "Tiempo en sistema", "w", "minutos"),
        ("Pw", "Prob. de esperar", "pw", "%"),
        ("λ", "Tasa de llegada", "lambda_", "clientes/h"),
        ("μ", "Tasa de servicio", "mu", "clientes/h"),
    ]

    for ax, (simbolo, titulo, attr, unidad) in zip(axes, indicadores):
        va = getattr(m.actual, attr)
        vm = getattr(m.mejorado, attr)
        if unidad == "%":
            va *= 100
            vm *= 100
        if attr in ("wq", "w"):
            va *= 60
            vm *= 60

        barras = ax.bar(["Actual", "Mejorado"], [va, vm],
                        color=[ROJO, VERDE], alpha=0.85,
                        edgecolor="white", lw=1.5)
        for b, v in zip(barras, [va, vm]):
            txt = f"{num(v, 3)} {unidad}" if unidad != "%" else f"{num(v, 2)} %"
            ax.text(b.get_x() + b.get_width() / 2, v, txt,
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")
        ax.set_title(f"{simbolo} — {titulo}", fontsize=10.5, fontweight="bold")
        ax.grid(axis="y", alpha=0.3, ls=":")
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)

    fig.suptitle("Teoría de Colas · Comparación del sistema actual vs. mejorado",
                 fontsize=14, fontweight="bold")
    fig.text(0.5, 0.005,
             f"Sistema M/M/1 · λ = {num(m.actual.lambda_, 4)} clientes/h · "
             f"μ actual = {num(m.actual.mu, 4)} · μ mejorado = "
             f"{num(m.mejorado.mu, 4)} clientes/h",
             ha="center", fontsize=10, style="italic", color="#334155")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return _guardar(fig, carpeta, "13_colas_comparacion.png")


# =====================================================================
#  2. PROBABILIDAD DE N CLIENTES
# =====================================================================
def figura_pn(m: ModeloColas, carpeta):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ns = sorted(m.actual.pn.keys())
    va = [m.actual.pn[n] for n in ns]
    vm = [m.mejorado.pn[n] for n in ns]
    ancho = 0.38

    ax.bar([n - ancho / 2 for n in ns], va, ancho,
           label="Actual", color=ROJO, alpha=0.85, edgecolor="white")
    ax.bar([n + ancho / 2 for n in ns], vm, ancho,
           label="Mejorado", color=VERDE, alpha=0.85, edgecolor="white")

    for n, v in zip(ns, va):
        ax.text(n - ancho / 2, v, num(v, 4), ha="center", va="bottom", fontsize=7.5)
    for n, v in zip(ns, vm):
        ax.text(n + ancho / 2, v, num(v, 4), ha="center", va="bottom", fontsize=7.5)

    ax.set_xlabel("n — Número de clientes en el sistema")
    ax.set_ylabel("Probabilidad P(n)")
    ax.set_title("Teoría de Colas · Probabilidad de n clientes en el sistema",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(ns)
    ax.grid(axis="y", alpha=0.3, ls=":")
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend()
    fig.tight_layout()
    return _guardar(fig, carpeta, "14_colas_pn.png")


# =====================================================================
#  3. DIAGRAMA DE FLUJO DEL SISTEMA
# =====================================================================
def figura_flujo(m: ModeloColas, carpeta):
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)

    # Flecha de llegada
    ax.annotate("", xy=(1.5, 2), xytext=(0.3, 2),
                arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=3))
    ax.text(0.9, 2.35, f"λ = {num(m.actual.lambda_, 4)}\nclientes/h",
            ha="center", fontsize=10.5, fontweight="bold", color=AZUL)

    # Cola
    ax.add_patch(FancyBboxPatch((1.5, 1.2), 2.5, 1.6,
                                boxstyle="round,pad=0.08",
                                fc="#fef3c7", ec=AMBAR, lw=2))
    ax.text(2.75, 2.0, "COLA\n(Lq)", ha="center", va="center",
            fontsize=13, fontweight="bold", color="#b45309")

    # Servidor
    ax.add_patch(FancyBboxPatch((5.0, 1.2), 2.0, 1.6,
                                boxstyle="round,pad=0.08",
                                fc="#dbeafe", ec=AZUL, lw=2))
    ax.text(6.0, 2.0, f"SERVIDOR\n(μ = {num(m.actual.mu, 2)})",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=AZUL)

    # Conexiones
    ax.annotate("", xy=(5.0, 2), xytext=(4.0, 2),
                arrowprops=dict(arrowstyle="-|>", color=GRIS_TEXTO, lw=2))
    ax.annotate("", xy=(8.5, 2), xytext=(7.0, 2),
                arrowprops=dict(arrowstyle="-|>", color=VERDE, lw=3))
    ax.text(7.75, 2.3, "Salida", ha="center", fontsize=11,
            fontweight="bold", color=VERDE)

    # Pie
    ax.text(5.0, 0.5,
            f"Sistema M/M/1 · ρ = {pct(m.actual.rho)} · "
            f"Tiempo de servicio = {num(m.actual.tiempo_servicio, 0)} s · "
            f"Buses por día = {m.cfg.BUSES_POR_DIA}",
            ha="center", fontsize=10.5, style="italic", color=GRIS_TEXTO)

    ax.set_title("Teoría de Colas · Diagrama del sistema",
                 fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    return _guardar(fig, carpeta, "15_colas_flujo.png")


# =====================================================================
#  4. RESUMEN COMPARATIVO
# =====================================================================
def figura_resumen_colas(m: ModeloColas, carpeta):
    fig = plt.figure(figsize=(13.5, 7.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.42, wspace=0.25)

    # --- Utilización ρ ---
    ax = fig.add_subplot(gs[0, 0])
    ax.bar(["Actual", "Mejorado"], [m.actual.rho * 100, m.mejorado.rho * 100],
           color=[ROJO, VERDE], alpha=0.9, edgecolor="white", lw=1.5)
    for i, v in enumerate([m.actual.rho * 100, m.mejorado.rho * 100]):
        ax.text(i, v, f"{num(v, 2)} %", ha="center", va="bottom",
                fontsize=11, fontweight="bold")
    ax.set_ylabel("Utilización ρ (%)")
    ax.set_title("Utilización del sistema", fontsize=12, fontweight="bold")
    ax.grid(axis="y", alpha=0.3, ls=":")
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    # --- Reducciones ---
    ax = fig.add_subplot(gs[0, 1])
    etiquetas = ["Lq", "L", "Wq", "W"]
    valores = [m.mejora_lq, m.mejora_l, m.mejora_wq, m.mejora_w]
    ax.barh(etiquetas, valores, color="#2563eb", alpha=0.85,
            edgecolor="white", lw=1.2)
    for i, v in enumerate(valores):
        ax.text(v + 0.3, i, f"−{num(v, 2)} %", va="center",
                fontsize=10.5, fontweight="bold")
    ax.set_xlabel("Reducción porcentual (%)")
    ax.set_title("Impacto de la mejora", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.3, ls=":")
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.set_xlim(0, max(valores) * 1.35 if max(valores) > 0 else 1)

    # --- Panel de conclusión ---
    ax = fig.add_subplot(gs[1, :])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.005, 0.02), 0.99, 0.96,
                                boxstyle="round,pad=0.012,rounding_size=0.02",
                                transform=ax.transAxes, facecolor="#ecfdf5",
                                edgecolor=VERDE, lw=2, zorder=1))

    # Título
    ax.text(0.5, 0.92, "CONCLUSIÓN DE LA MEJORA EN EL SISTEMA DE COLAS",
            transform=ax.transAxes, ha="center", va="center", fontsize=12.5,
            fontweight="bold", color="#065f46", zorder=3)

    # Bloque izquierdo (3 líneas, separadas por un solo salto)
    izq = [
        f"λ (clientes/h):  {num(m.actual.lambda_, 4)}",
        f"μ actual:  {num(m.actual.mu, 4)}  →  μ mejorado:  {num(m.mejorado.mu, 4)}",
        f"Tiempo de servicio:  {num(m.actual.tiempo_servicio, 0)} s  →  "
        f"{num(m.mejorado.tiempo_servicio, 0)} s",
    ]
    ax.text(0.04, 0.78, "\n".join(izq), transform=ax.transAxes, fontsize=10,
            va="top", ha="left", linespacing=1.8, zorder=3, color="#0f172a")

    # Bloque derecho (3 líneas, separadas por un solo salto)
    der = [
        f"Lq:  {num(m.actual.lq, 4)}  →  {num(m.mejorado.lq, 4)}   "
        f"(−{num(m.mejora_lq, 2)} %)",
        f"Wq:  {num(m.actual.wq * 60, 2)} min  →  "
        f"{num(m.mejorado.wq * 60, 2)} min   (−{num(m.mejora_wq, 2)} %)",
        f"Pw:  {pct(m.actual.pw)}  →  {pct(m.mejorado.pw)}",
    ]
    ax.text(0.54, 0.78, "\n".join(der), transform=ax.transAxes, fontsize=10,
            va="top", ha="left", linespacing=1.8, zorder=3, color="#0f172a")

    # MEJORA PROPUESTA: en la parte inferior, bien separada
    ax.text(0.5, 0.10,
            "MEJORA PROPUESTA: lector de cédula + pago electrónico en el "
            "mismo puesto de venta. Sin contratar personal.",
            transform=ax.transAxes, fontsize=9.5, va="center", ha="center",
            fontweight="bold", color="#065f46", zorder=4)

    fig.suptitle("Teoría de Colas · Resumen del sistema actual vs. mejorado",
                 fontsize=14, fontweight="bold", y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return _guardar(fig, carpeta, "16_colas_resumen.png")


# =====================================================================
#  ORQUESTADOR
# =====================================================================
def generar_todas_colas(m: ModeloColas, carpeta) -> dict:
    return {
        "colas_comparacion": figura_comparacion(m, carpeta),
        "colas_pn": figura_pn(m, carpeta),
        "colas_flujo": figura_flujo(m, carpeta),
        "colas_resumen": figura_resumen_colas(m, carpeta),
    }