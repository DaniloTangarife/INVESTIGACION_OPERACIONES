# -*- coding: utf-8 -*-
"""
=====================================================================
 MOTOR DE CÁLCULO — DIRECCIÓN DE PROYECTOS (CPM / PERT)
=====================================================================
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
import config_proyectos as CP

@dataclass
class Actividad:
    id: str
    nombre: str
    pre: list[str]
    O: float
    M: float
    P: float
    te: float = 0.0
    varianza: float = 0.0
    es: float = 0.0
    ef: float = 0.0
    ls: float = 0.0
    lf: float = 0.0
    holgura: float = 0.0
    es_critica: bool = False

class ModeloProyecto:
    def __init__(self, cfg=CP):
        self.cfg = cfg
        self.actividades = {a["id"]: Actividad(**a) for a in cfg.ACTIVIDADES}
        self._calcular_pert()
        self.orden = self._orden_topologico()
        self._forward_pass()
        self._backward_pass()
        self._ruta_critica()
        self._calcular_probabilidad()

    def _calcular_pert(self):
        for a in self.actividades.values():
            a.te = (a.O + 4 * a.M + a.P) / 6
            a.varianza = ((a.P - a.O) / 6) ** 2

    def _orden_topologico(self):
        # Algoritmo de Kahn para ordenar las actividades
        in_degree = {id: len(a.pre) for id, a in self.actividades.items()}
        queue = [id for id, deg in in_degree.items() if deg == 0]
        orden = []
        
        while queue:
            u = queue.pop(0)
            orden.append(u)
            for v in self.actividades:
                if u in self.actividades[v].pre:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)
        
        if len(orden) != len(self.actividades):
            raise ValueError("Hay un ciclo en la red del proyecto.")
        return orden

    def _forward_pass(self):
        for id in self.orden:
            a = self.actividades[id]
            if not a.pre:
                a.es = 0
            else:
                a.es = max(self.actividades[pre].ef for pre in a.pre)
            a.ef = a.es + a.te
        self.duracion_total = max(a.ef for a in self.actividades.values())

    def _backward_pass(self):
        for id in reversed(self.orden):
            a = self.actividades[id]
            sucesoras = [s for s in self.actividades.values() if id in s.pre]
            if not sucesoras:
                a.lf = self.duracion_total
            else:
                a.lf = min(s.ls for s in sucesoras)
            a.ls = a.lf - a.te
            a.holgura = a.ls - a.es

    def _ruta_critica(self):
        self.criticas = []
        for a in self.actividades.values():
            if abs(a.holgura) < 1e-9:
                a.es_critica = True
                self.criticas.append(a.id)
        self.criticas.sort(key=lambda x: self.actividades[x].es)

    def _calcular_probabilidad(self):
        varianza_total = sum(self.actividades[id].varianza for id in self.criticas)
        self.sigma = math.sqrt(varianza_total)
        if self.sigma > 0:
            z = (self.cfg.TIEMPO_META - self.duracion_total) / self.sigma
            self.probabilidad = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        else:
            self.probabilidad = 1.0 if self.duracion_total <= self.cfg.TIEMPO_META else 0.0