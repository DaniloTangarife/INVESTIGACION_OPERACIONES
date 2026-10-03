# -*- coding: utf-8 -*-
"""
=====================================================================
 MOTOR DE CÁLCULO — TEORÍA DE COLAS (M/M/1)
=====================================================================
Implementa los 7 pasos de las fórmulas vistas en clase:

  1. P0 = 1 - λ/μ
  2. Lq = λ² / (μ(μ-λ))
  3. L  = Lq + λ/μ
  4. Wq = Lq / λ
  5. W  = Wq + 1/μ
  6. Pw = λ/μ
  7. Pn = (λ/μ)^n · P0

Todo se deriva de config_colas.py. No hay números escritos a mano.
=====================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import config_colas as CC


# =====================================================================
#  UTILIDADES LOCALES (evitan dependencia circular con modelo.py)
# =====================================================================
def _num(v: float, d: int = 2) -> str:
    return f"{v:,.{d}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _pct(v: float, d: int = 2) -> str:
    return f"{_num(v * 100, d)}%"


def _dinero(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".") + " COP"


# =====================================================================
#  ESTRUCTURA DE RESULTADOS
# =====================================================================
@dataclass
class ResultadoColas:
    """Resultados completos de los 7 pasos para un sistema M/M/1."""
    tiempo_servicio: float
    lambda_: float          # tasa de llegada (clientes/hora)
    mu: float               # tasa de servicio (clientes/hora)
    rho: float              # utilización
    p0: float               # prob. sistema vacío
    lq: float               # clientes promedio en cola
    l: float                # clientes promedio en el sistema
    wq: float               # tiempo promedio en cola (horas)
    w: float                # tiempo promedio en sistema (horas)
    pw: float               # prob. de esperar
    pn: dict[int, float]    # prob. de n clientes
    pasajeros_dia: float
    horas_operacion: float
    descripcion: str = ""
    # Desarrollo algebraico (se llena al construir)
    desarrollo: dict[str, list[str]] = field(default_factory=dict)


# =====================================================================
#  MODELO
# =====================================================================
class ModeloColas:
    """Resuelve el sistema M/M/1 para el estado actual y el mejorado."""

    def __init__(self, cfg=CC):
        self.cfg = cfg
        self._validar()
        self.actual = self._calcular(
            cfg.TIEMPO_SERVICIO_ACTUAL,
            "Sistema actual (sin mejora)")
        self.mejorado = self._calcular(
            cfg.TIEMPO_SERVICIO_ACTUAL * cfg.FACTOR_MEJORA,
            f"Sistema mejorado: {cfg.MEJORA_DESCRIPCION}")

    # -----------------------------------------------------------------
    def _validar(self) -> None:
        self.avisos: list[str] = []
        errores: list[str] = []

        if self.cfg.VENTAS_MIN_DIA <= 0 or self.cfg.VENTAS_MAX_DIA <= 0:
            errores.append("Las ventas diarias deben ser positivas.")
        if self.cfg.VENTAS_MAX_DIA < self.cfg.VENTAS_MIN_DIA:
            errores.append("VENTAS_MAX_DIA debe ser mayor que VENTAS_MIN_DIA.")
        if not self.cfg.PRECIOS_PASAJE or any(p <= 0 for p in self.cfg.PRECIOS_PASAJE):
            errores.append("Los precios de pasaje deben ser positivos.")
        if self.cfg.BUSES_POR_DIA <= 0:
            errores.append("El número de buses por día debe ser positivo.")
        if self.cfg.HORAS_OPERACION <= 0:
            errores.append("Las horas de operación deben ser positivas.")
        if self.cfg.TIEMPO_SERVICIO_ACTUAL <= 0:
            errores.append("El tiempo de servicio actual debe ser positivo.")
        if not (0 < self.cfg.FACTOR_MEJORA < 1):
            errores.append("El factor de mejora debe estar en (0, 1).")
        if self.cfg.N_PN < 1:
            errores.append("N_PN debe ser al menos 1.")

        if errores:
            raise ValueError("Datos inconsistentes en config_colas.py:\n  - "
                             + "\n  - ".join(errores))

    # -----------------------------------------------------------------
    def _calcular(self, tiempo_servicio_seg: float,
                  descripcion: str) -> ResultadoColas:
        cfg = self.cfg

        # --- Tasa de llegada λ --------------------------------------
        ventas_promedio = (cfg.VENTAS_MIN_DIA + cfg.VENTAS_MAX_DIA) / 2
        precio_promedio = sum(cfg.PRECIOS_PASAJE) / len(cfg.PRECIOS_PASAJE)
        pasajeros_dia = ventas_promedio / precio_promedio
        lambda_ = pasajeros_dia / cfg.HORAS_OPERACION

        # --- Tasa de servicio μ --------------------------------------
        mu = 3600 / tiempo_servicio_seg

        # --- Utilización ρ ------------------------------------------
        rho = lambda_ / mu
        if rho >= 1:
            raise ValueError(
                f"Sistema inestable con estos parámetros:\n"
                f"  λ = {lambda_:.4f} clientes/h\n"
                f"  μ = {mu:.4f} clientes/h\n"
                f"  ρ = {rho:.4f} ≥ 1\n"
                f"Aumenta μ (menor tiempo de servicio) o reduce λ."
            )

        # --- 7 pasos ------------------------------------------------
        p0 = 1 - rho
        lq = (lambda_ ** 2) / (mu * (mu - lambda_))
        l  = lq + lambda_ / mu
        wq = lq / lambda_
        w  = wq + 1 / mu
        pw = lambda_ / mu
        pn = {n: (rho ** n) * p0 for n in range(cfg.N_PN + 1)}

        # --- Desarrollo algebraico para reporte ---------------------
        desarrollo = {
            "lambda": [
                f"Ventas promedio = ({_dinero(cfg.VENTAS_MIN_DIA)} + "
                f"{_dinero(cfg.VENTAS_MAX_DIA)}) / 2 = {_dinero(ventas_promedio)}",
                f"Precio promedio = ({' + '.join(_dinero(p) for p in cfg.PRECIOS_PASAJE)})"
                f" / {len(cfg.PRECIOS_PASAJE)} = {_dinero(precio_promedio)}",
                f"Pasajeros por día = {_dinero(ventas_promedio)} / "
                f"{_dinero(precio_promedio)} = {_num(pasajeros_dia, 2)}",
                f"λ = {_num(pasajeros_dia, 2)} / {_num(cfg.HORAS_OPERACION, 0)} = "
                f"{_num(lambda_, 4)} clientes/hora",
            ],
            "mu": [
                f"Tiempo de servicio = {_num(tiempo_servicio_seg, 0)} segundos",
                f"μ = 3600 / {_num(tiempo_servicio_seg, 0)} = {_num(mu, 4)} "
                f"clientes/hora",
            ],
            "rho": [
                f"ρ = λ / μ = {_num(lambda_, 4)} / {_num(mu, 4)} = {_num(rho, 4)} "
                f"({_pct(rho)})",
            ],
            "p0": [f"P0 = 1 − ρ = 1 − {_num(rho, 4)} = {_num(p0, 4)}"],
            "lq": [
                f"Lq = λ² / (μ(μ−λ))",
                f"Lq = ({_num(lambda_, 4)})² / ({_num(mu, 4)}·"
                f"({_num(mu, 4)} − {_num(lambda_, 4)}))",
                f"Lq = {_num(lambda_**2, 4)} / {_num(mu * (mu - lambda_), 4)} = "
                f"{_num(lq, 4)} clientes",
            ],
            "l": [
                f"L = Lq + λ/μ = {_num(lq, 4)} + {_num(lambda_, 4)}/"
                f"{_num(mu, 4)} = {_num(l, 4)} clientes",
            ],
            "wq": [
                f"Wq = Lq / λ = {_num(lq, 4)} / {_num(lambda_, 4)} = "
                f"{_num(wq, 4)} horas = {_num(wq * 60, 2)} minutos",
            ],
            "w": [
                f"W = Wq + 1/μ = {_num(wq, 4)} + 1/{_num(mu, 4)} = "
                f"{_num(w, 4)} horas = {_num(w * 60, 2)} minutos",
            ],
            "pw": [f"Pw = λ/μ = {_num(lambda_, 4)} / {_num(mu, 4)} = "
                   f"{_num(pw, 4)} ({_pct(pw)})"],
        }

        return ResultadoColas(
            tiempo_servicio=tiempo_servicio_seg,
            lambda_=lambda_, mu=mu, rho=rho,
            p0=p0, lq=lq, l=l, wq=wq, w=w, pw=pw, pn=pn,
            pasajeros_dia=pasajeros_dia,
            horas_operacion=cfg.HORAS_OPERACION,
            descripcion=descripcion,
            desarrollo=desarrollo,
        )

    # -----------------------------------------------------------------
    @property
    def mejora_lq(self) -> float:
        """Reducción porcentual de Lq con la mejora."""
        a, m = self.actual.lq, self.mejorado.lq
        return (a - m) / a * 100 if a > 0 else 0.0

    @property
    def mejora_wq(self) -> float:
        """Reducción porcentual de Wq con la mejora."""
        a, m = self.actual.wq, self.mejorado.wq
        return (a - m) / a * 100 if a > 0 else 0.0

    @property
    def mejora_l(self) -> float:
        a, m = self.actual.l, self.mejorado.l
        return (a - m) / a * 100 if a > 0 else 0.0

    @property
    def mejora_w(self) -> float:
        a, m = self.actual.w, self.mejorado.w
        return (a - m) / a * 100 if a > 0 else 0.0

    # -----------------------------------------------------------------
    def texto_conclusion(self) -> list[str]:
        """Conclusión generada a partir de los resultados calculados."""
        a, m = self.actual, self.mejorado
        partes: list[str] = []

        partes.append(
            f"1. DIAGNÓSTICO DEL SISTEMA ACTUAL. Se atiende con un único vendedor "
            f"(servidor) a una tasa de llegada de {_num(a.lambda_, 4)} pasajeros "
            f"por hora, con una tasa de servicio de {_num(a.mu, 4)} pasajeros por "
            f"hora. La utilización del sistema es de {_pct(a.rho)}, lo que "
            f"significa que el vendedor está ocupado el {_pct(a.rho)} del tiempo "
            f"y desocupado el {_pct(a.p0)}. El sistema es ESTABLE (ρ < 1)."
        )

        partes.append(
            f"2. INDICADORES ACTUALES. En promedio hay {_num(a.lq, 4)} pasajeros "
            f"en la cola y {_num(a.l, 4)} en el sistema (cola + siendo atendidos). "
            f"El tiempo promedio de espera en cola es de {_num(a.wq * 60, 2)} "
            f"minutos y el tiempo total en el sistema de {_num(a.w * 60, 2)} "
            f"minutos. La probabilidad de que un pasajero tenga que esperar es "
            f"del {_pct(a.pw)}."
        )

        partes.append(
            f"3. MEJORA PROPUESTA (SIN CONTRATAR PERSONAL). {self.cfg.MEJORA_DESCRIPCION} "
            f"Con esta mejora el tiempo de servicio baja de "
            f"{_num(a.tiempo_servicio, 0)} a {_num(m.tiempo_servicio, 0)} segundos, "
            f"elevando la tasa de servicio μ de {_num(a.mu, 4)} a {_num(m.mu, 4)} "
            f"pasajeros por hora."
        )

        partes.append(
            f"4. INDICADORES CON LA MEJORA. La utilización baja a {_pct(m.rho)}. "
            f"La cola promedio pasa de {_num(a.lq, 4)} a {_num(m.lq, 4)} pasajeros "
            f"(reducción del {_num(self.mejora_lq, 2)}%). El tiempo de espera en "
            f"cola baja de {_num(a.wq * 60, 2)} a {_num(m.wq * 60, 2)} minutos "
            f"(reducción del {_num(self.mejora_wq, 2)}%). El tiempo total en el "
            f"sistema pasa de {_num(a.w * 60, 2)} a {_num(m.w * 60, 2)} minutos. "
            f"La probabilidad de esperar baja a {_pct(m.pw)}."
        )

        partes.append(
            f"5. CONCLUSIÓN GERENCIAL. {self.cfg.MEJORA_JUSTIFICACION} El impacto "
            f"en los indicadores es medible y positivo, y no requiere ampliar la "
            f"nómina de la empresa. Se recomienda implementar la mejora."
        )

        return partes