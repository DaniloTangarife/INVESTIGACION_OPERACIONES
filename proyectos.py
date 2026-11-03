# -*- coding: utf-8 -*-
"""
=====================================================================
 MOTOR DE CÁLCULO — DIRECCIÓN DE PROYECTOS (CPM / PERT)
=====================================================================
"""
from __future__ import annotations
import math
import copy
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
    Cn: float
    Tc: float
    Cc: float
    te: float = 0.0
    Tn: float = 0.0
    S: float = 0.0
    varianza: float = 0.0
    es: float = 0.0
    ef: float = 0.0
    ls: float = 0.0
    lf: float = 0.0
    holgura: float = 0.0
    es_critica: bool = False
    tiempo_actual: float = 0.0

class ModeloProyecto:
    def __init__(self, cfg=CP):
        self.cfg = cfg
        self.actividades = {}
        self.iteraciones_crashing = []
        
        for a in cfg.ACTIVIDADES:
            act = Actividad(**a)
            act.te = (act.O + 4 * act.M + act.P) / 6
            act.Tn = act.te # El tiempo normal es el TE del PERT
            act.tiempo_actual = act.Tn
            act.varianza = ((act.P - act.O) / 6) ** 2
            # Calcular el costo de reducción por minuto (S)
            if act.Tn > act.Tc:
                act.S = (act.Cc - act.Cn) / (act.Tn - act.Tc)
            else:
                act.S = 0
            self.actividades[act.id] = act

        self.orden = self._orden_topologico()
        self._ejecutar_red()

    def _orden_topologico(self):
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
            a.ef = a.es + a.tiempo_actual
        self.duracion_total = max(a.ef for a in self.actividades.values())

    def _backward_pass(self):
        for id in reversed(self.orden):
            a = self.actividades[id]
            sucesoras = [s for s in self.actividades.values() if id in s.pre]
            if not sucesoras:
                a.lf = self.duracion_total
            else:
                a.lf = min(s.ls for s in sucesoras)
            a.ls = a.lf - a.tiempo_actual
            a.holgura = a.ls - a.es

    def _ruta_critica(self):
        self.criticas = []
        for a in self.actividades.values():
            if abs(a.holgura) < 1e-5:
                a.es_critica = True
                self.criticas.append(a.id)
            else:
                a.es_critica = False
        self.criticas.sort(key=lambda x: self.actividades[x].es)

    def _calcular_probabilidad(self):
        varianza_total = sum(self.actividades[id].varianza for id in self.criticas)
        self.sigma = math.sqrt(varianza_total)
        if self.sigma > 0:
            z = (self.cfg.TIEMPO_META - self.duracion_total) / self.sigma
            self.probabilidad = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        else:
            self.probabilidad = 1.0 if self.duracion_total <= self.cfg.TIEMPO_META else 0.0

    def _ejecutar_red(self):
        self._forward_pass()
        self._backward_pass()
        self._ruta_critica()
        self._calcular_probabilidad()

    def _obtener_rutas_criticas(self):
        """Encuentra todas las rutas críticas en el grafo actual."""
        rutas = []
        def dfs(nodo_actual_id, camino_actual, duracion_actual):
            nodo_actual = self.actividades[nodo_actual_id]
            sucesoras = [s for s in self.actividades.values() if nodo_actual_id in s.pre]
            if not sucesoras:
                rutas.append((list(camino_actual), duracion_actual))
            else:
                for suc in sucesoras:
                    dfs(suc.id, camino_actual + [suc.id], duracion_actual + suc.tiempo_actual)
                    
        for a in self.actividades.values():
            if not a.pre:
                dfs(a.id, [a.id], a.tiempo_actual)
                
        max_duracion = max(r[1] for r in rutas)
        criticas = [r[0] for r in rutas if abs(r[1] - max_duracion) < 1e-5]
        return criticas

    def calcular_crashing(self):
        """Ejecuta el algoritmo de reducción paso a paso buscando el óptimo global."""
        # Reiniciar tiempos al estado normal
        for a in self.actividades.values():
            a.tiempo_actual = a.Tn
        self._ejecutar_red()
        
        self.iteraciones_crashing = []
        costo_total_actual = sum(a.Cn for a in self.actividades.values())
        iteracion = 0
        
        self.iteraciones_crashing.append({
            "iter": 0, "actividad": "—", "tiempo_proyecto": self.duracion_total,
            "costo_extra": 0, "costo_total": costo_total_actual, "ruta": list(self.criticas)
        })

        while True:
            rutas_criticas = self._obtener_rutas_criticas()
            
            # 1. Buscar actividades comunes a todas las rutas críticas
            interseccion = set.intersection(*[set(ruta) for ruta in rutas_criticas])
            candidatas_comunes = [
                self.actividades[id] for id in interseccion 
                if self.actividades[id].tiempo_actual > self.actividades[id].Tc + 1e-5
            ]
            
            actividades_a_reducir = []
            costo_combinacion = 0.0
            
            if candidatas_comunes:
                # Si hay comunes, elegir la más barata
                elegida = min(candidatas_comunes, key=lambda a: a.S)
                actividades_a_reducir = [elegida]
                costo_combinacion = elegida.S
            else:
                # Si no hay comunes, hay que reducir una de cada ruta.
                import itertools
                combinaciones_validas = []
                
                # Filtramos las actividades de cada ruta que se puedan reducir
                opciones_por_ruta = []
                for ruta in rutas_criticas:
                    opciones = [self.actividades[id] for id in ruta 
                                if self.actividades[id].tiempo_actual > self.actividades[id].Tc + 1e-5]
                    if not opciones:
                        opciones_por_ruta = [] # No se puede reducir esta ruta
                        break
                    opciones_por_ruta.append(opciones)
                
                if opciones_por_ruta:
                    # Generar todas las combinaciones (una actividad por ruta)
                    for combo in itertools.product(*opciones_por_ruta):
                        # CORRECCIÓN AQUÍ: Eliminar duplicados por ID, no por objeto
                        ids_vistos = set()
                        combo_unico = []
                        for a in combo:
                            if a.id not in ids_vistos:
                                ids_vistos.add(a.id)
                                combo_unico.append(a)
                        
                        costo = sum(a.S for a in combo_unico)
                        combinaciones_validas.append((costo, combo_unico))
                        
                    if combinaciones_validas:
                        combinaciones_validas.sort(key=lambda x: x[0])
                        costo_combinacion, actividades_a_reducir = combinaciones_validas[0]
            
            if not actividades_a_reducir:
                break # No se puede reducir más el proyecto

            # 2. Calcular la reducción (1 minuto o el límite de la actividad que se reduce menos)
            reduccion = min(1.0, min(a.tiempo_actual - a.Tc for a in actividades_a_reducir))
            
            # 3. Aplicar reducción
            for a in actividades_a_reducir:
                a.tiempo_actual -= reduccion
                
            costo_extra = reduccion * costo_combinacion
            
            # 4. Recalcular red
            self._ejecutar_red()
            iteracion += 1
            
            self.iteraciones_crashing.append({
                "iter": iteracion, 
                "actividad": " + ".join(a.id for a in actividades_a_reducir), 
                "tiempo_proyecto": self.duracion_total,
                "costo_extra": costo_extra, 
                "costo_total": costo_total_actual + sum(i["costo_extra"] for i in self.iteraciones_crashing),
                "ruta": list(self.criticas)
            })

            if len(self.iteraciones_crashing) > 50: # Límite de seguridad
                break

        # Guardamos el estado final
        self.duracion_minima = self.duracion_total
        self.costo_maximo = self.iteraciones_crashing[-1]["costo_total"]

    def texto_paso_a_paso(self):
        """Genera una explicación textual de cómo se calcularon los tiempos."""
        lineas = []
        lineas.append("PASADA HACIA ADELANTE (Forward Pass) - Cálculo de ES y EF")
        lineas.append("Regla: ES = 0 si no tiene predecesoras. Si tiene, ES = max(EF de predecesoras). EF = ES + Duración.")
        for id in self.orden:
            a = self.actividades[id]
            if not a.pre:
                lineas.append(f"• {id}: No tiene predecesoras. ES = 0. EF = 0 + {a.Tn:.1f} = {a.ef:.1f}")
            else:
                ef_pres = ", ".join(f"{p}:{self.actividades[p].ef:.1f}" for p in a.pre)
                lineas.append(f"• {id}: Predecesoras ({ef_pres}). ES = max({ef_pres}) = {a.es:.1f}. EF = {a.es:.1f} + {a.Tn:.1f} = {a.ef:.1f}")
        
        lineas.append("\nPASADA HACIA ATRÁS (Backward Pass) - Cálculo de LS y LF")
        lineas.append("Regla: LF = Duración Total si no tiene sucesoras. Si tiene, LF = min(LS de sucesoras). LS = LF - Duración.")
        for id in reversed(self.orden):
            a = self.actividades[id]
            sucesoras = [s.id for s in self.actividades.values() if id in s.pre]
            if not sucesoras:
                lineas.append(f"• {id}: No tiene sucesoras. LF = Duración Total ({self.duracion_total:.1f}). LS = {a.lf:.1f} - {a.Tn:.1f} = {a.ls:.1f}")
            else:
                ls_sucs = ", ".join(f"{s}:{self.actividades[s].ls:.1f}" for s in sucesoras)
                lineas.append(f"• {id}: Sucesoras ({ls_sucs}). LF = min({ls_sucs}) = {a.lf:.1f}. LS = {a.lf:.1f} - {a.Tn:.1f} = {a.ls:.1f}")
        
        return lineas
