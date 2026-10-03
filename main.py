# -*- coding: utf-8 -*-
"""
=====================================================================
 PROGRAMA PRINCIPAL
=====================================================================
Ejecuta los 13 pasos del proyecto de Investigación de Operaciones y
genera las figuras. Todo se deriva de config.py.

Uso:
    python main.py                 → reporte completo + figuras
    python main.py --sin-graficas  → solo el reporte de consola
    python main.py --p 0.55        → recalcula todo con P(s1) = 0.55
    python main.py --exportar      → guarda el reporte en un .txt
=====================================================================
"""
from __future__ import annotations

import argparse
import os
import sys

import config as CFG
import config_Juegos as CJ
from juegos import JuegoSumaCero
from modelo import ModeloDecision, dinero, num, pct
import reporte as R
import reporte_Juegos as RJ


ESCENARIOS_SENSIBILIDAD = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def construir_reporte(m: ModeloDecision, archivos: dict,
                      juego: JuegoSumaCero | None = None) -> str:
    bloques = [
        R.portada(m),
        R.paso1(m),
        R.paso2(m),
        R.paso3(m),
        R.paso4(m, sorted(set(ESCENARIOS_SENSIBILIDAD +
                              [m.prior[m.ids_est[0]]] +
                              [c.p for c in m.cortes_validos]))),
        R.paso5(m, archivos),
        R.paso6(m),
        R.paso7(m),
        R.paso8(m),
        R.paso9(m),
        R.paso10(m, archivos),
        R.paso11(m),
        R.paso12(m),
        R.paso13(m),
        R.resumen_ejecutivo(m),
    ]
    if juego is not None:
        bloques.append(RJ.reporte_juego(juego, archivos))
    if archivos:
        listado = ["Figuras generadas automáticamente:"] + \
                  [f"• {k}: {v}" for k, v in archivos.items() if v]
        bloques.append("\n" + R.marco("ARCHIVOS DE SALIDA", listado))
    return "\n".join(bloques)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Modelo de decisión bajo incertidumbre")
    ap.add_argument("--sin-graficas", action="store_true",
                    help="omite la generación de figuras")
    ap.add_argument("--p", type=float, default=None,
                    help="sobrescribe P(s1) y recalcula todo el estudio")
    ap.add_argument("--salida", default=CFG.CARPETA_SALIDA,
                    help="carpeta donde se guardan las figuras")
    ap.add_argument("--exportar", action="store_true",
                    help="guarda el reporte completo en un archivo de texto")
    ap.add_argument("--solo-decisiones", action="store_true",
                    help="omite la parte de teoría de juegos")
    ap.add_argument("--solo-juegos", action="store_true",
                    help="muestra únicamente la parte de teoría de juegos")
    args = ap.parse_args(argv)

    # Escenario alterno: cambia la probabilidad a priori sin tocar config.py
    if args.p is not None:
        if not 0 <= args.p <= 1:
            print("El valor de --p debe estar entre 0 y 1."); return 1
        CFG.ESTADOS[0]["prior"] = args.p
        resto = 1 - args.p
        libres = CFG.ESTADOS[1:]
        base = sum(e["prior"] for e in libres)
        for e in libres:
            e["prior"] = resto / len(libres) if base == 0 else e["prior"] / base * resto

    try:
        modelo = ModeloDecision(CFG)
    except ValueError as err:
        print(f"\n❌ {err}\n"); return 1

    juego = None
    if not args.solo_decisiones:
        try:
            juego = JuegoSumaCero(CJ)
        except ValueError as err:
            print(f"\n❌ {err}\n"); return 1

    archivos: dict[str, str] = {}
    if not args.sin_graficas:
        import graficas
        archivos = graficas.generar_todas(modelo, args.salida)
        if juego is not None:
            import graficas_Juegos
            archivos.update(graficas_Juegos.generar_todas_juego(juego, args.salida))

    if args.solo_juegos and juego is not None:
        texto = RJ.reporte_juego(juego, archivos)
    else:
        texto = construir_reporte(modelo, archivos, juego)
    print(texto)

    for aviso in modelo.avisos + (juego.avisos if juego else []):
        print(f"\n⚠  {aviso}")

    if args.exportar:
        os.makedirs(args.salida, exist_ok=True)
        ruta = os.path.join(args.salida, "reporte.txt")
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(texto)
        print(f"\n✔ Reporte exportado a: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())