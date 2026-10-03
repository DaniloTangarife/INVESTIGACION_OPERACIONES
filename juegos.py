# -*- coding: utf-8 -*-
"""
=====================================================================
 MOTOR DE CÁLCULO — TEORÍA DE JUEGOS (suma cero, dos jugadores)
=====================================================================
Reproduce exactamente el procedimiento visto en clase:

  1. Matriz de pagos con Mínimo de fila y Máximo de columna.
  2. Maximin y Minimax → ¿existe punto de silla?
  3. Si NO hay silla: eliminación por dominancia.
        · Filas    → se elimina la dominada (la de pagos menores),
                     porque el jugador maximizador nunca la usaría.
        · Columnas → se elimina la dominada (la de pagos mayores),
                     porque el jugador minimizador nunca la usaría.
     El proceso es iterativo hasta dejar una matriz 2×2, conservando
     siempre la posición original de cada valor.
  4. La matriz 2×2 sobreviviente se convierte en matriz de
     probabilidades (se divide por el factor de normalización).
  5. Se plantean las ecuaciones, se igualan y se resuelve para p,
     primero desde el jugador fila y después desde el jugador columna.
  6. Con las rectas obtenidas se hace el análisis gráfico.

No contiene ningún número del problema: todo viene de config_juegos.py.
=====================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

import config_Juegos as CJ
from modelo import num, pct


# =====================================================================
#  UTILIDADES
# =====================================================================
def frac_exacta(numerador: float, denominador: float, limite: int = 100_000) -> str:
    if abs(denominador) < 1e-12:
        return "indefinido"
    f = (Fraction(numerador).limit_denominator(limite)
         / Fraction(denominador).limit_denominator(limite))
    return f"{f.numerator}/{f.denominator}"


def signo(valor: float, decimales: int = 2) -> str:
    return (f"+ {num(abs(valor), decimales)}" if valor >= 0
            else f"− {num(abs(valor), decimales)}")


# =====================================================================
#  ESTRUCTURAS
# =====================================================================
@dataclass
class PasoEliminacion:
    """Una eliminación por dominancia, con todo lo necesario para dibujarla."""
    orden: int
    tipo: str                       # "fila" o "columna"
    eliminada: str                  # id de la estrategia eliminada
    dominante: str                  # id de la que la elimina
    filas_antes: list[str] = field(default_factory=list)
    columnas_antes: list[str] = field(default_factory=list)
    comparacion: list[str] = field(default_factory=list)
    explicacion: str = ""


@dataclass
class SolucionMixta:
    """Solución algebraica de la matriz 2×2 para uno de los jugadores."""
    jugador: str                    # "fila" o "columna"
    etiqueta_p: str                 # qué representa p
    etiqueta_q: str
    p: float
    q: float
    ecuaciones: list[str] = field(default_factory=list)
    algebra: list[str] = field(default_factory=list)
    valor: float = 0.0              # valor del juego (normalizado)
    rectas: dict[str, dict] = field(default_factory=dict)


# =====================================================================
#  MODELO
# =====================================================================
class JuegoSumaCero:

    def __init__(self, cfg=CJ):
        self.cfg = cfg
        self.estrategias_fila = cfg.ESTRATEGIAS_FILA
        self.estrategias_col = cfg.ESTRATEGIAS_COLUMNA
        self.ids_f = [e["id"] for e in self.estrategias_fila]
        self.ids_c = [e["id"] for e in self.estrategias_col]
        self.nombre_f = {e["id"]: e["nombre"] for e in self.estrategias_fila}
        self.nombre_c = {e["id"]: e["nombre"] for e in self.estrategias_col}
        self.factor = cfg.FACTOR_PROBABILIDAD
        self.unidad = cfg.UNIDAD_JUEGO

        self.pagos = {
            f: {c: cfg.MATRIZ_JUEGO[i][j] for j, c in enumerate(self.ids_c)}
            for i, f in enumerate(self.ids_f)
        }

        self._validar()
        self._resolver()

    # -----------------------------------------------------------------
    def _validar(self) -> None:
        self.avisos: list[str] = []
        errores = []
        if len(self.cfg.MATRIZ_JUEGO) != len(self.ids_f):
            errores.append("La matriz del juego no tiene una fila por estrategia "
                           "del jugador I.")
        for i, fila in enumerate(self.cfg.MATRIZ_JUEGO):
            if len(fila) != len(self.ids_c):
                errores.append(f"La fila {i + 1} de la matriz del juego no tiene una "
                               f"columna por estrategia del jugador II.")
        if len(self.ids_f) < 2 or len(self.ids_c) < 2:
            errores.append("El juego necesita al menos 2 estrategias por jugador.")
        if errores:
            raise ValueError("Datos inconsistentes en config_juegos.py:\n  - "
                             + "\n  - ".join(errores))

    def _resolver(self) -> None:
        self._paso_silla()
        self._paso_eliminacion()
        self._paso_probabilidades()
        self._paso_algebraico()

    # =================================================================
    #  PASO 1 y 2 — MÍNIMOS, MÁXIMOS Y PUNTO DE SILLA
    # =================================================================
    def _paso_silla(self) -> None:
        self.min_fila = {f: min(self.pagos[f][c] for c in self.ids_c)
                         for f in self.ids_f}
        self.max_col = {c: max(self.pagos[f][c] for f in self.ids_f)
                        for c in self.ids_c}

        self.maximin = max(self.min_fila.values())
        self.minimax = min(self.max_col.values())

        self.fila_maximin = max(self.ids_f,
                                key=lambda f: (self.min_fila[f],
                                               -self.ids_f.index(f)))
        self.col_minimax = min(self.ids_c,
                               key=lambda c: (self.max_col[c], self.ids_c.index(c)))

        self.hay_silla = abs(self.maximin - self.minimax) < 1e-12
        self.sillas: list[tuple[str, str, float]] = []
        if self.hay_silla:
            for f in self.ids_f:
                for c in self.ids_c:
                    v = self.pagos[f][c]
                    if (abs(v - self.min_fila[f]) < 1e-12
                            and abs(v - self.max_col[c]) < 1e-12):
                        self.sillas.append((f, c, v))
            self.valor_juego = self.maximin
        else:
            self.valor_juego = None     # se determina con la solución mixta

    # =================================================================
    #  PASO 3 — ELIMINACIÓN POR DOMINANCIA
    # =================================================================
    def _domina_fila(self, a: str, b: str, cols: list[str]) -> bool:
        """La fila a domina a la fila b: a paga al menos lo mismo en toda
        columna y estrictamente más en alguna. El maximizador descarta b."""
        mejor = all(self.pagos[a][c] >= self.pagos[b][c] for c in cols)
        estricto = any(self.pagos[a][c] > self.pagos[b][c] for c in cols)
        return mejor and estricto

    def _domina_columna(self, a: str, b: str, filas: list[str]) -> bool:
        """La columna a domina a la columna b: a entrega al jugador fila a lo
        sumo lo mismo en toda fila y estrictamente menos en alguna. El
        minimizador descarta b."""
        mejor = all(self.pagos[f][a] <= self.pagos[f][b] for f in filas)
        estricto = any(self.pagos[f][a] < self.pagos[f][b] for f in filas)
        return mejor and estricto

    def _paso_eliminacion(self) -> None:
        self.pasos: list[PasoEliminacion] = []
        filas = list(self.ids_f)
        cols = list(self.ids_c)
        self.filas_finales, self.columnas_finales = filas, cols
        self.reduccion_completa = False
        if self.hay_silla:
            return

        orden = 0
        while len(filas) > 2 or len(cols) > 2:
            movio = False

            # --- Filas: se empieza por filas, como indica la nota de clase ---
            if len(filas) > 2:
                for b in list(filas):
                    dom = next((a for a in filas
                                if a != b and self._domina_fila(a, b, cols)), None)
                    if dom:
                        orden += 1
                        self.pasos.append(PasoEliminacion(
                            orden=orden, tipo="fila", eliminada=b, dominante=dom,
                            filas_antes=list(filas), columnas_antes=list(cols),
                            comparacion=[
                                f"{dom}: {num(self.pagos[dom][c], 0)}  ≥  "
                                f"{b}: {num(self.pagos[b][c], 0)}   (columna {c})"
                                for c in cols],
                            explicacion=(
                                f"La estrategia {dom} ({self.nombre_f[dom]}) paga a "
                                f"nuestra empresa al menos lo mismo que {b} "
                                f"({self.nombre_f[b]}) frente a cualquier respuesta de "
                                f"la competencia, y más en al menos un caso. Como "
                                f"nuestra empresa maximiza, jamás jugaría {b}: la fila "
                                f"{b} queda eliminada.")))
                        filas.remove(b)
                        movio = True
                        break
            if movio:
                continue

            # --- Columnas ---
            if len(cols) > 2:
                for b in list(cols):
                    dom = next((a for a in cols
                                if a != b and self._domina_columna(a, b, filas)), None)
                    if dom:
                        orden += 1
                        self.pasos.append(PasoEliminacion(
                            orden=orden, tipo="columna", eliminada=b, dominante=dom,
                            filas_antes=list(filas), columnas_antes=list(cols),
                            comparacion=[
                                f"{dom}: {num(self.pagos[f][dom], 0)}  ≤  "
                                f"{b}: {num(self.pagos[f][b], 0)}   (fila {f})"
                                for f in filas],
                            explicacion=(
                                f"La estrategia {dom} ({self.nombre_c[dom]}) le entrega "
                                f"a nuestra empresa a lo sumo lo mismo que {b} "
                                f"({self.nombre_c[b]}) en toda fila, y menos en al menos "
                                f"un caso. Como la competencia minimiza lo que nosotros "
                                f"ganamos, jamás jugaría {b}: la columna {b} queda "
                                f"eliminada.")))
                        cols.remove(b)
                        movio = True
                        break

            if not movio:
                self.avisos.append(
                    f"La eliminación por dominancia se detuvo en una matriz "
                    f"{len(filas)}×{len(cols)}: ninguna fila ni columna restante está "
                    f"dominada. Con este tamaño la solución algebraica de dos "
                    f"ecuaciones no aplica y haría falta programación lineal.")
                break

        self.filas_finales, self.columnas_finales = filas, cols
        self.reduccion_completa = (len(filas) == 2 and len(cols) == 2)

    # =================================================================
    #  PASO 4 — MATRIZ DE PROBABILIDADES
    # =================================================================
    def _paso_probabilidades(self) -> None:
        self.matriz_reducida = {f: {c: self.pagos[f][c] for c in self.columnas_finales}
                                for f in self.filas_finales}
        self.matriz_prob = {f: {c: self.pagos[f][c] / self.factor
                                for c in self.columnas_finales}
                            for f in self.filas_finales}

    # =================================================================
    #  PASO 5 — SOLUCIÓN ALGEBRAICA DE LA MATRIZ 2×2
    # =================================================================
    def _paso_algebraico(self) -> None:
        self.solucion_fila = None
        self.solucion_columna = None
        self.valor_normalizado = None
        if self.hay_silla or not self.reduccion_completa:
            if self.hay_silla:
                self.valor_normalizado = self.valor_juego / self.factor
            return

        f1, f2 = self.filas_finales
        c1, c2 = self.columnas_finales
        a = self.matriz_prob[f1][c1]
        b = self.matriz_prob[f1][c2]
        c = self.matriz_prob[f2][c1]
        d = self.matriz_prob[f2][c2]
        den = a - b - c + d

        if abs(den) < 1e-12:
            self.avisos.append("La matriz 2×2 no tiene solución mixta única "
                               "(denominador nulo al igualar las ecuaciones).")
            return

        # --- Jugador fila: p = probabilidad de jugar f1 ---------------
        p = (d - c) / den
        ec1 = (f"E(I | {c2 if False else c1}) = {num(a, 2)}p {signo(c)}(1 − p)")
        ec2 = (f"E(I | {c2}) = {num(b, 2)}p {signo(d)}(1 − p)")
        algebra_f = [
            f"{num(a, 2)}p + {num(c, 2)}(1 − p) = {num(b, 2)}p + {num(d, 2)}(1 − p)",
            f"{num(a, 2)}p + {num(c, 2)} − {num(c, 2)}p = {num(b, 2)}p + {num(d, 2)} "
            f"− {num(d, 2)}p",
            f"{num(a - c, 2)}p {signo(c)} = {num(b - d, 2)}p {signo(d)}",
            f"{num(den, 2)}p = {num(d - c, 2)}",
            f"p = {num(d - c, 2)} / {num(den, 2)} = {frac_exacta(d - c, den)}",
            f"p = {num(p, 4)}   ({pct(p, 2)})      q = 1 − p = {num(1 - p, 4)}   "
            f"({pct(1 - p, 2)})",
        ]
        valor = a * p + c * (1 - p)
        algebra_f.append(
            f"Valor del juego = {num(a, 2)}({num(p, 4)}) + {num(c, 2)}({num(1 - p, 4)}) "
            f"= {num(valor, 4)}")
        self.solucion_fila = SolucionMixta(
            jugador="fila",
            etiqueta_p=f"p = probabilidad de que {self.cfg.JUGADOR_FILA['nombre']} "
                       f"juegue {f1}",
            etiqueta_q=f"q = 1 − p = probabilidad de jugar {f2}",
            p=p, q=1 - p, ecuaciones=[ec1, ec2], algebra=algebra_f, valor=valor,
            rectas={
                c1: {"m": a - c, "b": c,
                     "ecuacion": f"E(I | {c1}) = {num(a - c, 2)}p {signo(c)}"},
                c2: {"m": b - d, "b": d,
                     "ecuacion": f"E(I | {c2}) = {num(b - d, 2)}p {signo(d)}"},
            })

        # --- Jugador columna: p = probabilidad de jugar c1 ------------
        pc = (d - b) / den
        algebra_c = [
            f"{num(a, 2)}p + {num(b, 2)}(1 − p) = {num(c, 2)}p + {num(d, 2)}(1 − p)",
            f"{num(a, 2)}p + {num(b, 2)} − {num(b, 2)}p = {num(c, 2)}p + {num(d, 2)} "
            f"− {num(d, 2)}p",
            f"{num(a - b, 2)}p {signo(b)} = {num(c - d, 2)}p {signo(d)}",
            f"{num(den, 2)}p = {num(d - b, 2)}",
            f"p = {num(d - b, 2)} / {num(den, 2)} = {frac_exacta(d - b, den)}",
            f"p = {num(pc, 4)}   ({pct(pc, 2)})      q = 1 − p = {num(1 - pc, 4)}   "
            f"({pct(1 - pc, 2)})",
        ]
        valor_c = a * pc + b * (1 - pc)
        algebra_c.append(
            f"Valor del juego = {num(a, 2)}({num(pc, 4)}) + {num(b, 2)}"
            f"({num(1 - pc, 4)}) = {num(valor_c, 4)}")
        self.solucion_columna = SolucionMixta(
            jugador="columna",
            etiqueta_p=f"p = probabilidad de que {self.cfg.JUGADOR_COLUMNA['nombre']} "
                       f"juegue {c1}",
            etiqueta_q=f"q = 1 − p = probabilidad de jugar {c2}",
            p=pc, q=1 - pc,
            ecuaciones=[f"E(II | {f1}) = {num(a, 2)}p {signo(b)}(1 − p)",
                        f"E(II | {f2}) = {num(c, 2)}p {signo(d)}(1 − p)"],
            algebra=algebra_c, valor=valor_c,
            rectas={
                f1: {"m": a - b, "b": b,
                     "ecuacion": f"E(II | {f1}) = {num(a - b, 2)}p {signo(b)}"},
                f2: {"m": c - d, "b": d,
                     "ecuacion": f"E(II | {f2}) = {num(c - d, 2)}p {signo(d)}"},
            })

        self.valor_normalizado = valor
        self.valor_juego = valor * self.factor

    # =================================================================
    #  LECTURA DEL RESULTADO
    # =================================================================
    @property
    def tipo_solucion(self) -> str:
        if self.hay_silla:
            return "estrategias puras (punto de silla)"
        if self.reduccion_completa and self.solucion_fila:
            return "estrategias mixtas (sin punto de silla)"
        return "sin solución cerrada por este método"

    def texto_conclusion(self) -> list[str]:
        """Conclusión generada a partir de los resultados, nunca escrita a mano."""
        jf = self.cfg.JUGADOR_FILA["nombre"]
        jc = self.cfg.JUGADOR_COLUMNA["nombre"]
        partes = []

        if self.hay_silla:
            f, c, v = self.sillas[0]
            partes.append(
                f"1. EXISTE PUNTO DE SILLA. El maximin ({num(self.maximin, 0)}) "
                f"coincide con el minimax ({num(self.minimax, 0)}), de modo que el "
                f"juego se resuelve con estrategias puras y no hace falta ni "
                f"eliminación ni mezcla de probabilidades.")
            partes.append(
                f"2. ESTRATEGIAS ÓPTIMAS. {jf} debe jugar siempre {f} "
                f"({self.nombre_f[f]}) y {jc} siempre {c} ({self.nombre_c[c]}). "
                f"Ninguno de los dos gana nada desviándose unilateralmente: es un "
                f"equilibrio estable.")
            partes.append(
                f"3. VALOR DEL JUEGO. {num(v, 0)} {self.unidad} para {jf}, y por lo "
                f"tanto {num(self.factor - v, 0)} {self.unidad} para {jc}.")
            return partes

        partes.append(
            f"1. NO EXISTE PUNTO DE SILLA. El maximin vale {num(self.maximin, 0)} y el "
            f"minimax {num(self.minimax, 0)}; al no coincidir, ninguna pareja de "
            f"estrategias puras es estable: si un jugador se fija en una sola "
            f"estrategia, el otro siempre encuentra cómo aprovecharlo. La solución "
            f"tiene que ser mixta.")

        if self.pasos:
            elim_f = [p.eliminada for p in self.pasos if p.tipo == "fila"]
            elim_c = [p.eliminada for p in self.pasos if p.tipo == "columna"]
            partes.append(
                f"2. REDUCCIÓN POR DOMINANCIA. De la matriz original "
                f"{len(self.ids_f)}×{len(self.ids_c)} se eliminaron "
                f"{len(elim_f)} fila(s) ({', '.join(elim_f) or '—'}) y "
                f"{len(elim_c)} columna(s) ({', '.join(elim_c) or '—'}), porque "
                f"ningún jugador racional las usaría. Quedan las estrategias "
                f"{' y '.join(self.filas_finales)} para {jf} y "
                f"{' y '.join(self.columnas_finales)} para {jc}, conservando sus "
                f"posiciones originales en la matriz.")

        if not (self.reduccion_completa and self.solucion_fila):
            partes.append(
                "3. El procedimiento algebraico de dos ecuaciones requiere una matriz "
                "2×2; con lo que queda no es aplicable y habría que resolver el juego "
                "por programación lineal.")
            return partes

        sf, sc = self.solucion_fila, self.solucion_columna
        f1, f2 = self.filas_finales
        c1, c2 = self.columnas_finales
        partes.append(
            f"3. ESTRATEGIA ÓPTIMA DE {jf.upper()}. Debe jugar {f1} "
            f"({self.nombre_f[f1]}) el {pct(sf.p, 2)} de los sábados y {f2} "
            f"({self.nombre_f[f2]}) el {pct(sf.q, 2)} restante. Esa mezcla es "
            f"justamente la que deja a la competencia indiferente entre {c1} y {c2}: "
            f"haga lo que haga el rival, nuestra participación esperada es la misma.")
        partes.append(
            f"4. ESTRATEGIA ÓPTIMA DE {jc.upper()}. Por simetría del análisis, la "
            f"competencia debe jugar {c1} ({self.nombre_c[c1]}) el {pct(sc.p, 2)} de "
            f"las veces y {c2} ({self.nombre_c[c2]}) el {pct(sc.q, 2)}. Las dos "
            f"probabilidades suman {num(sc.p + sc.q, 4)}, como debe ser.")
        partes.append(
            f"5. VALOR DEL JUEGO. Ambos caminos algebraicos conducen al mismo "
            f"número: {num(self.valor_normalizado, 4)}, es decir "
            f"{num(self.valor_juego, 2)} {self.unidad} para {jf} y "
            f"{num(self.factor - self.valor_juego, 2)} {self.unidad} para {jc}. Ese "
            f"es el resultado que cada empresa puede garantizarse jugando bien, y "
            f"está entre el maximin ({num(self.maximin, 0)}) y el minimax "
            f"({num(self.minimax, 0)}), como exige la teoría.")
        partes.append(
            f"6. LECTURA OPERATIVA. La recomendación no es escoger una única "
            f"estrategia y repetirla: es alternar de forma impredecible entre {f1} y "
            f"{f2} en la proporción calculada. Cualquier patrón fijo o predecible "
            f"permitiría a la competencia anticiparse y llevar nuestra participación "
            f"por debajo de {num(self.valor_juego, 2)} {self.unidad}.")
        return partes

    # -----------------------------------------------------------------
    def recta_valor(self, solucion: SolucionMixta, clave: str, p: float) -> float:
        r = solucion.rectas[clave]
        return r["m"] * p + r["b"]