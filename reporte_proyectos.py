# -*- coding: utf-8 -*-
from __future__ import annotations
from proyectos import ModeloProyecto
from modelo import num, pct
from reporte import marco, parrafo, tabla

def reporte_proyecto(m: ModeloProyecto) -> str:
    cuerpo = [
        "CONTEXTO",
        m.cfg.CONTEXTO_PROYECTO,
        "",
        "RESULTADOS GLOBALES",
        f"Duración esperada del proyecto (Ruta Crítica): {num(m.duracion_total, 2)} minutos.",
        f"Desviación estándar (σ): {num(m.sigma, 2)} minutos.",
        f"Probabilidad de terminar en <= {m.cfg.TIEMPO_META} min: {pct(m.probabilidad)}",
        "",
        "RUTA CRÍTICA",
        " -> ".join(m.criticas)
    ]
    
    txt = [marco(m.cfg.TITULO_PROYECTO.upper(), cuerpo, doble=True), ""]
    
    filas = []
    for id in m.orden:
        a = m.actividades[id]
        filas.append([id, a.nombre, num(a.te, 2), num(a.es, 2), num(a.ef, 2), 
                      num(a.ls, 2), num(a.lf, 2), num(a.holgura, 2), "SÍ" if a.es_critica else "NO"])
    
    txt.append("TABLA DE TIEMPOS Y HOLGURAS")
    txt.append(tabla(["ID", "Actividad", "TE", "ES", "EF", "LS", "LF", "Holgura", "Crítica"], filas, alinear_izq=2))
    
    return "\n".join(txt)