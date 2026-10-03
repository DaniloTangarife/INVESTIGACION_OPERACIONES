# -*- coding: utf-8 -*-
"""
=====================================================================
 MOTOR DE CÁLCULO DEL MODELO DE DECISIÓN
=====================================================================
Implementa los 13 pasos del proyecto. NO contiene ningún número del
problema: todo lo lee de config.py. Cualquier cambio en la matriz de
pagos, las probabilidades o las verosimilitudes se propaga solo.
=====================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from typing import Any

import config as CFG


# =====================================================================
#  UTILIDADES GENERALES
# =====================================================================
def mejor(valores: list[float], objetivo: str = CFG.OBJETIVO) -> float:
    """Mejor valor según el objetivo del problema (max o min)."""
    return max(valores) if objetivo == "max" else min(valores)


def peor(valores: list[float], objetivo: str = CFG.OBJETIVO) -> float:
    """Peor valor según el objetivo del problema."""
    return min(valores) if objetivo == "max" else max(valores)


def idx_mejor(valores: list[float], objetivo: str = CFG.OBJETIVO) -> int:
    """Índice del mejor valor (el primero en caso de empate)."""
    m = mejor(valores, objetivo)
    return valores.index(m)


def dinero(valor: float, decimales: int = 2) -> str:
    """Formatea un pago (en miles) como moneda completa: 775 -> 775.000 COP."""
    total = valor * CFG.FACTOR_MONEDA
    entero = f"{total:,.0f}".replace(",", ".")
    if abs(total - round(total)) > 1e-9:
        entero = f"{total:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{entero} {CFG.MONEDA}"


def num(valor: float, d: int = 2) -> str:
    """Formatea un número decimal con coma decimal (convención local)."""
    return f"{valor:,.{d}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def pct(valor: float, d: int = 2) -> str:
    """Formatea una proporción como porcentaje."""
    return f"{num(valor * 100, d)}%"


def frac(numerador: float, denominador: float, limite: int = 10_000) -> str:
    """Representación fraccionaria exacta para mostrar el álgebra del corte."""
    if abs(denominador) < 1e-12:
        return "indefinido"
    f = Fraction(numerador).limit_denominator(limite) / Fraction(denominador).limit_denominator(limite)
    return f"{f.numerator}/{f.denominator}"


def signo(valor: float) -> str:
    """Devuelve ' + x' o ' - x' para escribir ecuaciones legibles."""
    return f"+ {num(abs(valor))}" if valor >= 0 else f"- {num(abs(valor))}"


# =====================================================================
#  ESTRUCTURAS DE RESULTADO
# =====================================================================
@dataclass
class ResultadoCriterio:
    nombre: str
    descripcion: str
    valores: dict[str, float]          # id alternativa -> valor del criterio
    elegida: str                       # id de la alternativa elegida
    valor_elegido: float
    detalle: str = ""


@dataclass
class Corte:
    """Punto de corte entre las rectas de dos alternativas."""
    a: str
    b: str
    p: float
    valor: float
    valido: bool                       # ¿cae dentro de [0, 1]?
    algebra: list[str] = field(default_factory=list)


@dataclass
class Tramo:
    """Intervalo de p en el que domina una alternativa."""
    p_ini: float
    p_fin: float
    dominante: str


@dataclass
class RamaMuestral:
    indicador: str
    nombre: str
    prob_indicador: float
    conjuntas: dict[str, float]        # id estado -> P(indicador ∩ estado)
    posteriores: dict[str, float]      # id estado -> P(estado | indicador)
    ev: dict[str, float]               # id alternativa -> EV condicionado
    elegida: str
    valor: float


# =====================================================================
#  MODELO
# =====================================================================
class ModeloDecision:
    """Resuelve el problema completo a partir de config.py."""

    # -----------------------------------------------------------------
    def __init__(self, cfg=CFG):
        self.cfg = cfg
        self.objetivo = cfg.OBJETIVO

        self.alternativas = cfg.ALTERNATIVAS
        self.estados = cfg.ESTADOS
        self.indicadores = cfg.INDICADORES

        self.ids_alt = [a["id"] for a in self.alternativas]
        self.ids_est = [e["id"] for e in self.estados]
        self.ids_ind = [i["id"] for i in self.indicadores]

        self.nombre_alt = {a["id"]: a["nombre"] for a in self.alternativas}
        self.nombre_est = {e["id"]: e["nombre"] for e in self.estados}
        self.nombre_ind = {i["id"]: i["nombre"] for i in self.indicadores}

        self.pagos = {a["id"]: {e["id"]: cfg.MATRIZ_PAGOS[i][j]
                                for j, e in enumerate(self.estados)}
                      for i, a in enumerate(self.alternativas)}

        self.prior = {e["id"]: e["prior"] for e in self.estados}

        self.verosimilitud = {
            ind["id"]: {est["id"]: cfg.VEROSIMILITUDES[i][j]
                        for j, est in enumerate(self.estados)}
            for i, ind in enumerate(self.indicadores)
        }

        self._validar()
        self._resolver()

    # -----------------------------------------------------------------
    #  VALIDACIÓN DE COHERENCIA DE LOS DATOS
    # -----------------------------------------------------------------
    def _validar(self) -> None:
        self.avisos: list[str] = []
        errores: list[str] = []

        if len(self.cfg.MATRIZ_PAGOS) != len(self.alternativas):
            errores.append("La matriz de pagos no tiene una fila por alternativa.")
        for i, fila in enumerate(self.cfg.MATRIZ_PAGOS):
            if len(fila) != len(self.estados):
                errores.append(f"La fila {i + 1} de la matriz de pagos no tiene "
                               f"una columna por estado.")

        suma_prior = sum(self.prior.values())
        if abs(suma_prior - 1) > 1e-9:
            errores.append(f"Las probabilidades a priori suman {num(suma_prior, 4)}; "
                           f"deben sumar 1.")

        for est in self.ids_est:
            s = sum(self.verosimilitud[ind][est] for ind in self.ids_ind)
            if abs(s - 1) > 1e-9:
                errores.append(f"Las verosimilitudes P(indicador|{est}) suman "
                               f"{num(s, 4)}; deben sumar 1.")

        if self.objetivo not in ("max", "min"):
            errores.append("OBJETIVO debe ser 'max' o 'min'.")

        if errores:
            raise ValueError("Datos inconsistentes en config.py:\n  - " +
                             "\n  - ".join(errores))

        if len(self.estados) != 2:
            self.avisos.append(
                "El análisis gráfico y los puntos de corte requieren exactamente "
                "2 estados de la naturaleza; se omitirán los pasos 5 y 6.")

    # -----------------------------------------------------------------
    def _resolver(self) -> None:
        self._paso2_criterios()
        self._paso3_valores_esperados()
        self._paso4_sensibilidad()
        self._paso6_cortes()
        self._paso7_evpi()
        self._paso8_9_muestral()
        self._paso11_12_valor_informacion()

    # =================================================================
    #  PASO 2 — CRITERIOS BAJO INCERTIDUMBRE
    # =================================================================
    def _paso2_criterios(self) -> None:
        # --- Optimista (maximax / minimin) -------------------------------
        opt = {a: mejor([self.pagos[a][s] for s in self.ids_est], self.objetivo)
               for a in self.ids_alt}
        elegida_opt = self._elegir(opt)
        self.criterio_optimista = ResultadoCriterio(
            nombre="Optimista" + (" (maximax)" if self.objetivo == "max" else " (minimin)"),
            descripcion=("Se supone el escenario más favorable para cada alternativa "
                         "y se escoge el mejor de esos resultados."),
            valores=opt, elegida=elegida_opt, valor_elegido=opt[elegida_opt])

        # --- Conservador (maximin / minimax) -----------------------------
        con = {a: peor([self.pagos[a][s] for s in self.ids_est], self.objetivo)
               for a in self.ids_alt}
        elegida_con = self._elegir(con)
        self.criterio_conservador = ResultadoCriterio(
            nombre="Conservador" + (" (maximin)" if self.objetivo == "max" else " (minimax)"),
            descripcion=("Se supone el escenario más adverso para cada alternativa "
                         "y se escoge el mejor de esos peores resultados."),
            valores=con, elegida=elegida_con, valor_elegido=con[elegida_con])

        # --- Máximo arrepentimiento (minimax regret) ----------------------
        self.mejor_por_estado = {s: mejor([self.pagos[a][s] for a in self.ids_alt],
                                          self.objetivo) for s in self.ids_est}
        self.matriz_arrepentimiento = {
            a: {s: abs(self.mejor_por_estado[s] - self.pagos[a][s]) for s in self.ids_est}
            for a in self.ids_alt
        }
        arr = {a: max(self.matriz_arrepentimiento[a].values()) for a in self.ids_alt}
        elegida_arr = min(arr, key=lambda a: (arr[a], self.ids_alt.index(a)))
        self.criterio_arrepentimiento = ResultadoCriterio(
            nombre="Mínimo del máximo arrepentimiento (minimax regret)",
            descripcion=("Se mide cuánto se pierde por no haber elegido la mejor "
                         "alternativa en cada estado y se minimiza la peor pérdida."),
            valores=arr, elegida=elegida_arr, valor_elegido=arr[elegida_arr])

        self.criterios = [self.criterio_optimista,
                          self.criterio_conservador,
                          self.criterio_arrepentimiento]

    def _elegir(self, valores: dict[str, float]) -> str:
        """Elige el id de alternativa con mejor valor según el objetivo."""
        if self.objetivo == "max":
            return max(valores, key=lambda a: (valores[a], -self.ids_alt.index(a)))
        return min(valores, key=lambda a: (valores[a], self.ids_alt.index(a)))

    # =================================================================
    #  PASO 3 — VALORES ESPERADOS CON LAS PROBABILIDADES A PRIORI
    # =================================================================
    def _paso3_valores_esperados(self) -> None:
        self.ev_prior = {
            a: sum(self.prior[s] * self.pagos[a][s] for s in self.ids_est)
            for a in self.ids_alt
        }
        self.alt_optima_prior = self._elegir(self.ev_prior)
        self.ev_optimo_prior = self.ev_prior[self.alt_optima_prior]

        # Desarrollo algebraico automático de cada esperanza
        self.desarrollo_ev = {}
        for a in self.ids_alt:
            terminos = " + ".join(
                f"{num(self.prior[s])}·({num(self.pagos[a][s], 0)})" for s in self.ids_est)
            self.desarrollo_ev[a] = f"EV({a}) = {terminos} = {num(self.ev_prior[a])}"

    # =================================================================
    #  PASO 4 y 5 — ANÁLISIS DE SENSIBILIDAD Y RECTAS
    # =================================================================
    def _paso4_sensibilidad(self) -> None:
        """EV_a(p) = m_a · p + b_a, con p = P(s1) y (1-p) = P(s2)."""
        self.rectas: dict[str, dict[str, Any]] = {}
        if len(self.estados) != 2:
            return
        s1, s2 = self.ids_est
        for a in self.ids_alt:
            v1, v2 = self.pagos[a][s1], self.pagos[a][s2]
            m, b = v1 - v2, v2
            self.rectas[a] = {
                "m": m, "b": b,
                "ecuacion": f"EV({a}) = {num(m, 0)}p {signo(b)}",
                "pasos": [
                    f"EV({a}) = P({s1})·({num(v1, 0)}) + P({s2})·({num(v2, 0)})",
                    f"EV({a}) = {num(v1, 0)}p + (1 − p)·({num(v2, 0)})",
                    f"EV({a}) = {num(v1, 0)}p + {num(v2, 0)} − {num(v2, 0)}p",
                    f"EV({a}) = {num(m, 0)}p {signo(b)}",
                ],
                "punto_p0": (0.0, float(b)),
                "punto_p1": (1.0, float(m + b)),
            }

    def ev_en(self, alternativa: str, p: float) -> float:
        """Valor esperado de una alternativa cuando P(s1) = p."""
        r = self.rectas[alternativa]
        return r["m"] * p + r["b"]

    def escenario(self, p: float) -> dict[str, Any]:
        """Recalcula la decisión completa para un P(s1) arbitrario."""
        evs = {a: self.ev_en(a, p) for a in self.ids_alt}
        elegida = self._elegir(evs)
        empatadas = [a for a in self.ids_alt
                     if abs(evs[a] - evs[elegida]) < 1e-9]
        return {"p": p, "ev": evs, "elegida": elegida, "valor": evs[elegida],
                "empate": len(empatadas) > 1, "empatadas": empatadas}

    # =================================================================
    #  PASO 6 — PUNTOS DE CORTE
    # =================================================================
    def _paso6_cortes(self) -> None:
        self.cortes: list[Corte] = []
        self.tramos: list[Tramo] = []
        if len(self.estados) != 2:
            return

        for a, b in combinations(self.ids_alt, 2):
            ra, rb = self.rectas[a], self.rectas[b]
            dm, db = ra["m"] - rb["m"], rb["b"] - ra["b"]
            algebra = [f"EV({a}) = EV({b})",
                       f"{num(ra['m'], 0)}p {signo(ra['b'])} = {num(rb['m'], 0)}p {signo(rb['b'])}"]
            if abs(dm) < 1e-12:
                algebra.append("Las rectas son paralelas: no existe punto de corte.")
                self.cortes.append(Corte(a, b, float("nan"), float("nan"), False, algebra))
                continue
            p = db / dm
            algebra += [f"{num(dm, 0)}p = {num(db, 0)}",
                        f"p = {num(db, 0)} / {num(dm, 0)} = {frac(db, dm)}",
                        f"p = {num(p, 4)}  ({pct(p, 2)})"]
            self.cortes.append(Corte(a, b, p, self.ev_en(a, p), 0 <= p <= 1, algebra))

        # Tramos de dominancia (envolvente superior/inferior)
        ps = sorted({0.0, 1.0} | {c.p for c in self.cortes if c.valido})
        for ini, fin in zip(ps[:-1], ps[1:]):
            medio = (ini + fin) / 2
            dom = self._elegir({a: self.ev_en(a, medio) for a in self.ids_alt})
            if self.tramos and self.tramos[-1].dominante == dom:
                self.tramos[-1].p_fin = fin      # fusiona tramos contiguos iguales
            else:
                self.tramos.append(Tramo(ini, fin, dom))

        self.cortes_validos = [c for c in self.cortes if c.valido]

    # =================================================================
    #  PASO 7 — VALOR ESPERADO DE LA INFORMACIÓN PERFECTA
    # =================================================================
    def _paso7_evpi(self) -> None:
        self.mejor_decision_por_estado = {
            s: self._elegir({a: self.pagos[a][s] for a in self.ids_alt})
            for s in self.ids_est
        }
        self.ev_con_info_perfecta = sum(
            self.prior[s] * self.mejor_por_estado[s] for s in self.ids_est)
        self.evpi = abs(self.ev_con_info_perfecta - self.ev_optimo_prior)
        self.desarrollo_evpi = [
            "EVcIP = " + " + ".join(
                f"{num(self.prior[s])}·({num(self.mejor_por_estado[s], 0)})"
                for s in self.ids_est) + f" = {num(self.ev_con_info_perfecta)}",
            f"EVPI = EVcIP − EV({self.alt_optima_prior}) = "
            f"{num(self.ev_con_info_perfecta)} − {num(self.ev_optimo_prior)} = {num(self.evpi)}",
        ]

    # =================================================================
    #  PASOS 8 y 9 — INFORMACIÓN MUESTRAL Y TEOREMA DE BAYES
    # =================================================================
    def _paso8_9_muestral(self) -> None:
        self.ramas: list[RamaMuestral] = []
        for ind in self.ids_ind:
            conjuntas = {s: self.verosimilitud[ind][s] * self.prior[s] for s in self.ids_est}
            p_ind = sum(conjuntas.values())
            post = ({s: conjuntas[s] / p_ind for s in self.ids_est} if p_ind > 0
                    else {s: 0.0 for s in self.ids_est})
            evs = {a: sum(post[s] * self.pagos[a][s] for s in self.ids_est)
                   for a in self.ids_alt}
            elegida = self._elegir(evs)
            self.ramas.append(RamaMuestral(
                indicador=ind, nombre=self.nombre_ind[ind], prob_indicador=p_ind,
                conjuntas=conjuntas, posteriores=post, ev=evs,
                elegida=elegida, valor=evs[elegida]))
        self.rama_por_id = {r.indicador: r for r in self.ramas}

    # =================================================================
    #  PASOS 11 y 12 — EVSI Y EFICIENCIA
    # =================================================================
    def _paso11_12_valor_informacion(self) -> None:
        self.ev_con_info_muestral = sum(r.prob_indicador * r.valor for r in self.ramas)
        self.ev_sin_info_muestral = self.ev_optimo_prior
        self.evsi = abs(self.ev_con_info_muestral - self.ev_sin_info_muestral)
        self.eficiencia = (self.evsi / self.evpi) if self.evpi > 1e-12 else float("nan")

        self.desarrollo_evsi = [
            "EVcIM = " + " + ".join(
                f"P({r.indicador})·EV*|{r.indicador} = {num(r.prob_indicador, 4)}·{num(r.valor)}"
                for r in self.ramas) + f" = {num(self.ev_con_info_muestral)}",
            f"EVSI = EVcIM − EVsIM = {num(self.ev_con_info_muestral)} − "
            f"{num(self.ev_sin_info_muestral)} = {num(self.evsi)}",
            f"Eficiencia = EVSI / EVPI = {num(self.evsi)} / {num(self.evpi)} = "
            f"{pct(self.eficiencia)}",
        ]

    # =================================================================
    #  PASO 13 — DECISIÓN FINAL (texto generado, no escrito a mano)
    # =================================================================
    @property
    def cambia_decision_con_estudio(self) -> bool:
        return any(r.elegida != self.alt_optima_prior for r in self.ramas)

    @property
    def calificacion_eficiencia(self) -> str:
        e = self.eficiencia
        if e != e:                      # NaN
            return "no calculable"
        if e < 0.20:
            return "muy baja"
        if e < 0.40:
            return "baja"
        if e < 0.60:
            return "moderada"
        if e < 0.80:
            return "alta"
        return "muy alta"

    @property
    def recomienda_estudio(self) -> bool:
        """Se recomienda contratar el estudio si su eficiencia es al menos moderada."""
        return self.eficiencia == self.eficiencia and self.eficiencia >= 0.40

    @property
    def umbral_decisorio(self) -> Corte | None:
        """Corte que separa el tramo de la óptima actual del tramo rival."""
        if not getattr(self, "cortes_validos", None):
            return None
        return min(self.cortes_validos,
                   key=lambda c: abs(c.p - self.prior[self.ids_est[0]]))

    def texto_decision_final(self) -> list[str]:
        """Genera la conclusión gerencial a partir de los resultados calculados."""
        a_opt = self.alt_optima_prior
        s1 = self.ids_est[0]
        p1 = self.prior[s1]
        rival = [a for a in self.ids_alt if a != a_opt]
        partes = []

        # --- 1. Decisión inicial ---
        comparacion = "; ".join(
            f"EV({a}) = {dinero(self.ev_prior[a])}" for a in self.ids_alt)
        partes.append(
            f"1. DECISIÓN OPERATIVA INICIAL (sin estudio). Se elige la alternativa "
            f"{a_opt} — {self.nombre_alt[a_opt]} — porque alcanza el mejor valor "
            f"esperado: {comparacion}. Con una probabilidad de "
            f"{pct(self.prior[self.ids_est[-1]], 0)} de {self.nombre_est[self.ids_est[-1]]}, "
            f"esta opción protege a la empresa del riesgo financiero de operar bajo "
            f"un escenario regulatorio adverso.")

        # --- 2. Estabilidad / sensibilidad ---
        u = self.umbral_decisorio
        if u:
            otra = u.b if u.a == a_opt else u.a
            direccion = "superar" if p1 < u.p else "caer por debajo de"
            partes.append(
                f"2. ESTABILIDAD DE LA DECISIÓN. El análisis de sensibilidad muestra "
                f"que P({s1}) tendría que {direccion} el umbral de {pct(u.p)} "
                f"(p = {frac(u.p * 1, 1) if False else num(u.p, 4)}) para que la decisión "
                f"óptima pasara a ser {otra} — {self.nombre_alt[otra]}. Como el valor "
                f"estimado actual es {pct(p1, 0)}, la decisión {a_opt} se mantiene "
                f"{'con holgura' if abs(p1 - u.p) > 0.10 else 'con un margen estrecho'} "
                f"({num(abs(p1 - u.p) * 100)} puntos porcentuales de margen).")

        # --- 3. Información perfecta ---
        partes.append(
            f"3. INFORMACIÓN PERFECTA. Conocer con certeza el estado regulatorio valdría "
            f"como máximo {dinero(self.evpi)} (EVPI), diferencia entre el valor esperado "
            f"con información perfecta ({dinero(self.ev_con_info_perfecta)}) y el valor "
            f"esperado de la decisión actual ({dinero(self.ev_optimo_prior)}). Ningún "
            f"estudio, por bueno que sea, puede costar más que esta cifra.")

        # --- 4. Información muestral ---
        detalle = " ".join(
            f"Si el resultado es {r.nombre}, P({s1}) pasa a {pct(r.posteriores[s1])} "
            f"y la decisión {'cambia a' if r.elegida != a_opt else 'se ratifica en'} "
            f"{r.elegida} — {self.nombre_alt[r.elegida]} — con {dinero(r.valor)}."
            for r in self.ramas)
        partes.append(f"4. DECISIÓN CONDICIONADA AL ESTUDIO (Bayes). {detalle}")

        # --- 5. Conclusión económica ---
        veredicto = ("sí se justifica contratar" if self.recomienda_estudio
                     else "no se justifica contratar")
        partes.append(
            f"5. CONCLUSIÓN GERENCIAL Y FINANCIERA. El estudio aporta un incremento "
            f"esperado (EVSI) de {dinero(self.evsi)}, equivalente a una eficiencia "
            f"{self.calificacion_eficiencia} de {pct(self.eficiencia)} frente a la "
            f"información perfecta. Por lo tanto, {veredicto} la consultoría externa: "
            f"cualquier honorario superior a {dinero(self.evsi)} destruiría valor. "
            f"La recomendación final al tomador de decisiones es adoptar "
            f"{a_opt} — {self.nombre_alt[a_opt]} — con una utilidad esperada de "
            f"{dinero(self.ev_optimo_prior)}"
            f"{'' if self.recomienda_estudio else ' sin incurrir en gastos adicionales de estudio'}.")

        if rival and not self.recomienda_estudio and self.cambia_decision_con_estudio:
            partes.append(
                f"Observación: aunque un resultado favorable del estudio llegaría a "
                f"cambiar la decisión hacia {rival[0]}, la probabilidad de ese "
                f"escenario y la ganancia asociada son demasiado pequeñas para "
                f"compensar el costo de obtener esa información.")
        return partes

    # =================================================================
    #  ESTRUCTURA DE LOS ÁRBOLES DE DECISIÓN (paso 10)
    # =================================================================
    def arbol_prior(self) -> dict:
        """Árbol sin información muestral."""
        return {
            "tipo": "decision", "etiqueta": "Decisión\ninicial",
            "valor": self.ev_optimo_prior,
            "hijos": [
                {"tipo": "azar", "etiqueta": self.nombre_alt[a],
                 "rama": a, "valor": self.ev_prior[a],
                 "optimo": a == self.alt_optima_prior,
                 "hijos": [
                     {"tipo": "hoja", "etiqueta": self.nombre_est[s],
                      "rama": f"P({s}) = {num(self.prior[s])}",
                      "valor": self.pagos[a][s]}
                     for s in self.ids_est]}
                for a in self.ids_alt],
        }

    def arbol_muestral(self) -> dict:
        """Árbol con información muestral (nodo de azar en la raíz)."""
        return {
            "tipo": "azar", "etiqueta": "Resultado\ndel estudio",
            "valor": self.ev_con_info_muestral,
            "hijos": [
                {"tipo": "decision", "etiqueta": r.nombre,
                 "rama": f"P({r.indicador}) = {num(r.prob_indicador, 4)}",
                 "valor": r.valor,
                 "hijos": [
                     {"tipo": "azar", "etiqueta": self.nombre_alt[a],
                      "rama": a, "valor": r.ev[a], "optimo": a == r.elegida,
                      "hijos": [
                          {"tipo": "hoja", "etiqueta": self.nombre_est[s],
                           "rama": f"P({s}|{r.indicador}) = {num(r.posteriores[s], 4)}",
                           "valor": self.pagos[a][s]}
                          for s in self.ids_est]}
                     for a in self.ids_alt]}
                for r in self.ramas],
        }