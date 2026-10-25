# -*- coding: utf-8 -*-
"""
=====================================================================
 GRÁFICAS — DIRECCIÓN DE PROYECTOS
=====================================================================
"""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import math

from proyectos import ModeloProyecto
from modelo import num, pct
from graficas import _guardar, GRIS_BORDE, GRIS_TEXTO, AZUL, VERDE, ROJO

AMBAR = "#d97706"
MORADO = "#7c3aed"

def figura_red(m: ModeloProyecto, carpeta):
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")

    # 1. Calcular niveles (X) de cada actividad
    niveles = {}
    for id in m.orden:
        a = m.actividades[id]
        if not a.pre:
            niveles[id] = 0
        else:
            niveles[id] = max(niveles[pre] for pre in a.pre) + 1

    nodos_por_nivel = {}
    for id, n in niveles.items():
        nodos_por_nivel.setdefault(n, []).append(id)

    # 2. Asignar posiciones (Y) intentando minimizar cruces (Algoritmo del Baricentro)
    pos = {}
    ancho_caja = 2.4
    alto_caja = 1.2
    dist_x = 4.5   # Separación horizontal entre columnas
    dist_y = 2.5   # Separación vertical entre filas

    for n in sorted(nodos_por_nivel.keys()):
        nodos = nodos_por_nivel[n]
        
        # Ordenar las cajas según el promedio de la posición Y de sus predecesoras
        def peso_baricentro(id):
            pres = m.actividades[id].pre
            if not pres: return 0
            return sum(pos[p][1] for p in pres) / len(pres)
        
        nodos.sort(key=peso_baricentro)
        
        # Calcular Y centrando el grupo en el eje
        num_nodos = len(nodos)
        for i, id in enumerate(nodos):
            y = (i - num_nodos / 2) * dist_y
            x = n * dist_x
            pos[id] = (x, y)

    # 3. Dibujar las flechas (con codos y colores de ruta crítica)
    for id, a in m.actividades.items():
        x2, y2 = pos[id]
        for pre in a.pre:
            x1, y1 = pos[pre]
            
            # Puntos de conexión en los bordes de las cajas
            inicio = (x1 + ancho_caja/2, y1)
            fin = (x2 - ancho_caja/2, y2)
            
            es_critica = a.es_critica and m.actividades[pre].es_critica
            color_flecha = ROJO if es_critica else "#94a3b8"
            grosor = 2.0 if es_critica else 1.2

            # Si están a la misma altura, flecha recta
            if abs(y1 - y2) < 0.1:
                ax.annotate("", xy=fin, xytext=inicio,
                            arrowprops=dict(arrowstyle="-|>", color=color_flecha, 
                                            lw=grosor, shrinkA=0, shrinkB=0))
            else:
                # Si no, hacer un codo (línea recta horizontal, vertical, horizontal)
                x_medio = (inicio[0] + fin[0]) / 2
                # Segmento horizontal 1
                ax.plot([inicio[0], x_medio], [inicio[1], inicio[1]], color=color_flecha, lw=grosor)
                # Segmento vertical
                ax.plot([x_medio, x_medio], [inicio[1], fin[1]], color=color_flecha, lw=grosor)
                # Segmento horizontal 2 (con la flecha)
                ax.annotate("", xy=fin, xytext=(x_medio, fin[1]),
                            arrowprops=dict(arrowstyle="-|>", color=color_flecha, 
                                            lw=grosor, shrinkA=0, shrinkB=0))

    # 4. Dibujar los nodos (cajas)
    for id, a in m.actividades.items():
        x, y = pos[id]
        critica = a.es_critica
        color_borde = ROJO if critica else AZUL
        color_fondo = "#fef2f2" if critica else "#eff6ff"
        
        # Dibujar caja
        rect = FancyBboxPatch((x - ancho_caja/2, y - alto_caja/2), ancho_caja, alto_caja,
                              boxstyle="round,pad=0.1,rounding_size=0.2",
                              fc=color_fondo, ec=color_borde, lw=2.5 if critica else 1.5, zorder=4)
        ax.add_patch(rect)

        # Textos dentro de la caja
        ax.text(x, y + 0.3, f"{id}", ha="center", va="center", 
                fontsize=14, fontweight="bold", color=color_borde, zorder=5)
        ax.text(x, y - 0.05, f"TE={num(a.te, 1)}", ha="center", va="center", 
                fontsize=10, fontweight="bold", color="#334155", zorder=5)
        ax.text(x, y - 0.35, f"ES:{num(a.es, 1)} | EF:{num(a.ef, 1)}", ha="center", va="center", 
                fontsize=9, color="#64748b", zorder=5)

    # Ajustar límites del gráfico para que no queden bordes apretados
    if pos:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        ax.set_xlim(min(xs) - 2.5, max(xs) + 2.5)
        ax.set_ylim(min(ys) - 2.5, max(ys) + 2.5)

    ax.set_title("Red del Proyecto (AON) — Nodos rojos = Ruta Crítica", 
                 fontsize=15, fontweight="bold", pad=20)
    fig.tight_layout()
    return _guardar(fig, carpeta, "19_proyecto_red.png")

def figura_gantt(m: ModeloProyecto, carpeta):
    fig, ax = plt.subplots(figsize=(10, 6))
    ids = [id for id in m.orden if m.actividades[id].pre or True]
    
    for i, id in enumerate(ids):
        a = m.actividades[id]
        color = ROJO if a.es_critica else AZUL
        ax.barh(i, a.te, left=a.es, height=0.4, color=color, alpha=0.8)
        # Holgura
        if a.holgura > 0:
            ax.barh(i, a.holgura, left=a.ef, height=0.4, color="#cbd5e1", alpha=0.8, hatch="//")

    ax.set_yticks(range(len(ids)))
    ax.set_yticklabels([f"{id} - {m.actividades[id].nombre}" for id in ids])
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo (minutos)")
    ax.set_title("Diagrama de Gantt — Holguras y Ruta Crítica", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3, ls=":")
    fig.tight_layout()
    return _guardar(fig, carpeta, "20_proyecto_gantt.png")