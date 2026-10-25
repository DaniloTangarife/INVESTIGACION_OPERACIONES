# -*- coding: utf-8 -*-
"""
=====================================================================
 INTERFAZ GRÁFICA — Presentación del estudio paso a paso
=====================================================================
Aplicación de escritorio (Tkinter + Matplotlib) que presenta los
pasos del proyecto en un entorno visual navegable, con los datos del
problema editables en vivo: al cambiar la matriz de pagos, las
probabilidades, los datos de colas o del proyecto, todo el estudio 
se recalcula y todas las pantallas se redibujan.

Ejecutar:  python app.py
=====================================================================
"""
from __future__ import annotations

import copy
import os
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, ttk
from types import SimpleNamespace

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import config as CFG
import graficas
from modelo import ModeloDecision, dinero, num, pct

import config_colas as CC
from colas import ModeloColas, CalculadoraProbabilidades
import graficas_colas

import config_proyectos as CP
from proyectos import ModeloProyecto
import graficas_proyectos

# =====================================================================
#  PALETA Y ESTILO
# =====================================================================
C = {
    "fondo":        "#f1f5f9",
    "panel":        "#ffffff",
    "lateral":      "#1e293b",
    "lateral_alt":  "#334155",
    "activo":       "#2563eb",
    "texto":        "#0f172a",
    "texto_suave":  "#64748b",
    "texto_claro":  "#e2e8f0",
    "borde":        "#e2e8f0",
    "azul":         "#1e3a8a",
    "verde":        "#059669",
    "verde_claro":  "#ecfdf5",
    "rojo":         "#dc2626",
    "ambar":        "#d97706",
    "ambar_claro":  "#fffbeb",
    "morado":       "#7c3aed",
}

PASOS = [
    ("contexto", "Contexto del estudio", "◆"),
    ("datos",    "Datos del problema",   "⚙"),
    (1,  "Matriz de pagos",                    "1"),
    (2,  "Criterios bajo incertidumbre",       "2"),
    (3,  "Valor esperado a priori",            "3"),
    (4,  "Análisis de sensibilidad",           "4"),
    (5,  "Análisis gráfico",                   "5"),
    (6,  "Puntos de corte",                    "6"),
    (7,  "Información perfecta (EVPI)",        "7"),
    (8,  "Información muestral",               "8"),
    (9,  "Teorema de Bayes",                   "9"),
    (10, "Árboles de decisión",                "10"),
    (11, "Valor de la información (EVSI)",     "11"),
    (12, "Eficiencia del estudio",             "12"),
    (13, "Decisión final",                     "13"),
    ("colas_contexto", "Colas · Contexto", "⏳"),
    ("colas_datos",    "Colas · Datos",    "⚙"),
    (14, "Colas · Cálculo actual",   "14"),
    (15, "Colas · Mejora propuesta", "15"),
    (16, "Colas · Comparación",      "16"),
    ("colas_calculadora", "Colas · Calculadora", "🧮"),
    ("proyecto_contexto", "Proyecto · Contexto", "📋"),
    ("proyecto_red", "Proyecto · Red y Tiempos", "🔗"),
    ("proyecto_gantt", "Proyecto · Gantt y Ruta Crítica", "📊"),
]


# =====================================================================
#  WIDGETS REUTILIZABLES
# =====================================================================
class MarcoScroll(ttk.Frame):
    """Contenedor con barra de desplazamiento vertical."""

    def __init__(self, padre, **kw):
        super().__init__(padre, **kw)
        self.canvas = tk.Canvas(self, bg=C["fondo"], highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=C["fondo"])

        self._win = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=barra.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.interior.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self._win, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, self._rueda, add="+")

    def _rueda(self, ev):
        if not self.winfo_ismapped():
            return
        if getattr(ev, "num", None) == 4:
            self.canvas.yview_scroll(-3, "units")
        elif getattr(ev, "num", None) == 5:
            self.canvas.yview_scroll(3, "units")
        elif getattr(ev, "delta", 0):
            self.canvas.yview_scroll(int(-ev.delta / 60), "units")


def tarjeta(padre, titulo: str = "", color: str = None, pad: int = 18) -> tk.Frame:
    """Tarjeta blanca con franja de color superior y título opcional."""
    color = color or C["azul"]
    cont = tk.Frame(padre, bg=C["borde"], highlightthickness=0)
    cont.pack(fill="x", padx=22, pady=9)

    tk.Frame(cont, bg=color, height=4).pack(fill="x")
    cuerpo = tk.Frame(cont, bg=C["panel"])
    cuerpo.pack(fill="both", expand=True)

    if titulo:
        tk.Label(cuerpo, text=titulo, bg=C["panel"], fg=color,
                 font=("DejaVu Sans", 12, "bold"), anchor="w").pack(
            fill="x", padx=pad, pady=(pad - 4, 2))
    interior = tk.Frame(cuerpo, bg=C["panel"])
    interior.pack(fill="both", expand=True, padx=pad, pady=(0, pad))
    return interior


def parrafo(padre, texto: str, color: str = None, negrita: bool = False,
            tam: int = 10, pady: tuple = (2, 2)) -> tk.Label:
    lbl = tk.Label(padre, text=texto, bg=padre["bg"],
                   fg=color or C["texto"], justify="left", anchor="w",
                   wraplength=940,
                   font=("DejaVu Sans", tam, "bold" if negrita else "normal"))
    lbl.pack(fill="x", pady=pady)
    return lbl


def formula(padre, lineas: list[str]) -> None:
    caja = tk.Frame(padre, bg="#f8fafc", highlightbackground=C["borde"],
                    highlightthickness=1)
    caja.pack(fill="x", pady=6)
    for ln in lineas:
        tk.Label(caja, text=ln, bg="#f8fafc", fg="#1e293b", anchor="w",
                 font=("DejaVu Sans Mono", 10)).pack(fill="x", padx=14, pady=2)


def tabla(padre, columnas: list[str], filas: list[list], anchos: list[int] = None,
          destacar: list[int] = None, altura: int = None) -> ttk.Treeview:
    """Tabla con Treeview. `destacar` son índices de fila a resaltar en verde."""
    marco = tk.Frame(padre, bg=C["panel"])
    marco.pack(fill="x", pady=8)
    tv = ttk.Treeview(marco, columns=columnas, show="headings",
                      height=altura or len(filas), style="IO.Treeview")
    anchos = anchos or [max(150, 90 + 8 * len(c)) for c in columnas]
    for col, an in zip(columnas, anchos):
        tv.heading(col, text=col)
        tv.column(col, width=an, anchor="center" if col != columnas[0] else "w")
    for i, f in enumerate(filas):
        etiqueta = "destacada" if destacar and i in destacar else (
            "par" if i % 2 == 0 else "impar")
        tv.insert("", "end", values=[str(x) for x in f], tags=(etiqueta,))
    tv.tag_configure("par", background="#ffffff")
    tv.tag_configure("impar", background="#f8fafc")
    tv.tag_configure("destacada", background=C["verde_claro"], foreground="#065f46",
                     font=("DejaVu Sans", 10, "bold"))
    tv.pack(fill="x")
    return tv


def kpis(padre, items: list[tuple[str, str, str]]) -> None:
    """Fila de indicadores: (etiqueta, valor, color)."""
    fila = tk.Frame(padre, bg=padre["bg"])
    fila.pack(fill="x", pady=(6, 2))
    for etiqueta, valor, color in items:
        caja = tk.Frame(fila, bg="#f8fafc", highlightbackground=color,
                        highlightthickness=2)
        caja.pack(side="left", expand=True, fill="both", padx=5)
        tk.Label(caja, text=etiqueta, bg="#f8fafc", fg=C["texto_suave"],
                 font=("DejaVu Sans", 9)).pack(pady=(10, 0), padx=14)
        tk.Label(caja, text=valor, bg="#f8fafc", fg=color,
                 font=("DejaVu Sans", 14, "bold")).pack(pady=(0, 10), padx=14)


def insertar_figura(padre, fig, ancho_px: int = 1000) -> None:
    """Embebe una figura de matplotlib escalada al ancho disponible."""
    w, h = fig.get_size_inches()
    fig.set_dpi(max(50, ancho_px / w))
    marco = tk.Frame(padre, bg=C["panel"])
    marco.pack(fill="x", pady=6)
    lienzo = FigureCanvasTkAgg(fig, master=marco)
    lienzo.draw()
    lienzo.get_tk_widget().pack()


# =====================================================================
#  APLICACIÓN
# =====================================================================
class Aplicacion(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Investigación de Operaciones — Decisiones bajo incertidumbre")
        self.geometry("1360x860")
        self.minsize(1120, 720)
        self.configure(bg=C["fondo"])

        self.datos = self._datos_iniciales()
        self.modelo = ModeloDecision(self.datos)
        
        self.datos_colas = self._datos_colas_iniciales()
        self.modelo_colas = ModeloColas(self.datos_colas)
        
        self.datos_proyecto = CP
        self.modelo_proyecto = ModeloProyecto(self.datos_proyecto)
        
        self.actual = "contexto"
        self.botones: dict = {}
        self.entradas: dict = {}
        self.entradas_colas: dict = {}

        self._estilos()
        self._construir()
        self.mostrar("contexto")

    # -----------------------------------------------------------------
    def _datos_iniciales(self) -> SimpleNamespace:
        """Copia editable de config.py (el archivo original nunca se toca)."""
        return SimpleNamespace(
            TITULO=CFG.TITULO, SUBTITULO=CFG.SUBTITULO, CURSO=CFG.CURSO,
            MARCO_LEGAL=CFG.MARCO_LEGAL, EQUIPO=copy.deepcopy(CFG.EQUIPO),
            MONEDA=CFG.MONEDA, FACTOR_MONEDA=CFG.FACTOR_MONEDA,
            UNIDAD_CORTA=CFG.UNIDAD_CORTA,
            ALTERNATIVAS=copy.deepcopy(CFG.ALTERNATIVAS),
            ESTADOS=copy.deepcopy(CFG.ESTADOS),
            MATRIZ_PAGOS=copy.deepcopy(CFG.MATRIZ_PAGOS),
            INDICADORES=copy.deepcopy(CFG.INDICADORES),
            VEROSIMILITUDES=copy.deepcopy(CFG.VEROSIMILITUDES),
            OBJETIVO=CFG.OBJETIVO, CARPETA_SALIDA=CFG.CARPETA_SALIDA,
            ANCHO_CONSOLA=CFG.ANCHO_CONSOLA,
        )

    def _datos_colas_iniciales(self) -> SimpleNamespace:
        """Copia editable de config_colas.py (el archivo original nunca se toca)."""
        return SimpleNamespace(
            TITULO_COLAS=CC.TITULO_COLAS,
            SUBTITULO_COLAS=CC.SUBTITULO_COLAS,
            CONTEXTO_COLAS=CC.CONTEXTO_COLAS,
            VENTAS_MIN_DIA=CC.VENTAS_MIN_DIA,
            VENTAS_MAX_DIA=CC.VENTAS_MAX_DIA,
            PRECIOS_PASAJE=list(CC.PRECIOS_PASAJE),
            BUSES_POR_DIA=CC.BUSES_POR_DIA,
            HORAS_OPERACION=CC.HORAS_OPERACION,
            TIEMPO_SERVICIO_ACTUAL=CC.TIEMPO_SERVICIO_ACTUAL,
            MEJORA_DESCRIPCION=CC.MEJORA_DESCRIPCION,
            MEJORA_JUSTIFICACION=CC.MEJORA_JUSTIFICACION,
            FACTOR_MEJORA=CC.FACTOR_MEJORA,
            UNIDAD_TIEMPO=CC.UNIDAD_TIEMPO,
            UNIDAD_TASA=CC.UNIDAD_TASA,
            N_PN=CC.N_PN,
        )

    def _estilos(self) -> None:
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("IO.Treeview", background="#ffffff", fieldbackground="#ffffff",
                     foreground=C["texto"], rowheight=30, borderwidth=0,
                     font=("DejaVu Sans", 10))
        st.configure("IO.Treeview.Heading", background=C["azul"], foreground="white",
                     font=("DejaVu Sans", 10, "bold"), relief="flat", padding=8)
        st.map("IO.Treeview.Heading", background=[("active", C["activo"])])
        st.map("IO.Treeview", background=[("selected", "#dbeafe")],
               foreground=[("selected", C["texto"])])

    # -----------------------------------------------------------------
    def _construir(self) -> None:
        lateral = tk.Frame(self, bg=C["lateral"], width=290)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        cab = tk.Frame(lateral, bg=C["azul"])
        cab.pack(fill="x")
        tk.Label(cab, text="INVESTIGACIÓN\nDE OPERACIONES", bg=C["azul"], fg="white",
                 font=("DejaVu Sans", 13, "bold"), justify="left").pack(
            anchor="w", padx=20, pady=(20, 4))
        tk.Label(cab, text="Decisiones · Juegos · Colas · Proyectos",
                 bg=C["azul"], fg="#bfdbfe", font=("DejaVu Sans", 9),
                 justify="left").pack(anchor="w", padx=20, pady=(0, 18))

        lista = tk.Frame(lateral, bg=C["lateral"])
        lista.pack(fill="both", expand=True, pady=10)
        for clave, titulo, icono in PASOS:
            self.botones[clave] = self._boton_nav(lista, clave, titulo, icono)

        pie = tk.Frame(lateral, bg=C["lateral"])
        pie.pack(fill="x", side="bottom")
        tk.Button(pie, text="⤓  Exportar informe y figuras", command=self.exportar,
                  bg=C["verde"], fg="white", relief="flat", cursor="hand2",
                  activebackground="#047857", activeforeground="white",
                  font=("DejaVu Sans", 10, "bold"), pady=10).pack(
            fill="x", padx=16, pady=(10, 6))
        self.etiqueta_pie = tk.Label(pie, text="", bg=C["lateral"], fg="#94a3b8",
                                     font=("DejaVu Sans", 8), wraplength=250,
                                     justify="left")
        self.etiqueta_pie.pack(fill="x", padx=16, pady=(0, 12))

        # Área de contenido
        self.contenido = tk.Frame(self, bg=C["fondo"])
        self.contenido.pack(side="right", fill="both", expand=True)

        self.barra = tk.Frame(self.contenido, bg=C["panel"], height=64)
        self.barra.pack(fill="x")
        self.barra.pack_propagate(False)
        self.titulo_pagina = tk.Label(self.barra, text="", bg=C["panel"],
                                      fg=C["texto"], font=("DejaVu Sans", 16, "bold"))
        self.titulo_pagina.pack(side="left", padx=26)
        self.resumen_barra = tk.Label(self.barra, text="", bg=C["panel"],
                                      fg=C["texto_suave"], font=("DejaVu Sans", 10))
        self.resumen_barra.pack(side="right", padx=26)
        tk.Frame(self.contenido, bg=C["borde"], height=1).pack(fill="x")

        self.area = MarcoScroll(self.contenido)
        self.area.pack(fill="both", expand=True)

        nav = tk.Frame(self.contenido, bg=C["panel"], height=54)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)
        tk.Button(nav, text="◀  Anterior", command=lambda: self.saltar(-1),
                  bg="#e2e8f0", fg=C["texto"], relief="flat", cursor="hand2",
                  font=("DejaVu Sans", 10), padx=18, pady=6).pack(side="left", padx=26)
        tk.Button(nav, text="Siguiente  ▶", command=lambda: self.saltar(1),
                  bg=C["activo"], fg="white", relief="flat", cursor="hand2",
                  activebackground="#1d4ed8", activeforeground="white",
                  font=("DejaVu Sans", 10, "bold"), padx=18, pady=6).pack(
            side="right", padx=26)

    def _boton_nav(self, padre, clave, titulo, icono) -> tk.Frame:
        fila = tk.Frame(padre, bg=C["lateral"], cursor="hand2")
        fila.pack(fill="x")
        marca = tk.Frame(fila, bg=C["lateral"], width=4)
        marca.pack(side="left", fill="y")
        ic = tk.Label(fila, text=icono, bg=C["lateral"], fg="#94a3b8", width=3,
                      font=("DejaVu Sans", 10, "bold"))
        ic.pack(side="left", pady=6)
        tx = tk.Label(fila, text=titulo, bg=C["lateral"], fg=C["texto_claro"],
                      anchor="w", font=("DejaVu Sans", 10))
        tx.pack(side="left", fill="x", expand=True, pady=6)
        fila.widgets = (marca, ic, tx)
        for w in (fila, ic, tx):
            w.bind("<Button-1>", lambda e, k=clave: self.mostrar(k))
        return fila

    # -----------------------------------------------------------------
    def saltar(self, paso: int) -> None:
        claves = [p[0] for p in PASOS]
        i = min(max(claves.index(self.actual) + paso, 0), len(claves) - 1)
        self.mostrar(claves[i])

    def mostrar(self, clave) -> None:
        self.actual = clave
        for k, fila in self.botones.items():
            activo = k == clave
            marca, ic, tx = fila.widgets
            fondo = C["lateral_alt"] if activo else C["lateral"]
            for w in (fila, ic, tx):
                w.configure(bg=fondo)
            marca.configure(bg=C["activo"] if activo else fondo)
            tx.configure(fg="white" if activo else C["texto_claro"],
                         font=("DejaVu Sans", 10, "bold" if activo else "normal"))
            ic.configure(fg=C["activo"] if activo else "#94a3b8", bg=fondo)

        titulo = next(t for k, t, _ in PASOS if k == clave)
        self.titulo_pagina.configure(
            text=titulo if isinstance(clave, str) else f"Paso {clave} — {titulo}")
        m = self.modelo
        mc = self.modelo_colas
        mp = self.modelo_proyecto
        
        self.resumen_barra.configure(
            text=f"Óptima: {m.alt_optima_prior} · {dinero(m.ev_optimo_prior)} | "
                 f"Colas: {pct(mc.actual.rho)}→{pct(mc.mejorado.rho)} | "
                 f"Proyecto: {num(mp.duracion_total, 1)} min")

        for w in self.area.interior.winfo_children():
            w.destroy()
        self.area.canvas.yview_moveto(0)
        tk.Frame(self.area.interior, bg=C["fondo"], height=6).pack(fill="x")

        constructor = {
            "contexto": self.pg_contexto, "datos": self.pg_datos,
            1: self.pg1, 2: self.pg2, 3: self.pg3, 4: self.pg4, 5: self.pg5,
            6: self.pg6, 7: self.pg7, 8: self.pg8, 9: self.pg9, 10: self.pg10,
            11: self.pg11, 12: self.pg12, 13: self.pg13,
            "colas_contexto": self.pg_colas_contexto,
            "colas_datos":    self.pg_colas_datos,
            14: self.pg_colas_actual,
            15: self.pg_colas_mejora,
            16: self.pg_colas_comparacion,
            "colas_calculadora": self.pg_colas_calculadora,
            "proyecto_contexto": self.pg_proyecto_contexto,
            "proyecto_red": self.pg_proyecto_red,
            "proyecto_gantt": self.pg_proyecto_gantt,
        }[clave]
        constructor(self.area.interior)
        tk.Frame(self.area.interior, bg=C["fondo"], height=18).pack(fill="x")

    # =================================================================
    #  PÁGINA: CONTEXTO
    # =================================================================
    def pg_contexto(self, p) -> None:
        m, d = self.modelo, self.datos

        enc = tk.Frame(p, bg=C["azul"])
        enc.pack(fill="x", padx=22, pady=(6, 10))
        tk.Label(enc, text=d.TITULO, bg=C["azul"], fg="white", wraplength=980,
                 font=("DejaVu Sans", 15, "bold"), justify="center").pack(pady=(18, 4))
        tk.Label(enc, text=d.SUBTITULO, bg=C["azul"], fg="#dbeafe",
                 font=("DejaVu Sans", 10), wraplength=980).pack()
        tk.Label(enc, text=f"{d.CURSO}   ·   {d.MARCO_LEGAL}", bg=C["azul"],
                 fg="#bfdbfe", font=("DejaVu Sans", 9, "italic"),
                 wraplength=980).pack(pady=(2, 18))

        i = tarjeta(p, "¿QUÉ DECISIÓN SE ESTÁ TOMANDO?", C["azul"])
        parrafo(i, "La empresa debe escoger UNA de estas alternativas para la "
                   "operación de los sábados:")
        for a in d.ALTERNATIVAS:
            parrafo(i, f"▪  {a['id']} — {a['nombre']}: {a['descripcion']}.",
                    pady=(4, 0))

        i = tarjeta(p, "¿QUÉ NO CONTROLA LA EMPRESA?", C["morado"])
        parrafo(i, "El resultado económico depende del estado regulatorio, un "
                   "factor externo a la empresa:")
        for e in d.ESTADOS:
            parrafo(i, f"▪  {e['id']} — {e['nombre']}  ({pct(e['prior'], 0)}): "
                       f"{e['descripcion']}.", pady=(4, 0))

        i = tarjeta(p, "¿QUÉ SE BUSCA CON ESTE ESTUDIO?", C["verde"])
        for t in ["1. Determinar la alternativa que maximiza la utilidad esperada.",
                  "2. Medir qué tan estable es esa decisión si cambian las "
                  "probabilidades (análisis de sensibilidad y punto de corte).",
                  "3. Calcular cuánto valdría eliminar por completo la "
                  "incertidumbre (EVPI).",
                  "4. Evaluar, con el Teorema de Bayes, si una consultoría jurídica "
                  "previa cambiaría la decisión (EVSI).",
                  "5. Analizar el sistema de colas de la venta de tiquetes (M/M/1).",
                  "6. Concluir con cifras si conviene o no pagar esa consultoría.",
                  "7. Optimizar el proyecto de despacho de un bus (PERT/CPM)."]:
            parrafo(i, t, pady=(3, 0))

        # Origen de los datos — destacado
        cont = tk.Frame(p, bg=C["ambar"], highlightthickness=0)
        cont.pack(fill="x", padx=22, pady=9)
        cuerpo = tk.Frame(cont, bg=C["ambar_claro"])
        cuerpo.pack(fill="both", expand=True, padx=3, pady=3)
        tk.Label(cuerpo, text="LOS DATOS NO SON INVENTADOS", bg=C["ambar_claro"],
                 fg="#b45309", font=("DejaVu Sans", 12, "bold"), anchor="w").pack(
            fill="x", padx=18, pady=(16, 6))
        fuentes = ", ".join(x["nombre"] for x in d.EQUIPO if x.get("fuente")) \
            or "un integrante del equipo"
        for t in [f"{fuentes} hace parte de este equipo de trabajo y labora "
                  f"actualmente en la empresa de transporte intermunicipal analizada. "
                  f"Gracias a ello cuenta con acceso directo y autorizado a la "
                  f"información operativa real de la ruta: utilidades por despacho, "
                  f"niveles de ocupación de los sábados y condiciones regulatorias "
                  f"vigentes.",
                  f"Las cifras de la matriz de pagos provienen de esa fuente "
                  f"primaria, no de supuestos académicos. Por eso las conclusiones de "
                  f"este modelo son directamente aplicables a la operación real de la "
                  f"empresa."]:
            tk.Label(cuerpo, text=t, bg=C["ambar_claro"], fg="#78350f", anchor="w",
                     justify="left", wraplength=940,
                     font=("DejaVu Sans", 10)).pack(fill="x", padx=18, pady=(0, 12))

        i = tarjeta(p, "MATRIZ DE PAGOS — PUNTO DE PARTIDA DE TODO EL MODELO", C["rojo"])
        self._tabla_pagos(i)
        parrafo(i, f"Todos los valores están expresados en {d.UNIDAD_CORTA} de "
                   f"utilidad operativa por jornada de sábado. A partir ÚNICAMENTE de "
                   f"esta matriz y de las probabilidades mostradas, el programa "
                   f"calcula los 13 pasos del estudio.",
                color=C["texto_suave"], pady=(8, 0))

    def _tabla_pagos(self, padre) -> None:
        m = self.modelo
        cols = ["Alternativa"] + [f"{s} · {m.nombre_est[s]}" for s in m.ids_est]
        filas = [[f"{a} · {m.nombre_alt[a]}"] + [dinero(m.pagos[a][s]) for s in m.ids_est]
                 for a in m.ids_alt]
        filas.append(["Probabilidad a priori"] + [num(m.prior[s]) for s in m.ids_est])
        tabla(padre, cols, filas, [300] + [240] * len(m.ids_est))

    # =================================================================
    #  PÁGINA: DATOS EDITABLES
    # =================================================================
    def pg_datos(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "DATOS DEL PROBLEMA — EDITABLES EN VIVO", C["ambar"])
        parrafo(i, "Toda la aplicación se alimenta ÚNICAMENTE de estos valores. "
                   "Al pulsar «Recalcular», los 13 pasos, las gráficas, los árboles y "
                   "los textos de conclusión se rehacen automáticamente.",
                color=C["texto_suave"])

        self.entradas = {"pagos": {}, "prior": {}, "veros": {}}

        # --- Matriz de pagos ---
        i = tarjeta(p, f"Matriz de pagos ({self.datos.UNIDAD_CORTA})", C["rojo"])
        rej = tk.Frame(i, bg=C["panel"])
        rej.pack(anchor="w")
        tk.Label(rej, text="", bg=C["panel"], width=24).grid(row=0, column=0)
        for j, s in enumerate(m.ids_est):
            tk.Label(rej, text=f"{s} · {m.nombre_est[s]}", bg=C["panel"],
                     fg=C["azul"], font=("DejaVu Sans", 10, "bold")).grid(
                row=0, column=j + 1, padx=10, pady=6)
        for r, a in enumerate(m.ids_alt):
            tk.Label(rej, text=f"{a} · {m.nombre_alt[a]}", bg=C["panel"], anchor="w",
                     font=("DejaVu Sans", 10)).grid(row=r + 1, column=0, sticky="w",
                                                    padx=(0, 12), pady=4)
            for j, s in enumerate(m.ids_est):
                var = tk.StringVar(value=str(m.pagos[a][s]))
                tk.Entry(rej, textvariable=var, width=12, justify="center",
                         font=("DejaVu Sans Mono", 11), relief="solid", bd=1).grid(
                    row=r + 1, column=j + 1, padx=10, pady=4, ipady=4)
                self.entradas["pagos"][(a, s)] = var

        # --- Probabilidades a priori ---
        i = tarjeta(p, "Probabilidades a priori de los estados", C["morado"])
        rej = tk.Frame(i, bg=C["panel"])
        rej.pack(anchor="w")
        for j, s in enumerate(m.ids_est):
            tk.Label(rej, text=f"P({s}) — {m.nombre_est[s]}", bg=C["panel"],
                     font=("DejaVu Sans", 10)).grid(row=j, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=str(m.prior[s]))
            tk.Entry(rej, textvariable=var, width=12, justify="center",
                     font=("DejaVu Sans Mono", 11), relief="solid", bd=1).grid(
                row=j, column=1, padx=14, pady=5, ipady=4)
            self.entradas["prior"][s] = var
        parrafo(i, "Deben sumar exactamente 1.", color=C["texto_suave"], tam=9)

        if len(m.ids_est) == 2:
            s1 = m.ids_est[0]
            self.deslizador = tk.DoubleVar(value=m.prior[s1])
            marco = tk.Frame(i, bg=C["panel"])
            marco.pack(fill="x", pady=(10, 0))
            tk.Label(marco, text=f"Explorar P({s1}) rápidamente:", bg=C["panel"],
                     font=("DejaVu Sans", 10, "bold")).pack(anchor="w")
            tk.Scale(marco, from_=0.0, to=1.0, resolution=0.01, orient="horizontal",
                     variable=self.deslizador, bg=C["panel"], highlightthickness=0,
                     troughcolor="#e2e8f0", length=560,
                     command=self._mover_deslizador).pack(anchor="w")
            self.vista_previa = tk.Label(marco, text="", bg=C["panel"],
                                         fg=C["texto_suave"],
                                         font=("DejaVu Sans", 10))
            self.vista_previa.pack(anchor="w")
            self._mover_deslizador(self.deslizador.get())

        # --- Verosimilitudes ---
        i = tarjeta(p, "Confiabilidad del estudio — P(indicador | estado)", C["azul"])
        rej = tk.Frame(i, bg=C["panel"])
        rej.pack(anchor="w")
        tk.Label(rej, text="", bg=C["panel"], width=24).grid(row=0, column=0)
        for j, s in enumerate(m.ids_est):
            tk.Label(rej, text=f"P( · | {s})", bg=C["panel"], fg=C["azul"],
                     font=("DejaVu Sans", 10, "bold")).grid(row=0, column=j + 1,
                                                            padx=10, pady=6)
        for r, ind in enumerate(m.ids_ind):
            tk.Label(rej, text=f"{ind} · {m.nombre_ind[ind]}", bg=C["panel"],
                     anchor="w", font=("DejaVu Sans", 10)).grid(
                row=r + 1, column=0, sticky="w", padx=(0, 12), pady=4)
            for j, s in enumerate(m.ids_est):
                var = tk.StringVar(value=str(m.verosimilitud[ind][s]))
                tk.Entry(rej, textvariable=var, width=12, justify="center",
                         font=("DejaVu Sans Mono", 11), relief="solid", bd=1).grid(
                    row=r + 1, column=j + 1, padx=10, pady=4, ipady=4)
                self.entradas["veros"][(ind, s)] = var
        parrafo(i, "Cada columna debe sumar 1.", color=C["texto_suave"], tam=9)

        # --- Acciones ---
        i = tarjeta(p, "", C["verde"])
        botones = tk.Frame(i, bg=C["panel"])
        botones.pack(anchor="w")
        tk.Button(botones, text="↻  Recalcular todo el estudio",
                  command=self.recalcular, bg=C["verde"], fg="white", relief="flat",
                  cursor="hand2", activebackground="#047857",
                  activeforeground="white", font=("DejaVu Sans", 11, "bold"),
                  padx=22, pady=10).pack(side="left")
        tk.Button(botones, text="⟲  Restaurar valores originales",
                  command=self.restaurar, bg="#e2e8f0", fg=C["texto"], relief="flat",
                  cursor="hand2", font=("DejaVu Sans", 11), padx=22, pady=10).pack(
            side="left", padx=12)

    def _mover_deslizador(self, valor) -> None:
        m = self.modelo
        if len(m.ids_est) != 2:
            return
        e = m.escenario(float(valor))
        s1, s2 = m.ids_est
        if e["empate"]:
            txt = (f"P({s1}) = {pct(float(valor), 0)}  →  INDIFERENTE entre "
                   f"{' y '.join(e['empatadas'])} · {dinero(e['valor'])}")
        else:
            txt = (f"P({s1}) = {pct(float(valor), 0)}   ·   P({s2}) = "
                   f"{pct(1 - float(valor), 0)}   →   óptima: {e['elegida']} · "
                   f"{m.nombre_alt[e['elegida']]} con {dinero(e['valor'])}")
        self.vista_previa.configure(text=txt)
        for s, var in self.entradas["prior"].items():
            var.set(f"{float(valor):.4g}" if s == m.ids_est[0]
                    else f"{1 - float(valor):.4g}")

    def recalcular(self) -> None:
        try:
            d = self.datos
            for (a, s), var in self.entradas["pagos"].items():
                i, j = self.modelo.ids_alt.index(a), self.modelo.ids_est.index(s)
                d.MATRIZ_PAGOS[i][j] = float(var.get().replace(",", "."))
            for s, var in self.entradas["prior"].items():
                j = self.modelo.ids_est.index(s)
                d.ESTADOS[j]["prior"] = float(var.get().replace(",", "."))
            for (ind, s), var in self.entradas["veros"].items():
                i = self.modelo.ids_ind.index(ind)
                j = self.modelo.ids_est.index(s)
                d.VEROSIMILITUDES[i][j] = float(var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Dato inválido",
                                 "Todos los campos deben ser numéricos.")
            return

        try:
            self.modelo = ModeloDecision(d)
        except ValueError as err:
            messagebox.showerror("Datos inconsistentes", str(err))
            return

        messagebox.showinfo(
            "Estudio recalculado",
            f"Alternativa óptima: {self.modelo.alt_optima_prior} — "
            f"{self.modelo.nombre_alt[self.modelo.alt_optima_prior]}\n"
            f"Valor esperado: {dinero(self.modelo.ev_optimo_prior)}\n"
            f"Eficiencia del estudio: {pct(self.modelo.eficiencia)}")
        self.mostrar("datos")

    def recalcular_colas(self) -> None:
        try:
            d = self.datos_colas
            d.VENTAS_MIN_DIA = float(self.entradas_colas["ventas_min"].get().replace(",", "."))
            d.VENTAS_MAX_DIA = float(self.entradas_colas["ventas_max"].get().replace(",", "."))
            d.HORAS_OPERACION = float(self.entradas_colas["horas"].get().replace(",", "."))
            d.TIEMPO_SERVICIO_ACTUAL = float(
                self.entradas_colas["tiempo_servicio"].get().replace(",", "."))
            d.FACTOR_MEJORA = float(self.entradas_colas["factor_mejora"].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Dato inválido",
                                 "Todos los campos deben ser numéricos.")
            return
        try:
            self.modelo_colas = ModeloColas(d)
        except ValueError as err:
            messagebox.showerror("Datos inconsistentes", str(err))
            return
        messagebox.showinfo(
            "Colas recalculadas",
            f"λ = {num(self.modelo_colas.actual.lambda_, 4)} clientes/h\n"
            f"μ actual = {num(self.modelo_colas.actual.mu, 4)} clientes/h\n"
            f"μ mejorado = {num(self.modelo_colas.mejorado.mu, 4)} clientes/h\n"
            f"ρ actual = {pct(self.modelo_colas.actual.rho)}")
        self.mostrar("colas_datos")

    def restaurar(self) -> None:
        self.datos = self._datos_iniciales()
        self.modelo = ModeloDecision(self.datos)
        self.datos_colas = self._datos_colas_iniciales()
        self.modelo_colas = ModeloColas(self.datos_colas)
        self.datos_proyecto = CP
        self.modelo_proyecto = ModeloProyecto(self.datos_proyecto)
        self.mostrar("datos")

    # =================================================================
    #  PÁGINAS DE LOS 13 PASOS
    # =================================================================
    def pg1(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Matriz de pagos", C["rojo"])
        parrafo(i, f"Utilidad operativa del sábado para cada combinación de decisión "
                   f"y estado regulatorio, expresada en {self.datos.UNIDAD_CORTA}.",
                color=C["texto_suave"])
        self._tabla_pagos(i)
        parrafo(i, f"Suma de probabilidades = {num(sum(m.prior.values()))}  ✔       "
                   f"Objetivo: "
                   f"{'MAXIMIZAR utilidad' if m.objetivo == 'max' else 'MINIMIZAR costo'}",
                negrita=True, color=C["verde"], pady=(10, 0))
        insertar_figura(p, graficas.figura_matriz_criterios(m, None), 980)

    def pg2(self, p) -> None:
        m = self.modelo
        for c in m.criterios:
            color = {"Optimista": C["azul"], "Conservador": C["rojo"]}.get(
                c.nombre.split()[0], C["verde"])
            i = tarjeta(p, c.nombre, color)
            parrafo(i, c.descripcion, color=C["texto_suave"])
            filas = [[f"{a} · {m.nombre_alt[a]}", num(c.valores[a], 0),
                      "◄ ELEGIDA" if a == c.elegida else ""] for a in m.ids_alt]
            destacar = [m.ids_alt.index(c.elegida)]
            tabla(i, ["Alternativa", "Valor del criterio", ""], filas,
                  [320, 220, 160], destacar)
            parrafo(i, f"Decisión por este criterio: {c.elegida} — "
                       f"{m.nombre_alt[c.elegida]}  (valor {num(c.valor_elegido, 0)})",
                    negrita=True, color=color)

        i = tarjeta(p, "Matriz de arrepentimiento", C["morado"])
        cols = ["Alternativa"] + [m.nombre_est[s] for s in m.ids_est] + \
               ["Máximo arrepentimiento"]
        filas = [[f"{a} · {m.nombre_alt[a]}"]
                 + [num(m.matriz_arrepentimiento[a][s], 0) for s in m.ids_est]
                 + [num(max(m.matriz_arrepentimiento[a].values()), 0)]
                 for a in m.ids_alt]
        tabla(i, cols, filas, [300] + [200] * (len(cols) - 1))

        coinciden = len({c.elegida for c in m.criterios}) == 1
        i = tarjeta(p, "Lectura", C["verde"] if coinciden else C["ambar"])
        parrafo(i, "Los tres criterios coinciden en la misma alternativa, lo que "
                   "refuerza la robustez de la decisión." if coinciden else
                   "Los criterios NO coinciden entre sí: "
                   + "; ".join(f"{c.nombre.split('(')[0].strip()} → {c.elegida}"
                               for c in m.criterios)
                   + ". Es esperable, porque cada criterio refleja una actitud "
                     "distinta frente al riesgo. Por eso el estudio continúa "
                     "incorporando las probabilidades, que sí permiten una decisión "
                     "fundamentada.")

    def pg3(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Valor esperado con las probabilidades a priori", C["azul"])
        parrafo(i, "Se pondera cada pago por la probabilidad de su estado:  "
                   "EV(d) = Σ P(s) · pago(d, s)", color=C["texto_suave"])
        formula(i, [m.desarrollo_ev[a] for a in m.ids_alt])
        filas = [[f"{a} · {m.nombre_alt[a]}", num(m.ev_prior[a]),
                  dinero(m.ev_prior[a]), "◄ ÓPTIMA" if a == m.alt_optima_prior else ""]
                 for a in m.ids_alt]
        tabla(i, ["Alternativa", "Valor esperado", "Equivalente", ""], filas,
              [300, 180, 220, 140], [m.ids_alt.index(m.alt_optima_prior)])

        i = tarjeta(p, "Decisión con la información disponible", C["verde"])
        kpis(i, [("Alternativa óptima",
                  f"{m.alt_optima_prior} · {m.nombre_alt[m.alt_optima_prior]}",
                  C["verde"]),
                 ("Valor esperado", dinero(m.ev_optimo_prior), C["verde"]),
                 ("Diferencia con la siguiente",
                  dinero(abs(m.ev_optimo_prior
                             - sorted(m.ev_prior.values())[-2]))
                  if len(m.ids_alt) > 1 else "—", C["azul"])])

    def pg4(self, p) -> None:
        m = self.modelo
        if len(m.ids_est) != 2:
            tarjeta(p, "No disponible", C["ambar"])
            return
        s1, s2 = m.ids_est
        i = tarjeta(p, "Análisis de sensibilidad", C["azul"])
        parrafo(i, f"Se somete a cambio la variable P({s1}) = p (por lo tanto "
                   f"P({s2}) = 1 − p) y se observa cómo se comporta la decisión en "
                   f"todo su recorrido.", color=C["texto_suave"])
        for a in m.ids_alt:
            parrafo(i, f"{a} · {m.nombre_alt[a]}", negrita=True, pady=(10, 2))
            formula(i, m.rectas[a]["pasos"])

        i = tarjeta(p, "Comportamiento de la decisión en todo el recorrido", C["morado"])
        escenarios = sorted(set([x / 10 for x in range(11)] + [m.prior[s1]]
                                + [c.p for c in m.cortes_validos]))
        filas, destacar = [], []
        for k, pp in enumerate(escenarios):
            e = m.escenario(pp)
            etiqueta = ("INDIFERENTE (" + " = ".join(e["empatadas"]) + ")"
                        if e["empate"] else
                        f"{e['elegida']} · {m.nombre_alt[e['elegida']]}")
            if e["empate"] or abs(pp - m.prior[s1]) < 1e-12:
                destacar.append(k)
            filas.append([pct(pp, 2 if e["empate"] else 0)]
                         + [num(e["ev"][a]) for a in m.ids_alt]
                         + [etiqueta, num(e["valor"])])
        tabla(i, [f"P({s1})"] + [f"EV({a})" for a in m.ids_alt]
              + ["Decisión óptima", "Valor"], filas,
              [120] + [150] * len(m.ids_alt) + [280, 150], destacar)

        i = tarjeta(p, "Tramos de dominancia", C["verde"])
        for t in m.tramos:
            parrafo(i, f"▪  Si {pct(t.p_ini, 2)} ≤ P({s1}) ≤ {pct(t.p_fin, 2)}  →  la "
                       f"decisión óptima es {t.dominante} · {m.nombre_alt[t.dominante]}",
                    pady=(4, 0))

    def pg5(self, p) -> None:
        m = self.modelo
        if len(m.ids_est) != 2:
            tarjeta(p, "El análisis gráfico requiere exactamente 2 estados.", C["ambar"])
            return
        i = tarjeta(p, "Análisis gráfico", C["azul"])
        parrafo(i, "Cada alternativa es una recta EV(d) = m·p + b sobre el eje "
                   "p = P(s1) ∈ [0, 1]. Con dos puntos por recta basta para graficarla.",
                color=C["texto_suave"])
        filas = [[a, m.rectas[a]["ecuacion"],
                  f"(0 , {num(m.rectas[a]['punto_p0'][1], 0)})",
                  f"(1 , {num(m.rectas[a]['punto_p1'][1], 0)})"] for a in m.ids_alt]
        tabla(i, ["Alternativa", "Ecuación de la recta", "Punto p = 0", "Punto p = 1"],
              filas, [140, 300, 200, 200])
        insertar_figura(p, graficas.figura_sensibilidad(m, None), 1000)

    def pg6(self, p) -> None:
        m = self.modelo
        if not m.cortes:
            tarjeta(p, "Los puntos de corte requieren exactamente 2 estados.", C["ambar"])
            return
        for c in m.cortes:
            i = tarjeta(p, f"Igualación  {c.a}  =  {c.b}",
                        C["verde"] if c.valido else C["ambar"])
            formula(i, c.algebra)
            if c.valido:
                kpis(i, [("Punto de corte", pct(c.p), C["ambar"]),
                         ("Valor en p = " + num(c.p, 4), dinero(c.valor), C["azul"])])
            else:
                parrafo(i, "El corte cae fuera del intervalo [0, 1]: una alternativa "
                           "domina a la otra en todo el recorrido.", color=C["ambar"])
        u = m.umbral_decisorio
        if u:
            p1 = m.prior[m.ids_est[0]]
            otra = u.b if u.a == m.alt_optima_prior else u.a
            estable = abs(p1 - u.p) > 0.10
            i = tarjeta(p, "Interpretación del umbral",
                        C["verde"] if estable else C["ambar"])
            parrafo(i, f"P({m.ids_est[0]}) debe "
                       f"{'superar' if p1 < u.p else 'caer por debajo de'} "
                       f"{pct(u.p)} para que convenga cambiar a {otra} · "
                       f"{m.nombre_alt[otra]}.")
            kpis(i, [("Valor actual estimado", pct(p1, 0), C["azul"]),
                     ("Umbral de cambio", pct(u.p), C["ambar"]),
                     ("Margen", f"{num(abs(p1 - u.p) * 100)} p.p.",
                      C["verde"] if estable else C["rojo"]),
                     ("Decisión", "ESTABLE" if estable else "SENSIBLE",
                      C["verde"] if estable else C["rojo"])])

    def pg7(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Valor esperado de la información perfecta (EVPI)", C["verde"])
        parrafo(i, "Si se supiera con certeza qué estado va a ocurrir, se elegiría la "
                   "mejor alternativa en cada caso.", color=C["texto_suave"])
        filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
                  f"{m.mejor_decision_por_estado[s]} · "
                  f"{m.nombre_alt[m.mejor_decision_por_estado[s]]}",
                  dinero(m.mejor_por_estado[s])] for s in m.ids_est]
        tabla(i, ["Estado", "Probabilidad", "Mejor decisión si ocurre", "Pago"],
              filas, [280, 160, 300, 200])
        formula(i, m.desarrollo_evpi)
        kpis(i, [("EV con información perfecta", dinero(m.ev_con_info_perfecta),
                  C["verde"]),
                 ("EV de la decisión actual", dinero(m.ev_optimo_prior), C["azul"]),
                 ("EVPI", dinero(m.evpi), C["ambar"])])

        i = tarjeta(p, "Lectura gerencial", C["ambar"])
        parrafo(i, f"El EVPI de {dinero(m.evpi)} es el máximo que la empresa debería "
                   f"pagar por eliminar por completo la incertidumbre regulatoria. "
                   f"Ningún estudio, consultoría o asesoría puede valer más que esta "
                   f"cifra.")

    def pg8(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Información muestral — consultoría jurídica/operativa", C["azul"])
        parrafo(i, "Antes de decidir se puede contratar una consultoría cuyo concepto "
                   "es un indicador imperfecto del estado real. Su confiabilidad se "
                   "expresa como P(indicador | estado).", color=C["texto_suave"])
        cols = ["Indicador"] + [f"P( · | {s})" for s in m.ids_est]
        filas = [[f"{ind} · {m.nombre_ind[ind]}"]
                 + [num(m.verosimilitud[ind][s]) for s in m.ids_est]
                 for ind in m.ids_ind]
        filas.append(["Suma por columna"]
                     + [num(sum(m.verosimilitud[ind][s] for ind in m.ids_ind))
                        for s in m.ids_est])
        tabla(i, cols, filas, [280] + [200] * len(m.ids_est))

        i = tarjeta(p, "Probabilidades marginales de cada resultado", C["morado"])
        lineas = []
        for r in m.ramas:
            det = " + ".join(f"{num(m.verosimilitud[r.indicador][s])}·{num(m.prior[s])}"
                             for s in m.ids_est)
            lineas.append(f"P({r.indicador}) = {det} = {num(r.prob_indicador, 4)}")
        lineas.append(f"Suma = {num(sum(r.prob_indicador for r in m.ramas), 4)}  ✔")
        formula(i, lineas)

    def pg9(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Teorema de Bayes", C["azul"])
        parrafo(i, "P(s | indicador) = [ P(indicador | s) · P(s) ] / P(indicador)",
                negrita=True)
        for r in m.ramas:
            cambia = r.elegida != m.alt_optima_prior
            i = tarjeta(p, f"Resultado {r.nombre}  ({r.indicador})   ·   "
                           f"P({r.indicador}) = {num(r.prob_indicador, 4)}",
                        C["rojo"] if cambia else C["verde"])
            filas = [[f"{s} · {m.nombre_est[s]}", num(m.prior[s]),
                      num(m.verosimilitud[r.indicador][s]), num(r.conjuntas[s], 4),
                      num(r.posteriores[s], 4), pct(r.posteriores[s])]
                     for s in m.ids_est]
            filas.append(["Total", num(sum(m.prior.values())), "—",
                          num(r.prob_indicador, 4),
                          num(sum(r.posteriores.values()), 4), "100,00%"])
            tabla(i, ["Estado", "P(s) previa", f"P({r.indicador}|s)", "Conjunta",
                      "P(s | ind.)", "%"], filas, [260, 140, 140, 140, 140, 120])
            lineas = []
            for a in m.ids_alt:
                det = " + ".join(f"{num(r.posteriores[s], 4)}·({num(m.pagos[a][s], 0)})"
                                 for s in m.ids_est)
                marca = "   ◄ ÓPTIMA" if a == r.elegida else ""
                lineas.append(f"EV({a}|{r.indicador}) = {det} = {num(r.ev[a])}{marca}")
            formula(i, lineas)
            parrafo(i, f"Si el estudio resulta {r.nombre}, la decisión "
                       f"{'CAMBIA a' if cambia else 'se RATIFICA en'} {r.elegida} · "
                       f"{m.nombre_alt[r.elegida]} con {dinero(r.valor)}.",
                    negrita=True, color=C["rojo"] if cambia else C["verde"])
        insertar_figura(p, graficas.figura_bayes(m, None), 1000)

    def pg10(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Árboles de decisión", C["azul"])
        parrafo(i, "Los nodos cuadrados son decisiones (las controla la empresa) y los "
                   "circulares son nodos de azar (los controla el entorno regulatorio). "
                   "La resolución es por inducción hacia atrás: se promedia en los "
                   "nodos de azar y se optimiza en los nodos de decisión.",
                color=C["texto_suave"])
        kpis(i, [("Raíz del árbol sin estudio", dinero(m.ev_optimo_prior), C["azul"]),
                 ("Raíz del árbol con estudio", dinero(m.ev_con_info_muestral),
                  C["verde"])])
        insertar_figura(p, graficas.figura_arbol_prior(m, None), 1000)
        insertar_figura(p, graficas.figura_arbol_muestral(m, None), 1000)

    def pg11(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Valor esperado de la información muestral (EVSI)", C["azul"])
        filas = [[f"{r.indicador} · {r.nombre}", num(r.prob_indicador, 4),
                  f"{r.elegida} · {m.nombre_alt[r.elegida]}", num(r.valor),
                  num(r.prob_indicador * r.valor)] for r in m.ramas]
        tabla(i, ["Resultado del estudio", "P(resultado)", "Decisión óptima",
                  "Valor esperado", "Aporte ponderado"], filas,
              [240, 160, 280, 180, 180])
        formula(i, m.desarrollo_evsi[:2])
        kpis(i, [("EV SIN información muestral", dinero(m.ev_sin_info_muestral),
                  C["texto_suave"]),
                 ("EV CON información muestral", dinero(m.ev_con_info_muestral),
                  C["azul"]),
                 ("EVSI", dinero(m.evsi), C["verde"])])
        parrafo(i, f"Contratar la consultoría solo tiene sentido si su honorario es "
                   f"inferior a {dinero(m.evsi)}.", negrita=True, color=C["ambar"],
                pady=(10, 0))

    def pg12(self, p) -> None:
        m = self.modelo
        i = tarjeta(p, "Eficiencia del estudio de mercado", C["verde"])
        formula(i, [m.desarrollo_evsi[2]])
        tabla(i, ["Concepto", "Valor", "Equivalente"], [
            ["EVSI — información muestral (imperfecta)", num(m.evsi), dinero(m.evsi)],
            ["EVPI — información perfecta", num(m.evpi), dinero(m.evpi)],
            ["Eficiencia = EVSI / EVPI", pct(m.eficiencia),
             m.calificacion_eficiencia.upper()],
        ], [420, 180, 240])

        # Barra de eficiencia dibujada
        lienzo = tk.Canvas(i, height=42, bg=C["panel"], highlightthickness=0)
        lienzo.pack(fill="x", pady=(12, 4))

        def pintar(ev=None):
            lienzo.delete("all")
            ancho = max(lienzo.winfo_width(), 400) - 20
            lienzo.create_rectangle(10, 10, 10 + ancho, 36, fill="#e2e8f0",
                                    outline="")
            frac = min(max(m.eficiencia, 0), 1) if m.eficiencia == m.eficiencia else 0
            color = C["rojo"] if frac < 0.2 else (
                C["ambar"] if frac < 0.5 else C["verde"])
            if frac > 0:
                lienzo.create_rectangle(10, 10, 10 + ancho * frac, 36, fill=color,
                                        outline="")
            lienzo.create_text(10 + ancho / 2, 23,
                               text=f"{pct(m.eficiencia)}  ·  "
                                    f"{m.calificacion_eficiencia.upper()}",
                               fill=C["texto"], font=("DejaVu Sans", 11, "bold"))
        lienzo.bind("<Configure>", pintar)
        self.after(60, pintar)

        rec = m.recomienda_estudio
        i = tarjeta(p, "Lectura", C["verde"] if rec else C["rojo"])
        parrafo(i, f"Una eficiencia del {pct(m.eficiencia)} significa que el estudio "
                   f"solo captura esa fracción del beneficio que aportaría saber con "
                   f"certeza el estado regulatorio. La calificación es "
                   f"{m.calificacion_eficiencia.upper()}, por lo que "
                   f"{'SÍ se recomienda' if rec else 'NO se recomienda'} contratarlo.",
                negrita=True, color=C["verde"] if rec else C["rojo"])

    def pg13(self, p) -> None:
        m = self.modelo
        rec = m.recomienda_estudio
        i = tarjeta(p, "Resumen ejecutivo", C["azul"])
        kpis(i, [("Alternativa seleccionada",
                  f"{m.alt_optima_prior} · {m.nombre_alt[m.alt_optima_prior]}",
                  C["verde"]),
                 ("Utilidad esperada", dinero(m.ev_optimo_prior), C["verde"]),
                 ("¿Contratar consultoría?", "SÍ" if rec else "NO",
                  C["verde"] if rec else C["rojo"])])
        kpis(i, [("Umbral de cambio",
                  pct(m.umbral_decisorio.p) if m.umbral_decisorio else "—", C["ambar"]),
                 ("EVPI", dinero(m.evpi), C["azul"]),
                 ("EVSI", dinero(m.evsi), C["azul"]),
                 ("Eficiencia", pct(m.eficiencia), C["morado"])])

        colores = [C["azul"], C["morado"], C["verde"], C["ambar"], C["rojo"], C["azul"]]
        for k, texto in enumerate(m.texto_decision_final()):
            titulo, _, cuerpo = texto.partition(". ")
            i = tarjeta(p, titulo if len(titulo) < 70 else "", colores[k % len(colores)])
            parrafo(i, cuerpo or texto)

        insertar_figura(p, graficas.figura_resumen(m, None), 1000)

    # =================================================================
    #  PÁGINAS DE TEORÍA DE COLAS
    # =================================================================
    def pg_colas_contexto(self, p) -> None:
        d = self.datos_colas
        mc = self.modelo_colas

        enc = tk.Frame(p, bg=C["azul"])
        enc.pack(fill="x", padx=22, pady=(6, 10))
        tk.Label(enc, text=d.TITULO_COLAS, bg=C["azul"], fg="white", wraplength=980,
                 font=("DejaVu Sans", 15, "bold"), justify="center").pack(pady=(18, 4))
        tk.Label(enc, text=d.SUBTITULO_COLAS, bg=C["azul"], fg="#dbeafe",
                 font=("DejaVu Sans", 10), wraplength=980).pack(pady=(0, 18))

        i = tarjeta(p, "¿QUÉ ES EL SISTEMA DE COLAS?", C["azul"])
        parrafo(i, d.CONTEXTO_COLAS)
        parrafo(i, "El sistema se modela como una cola M/M/1: llegadas tipo "
                   "Poisson, tiempos de servicio exponenciales y un único servidor.",
                color=C["texto_suave"])

        i = tarjeta(p, "¿CÓMO SE OBTIENEN λ Y μ?", C["morado"])
        parrafo(i, "A partir de los datos operativos reales de la empresa, "
                   "no de supuestos académicos:")
        formula(i, mc.actual.desarrollo["lambda"])
        formula(i, mc.actual.desarrollo["mu"])
        formula(i, mc.actual.desarrollo["rho"])

        i = tarjeta(p, "MEJORA PROPUESTA (SIN CONTRATAR PERSONAL)", C["verde"])
        parrafo(i, d.MEJORA_DESCRIPCION)
        parrafo(i, "Justificación:")
        parrafo(i, d.MEJORA_JUSTIFICACION, color=C["texto_suave"])
        parrafo(i, f"Con esta mejora, el tiempo de servicio baja de "
                   f"{num(mc.actual.tiempo_servicio, 0)} a "
                   f"{num(mc.mejorado.tiempo_servicio, 0)} segundos, "
                   f"elevando μ de {num(mc.actual.mu, 4)} a "
                   f"{num(mc.mejorado.mu, 4)} clientes/hora.",
                negrita=True, color=C["verde"])

    def pg_colas_datos(self, p) -> None:
        d = self.datos_colas
        mc = self.modelo_colas

        i = tarjeta(p, "DATOS DEL SISTEMA DE COLAS — EDITABLES", C["ambar"])
        parrafo(i, "Modifica los valores y pulsa «Recalcular colas». Toda la "
                   "sección de colas (cálculos, gráficas y conclusión) se "
                   "actualiza automáticamente.",
                color=C["texto_suave"])

        self.entradas_colas = {}

        # Panel de datos operativos
        i = tarjeta(p, "Datos operativos", C["azul"])
        rej = tk.Frame(i, bg=C["panel"])
        rej.pack(anchor="w")

        campos = [
            ("Ventas mínimas por día (COP):", "ventas_min", d.VENTAS_MIN_DIA),
            ("Ventas máximas por día (COP):", "ventas_max", d.VENTAS_MAX_DIA),
            ("Horas de operación al día:", "horas", d.HORAS_OPERACION),
            ("Tiempo de servicio actual (s):", "tiempo_servicio",
             d.TIEMPO_SERVICIO_ACTUAL),
            ("Factor de mejora (0–1):", "factor_mejora", d.FACTOR_MEJORA),
        ]
        for r, (etiqueta, clave, valor) in enumerate(campos):
            tk.Label(rej, text=etiqueta, bg=C["panel"], anchor="w",
                     font=("DejaVu Sans", 10)).grid(row=r, column=0, sticky="w",
                                                    pady=5, padx=(0, 12))
            var = tk.StringVar(value=str(valor))
            tk.Entry(rej, textvariable=var, width=14, justify="center",
                     font=("DejaVu Sans Mono", 11), relief="solid", bd=1).grid(
                row=r, column=1, padx=10, pady=5, ipady=4)
            self.entradas_colas[clave] = var

        parrafo(i, "Precios de pasaje usados para el promedio: "
                   + " · ".join(f"{p:,.0f}".replace(",", ".")
                                for p in d.PRECIOS_PASAJE) + " COP",
                color=C["texto_suave"], tam=9)

        # Panel de referencia
        i = tarjeta(p, "Datos actuales calculados", C["morado"])
        formula(i, mc.actual.desarrollo["lambda"])
        formula(i, mc.actual.desarrollo["mu"])

        # Botones
        i = tarjeta(p, "", C["verde"])
        botones = tk.Frame(i, bg=C["panel"])
        botones.pack(anchor="w")
        tk.Button(botones, text="↻  Recalcular colas",
                  command=self.recalcular_colas, bg=C["verde"], fg="white",
                  relief="flat", cursor="hand2", activebackground="#047857",
                  activeforeground="white", font=("DejaVu Sans", 11, "bold"),
                  padx=22, pady=10).pack(side="left")
        tk.Button(botones, text="⟲  Restaurar valores originales",
                  command=self.restaurar, bg="#e2e8f0", fg=C["texto"],
                  relief="flat", cursor="hand2", font=("DejaVu Sans", 11),
                  padx=22, pady=10).pack(side="left", padx=12)

    def pg_colas_actual(self, p) -> None:
        m = self.modelo_colas.actual
        mc = self.modelo_colas

        i = tarjeta(p, "CÁLCULO DE LOS 7 PASOS — SISTEMA ACTUAL", C["azul"])
        parrafo(i, f"λ = {num(m.lambda_, 4)} clientes/hora   ·   "
                   f"μ = {num(m.mu, 4)} clientes/hora   ·   "
                   f"ρ = {pct(m.rho)}", negrita=True, color=C["azul"])
        parrafo(i, f"Sistema M/M/1 con un único servidor (vendedor). "
                   f"Buses por día: {mc.cfg.BUSES_POR_DIA}.",
                color=C["texto_suave"])

        pasos = [
            ("p0", "1. P0 — Probabilidad de que el sistema esté vacío"),
            ("lq", "2. Lq — Número promedio de clientes en la cola"),
            ("l",  "3. L  — Número promedio de clientes en el sistema"),
            ("wq", "4. Wq — Tiempo promedio de espera en la cola"),
            ("w",  "5. W  — Tiempo promedio en el sistema"),
            ("pw", "6. Pw — Probabilidad de que un cliente tenga que esperar"),
        ]
        for clave, titulo in pasos:
            i = tarjeta(p, titulo, C["azul"])
            formula(i, m.desarrollo[clave])

        i = tarjeta(p, "7. Pn — Probabilidad de n clientes en el sistema",
                    C["morado"])
        filas = [[n, num(m.pn[n], 6), pct(m.pn[n])]
                 for n in sorted(m.pn.keys())]
        tabla(i, ["n", "P(n)", "%"], filas, [80, 180, 180])

        insertar_figura(p, graficas_colas.figura_flujo(self.modelo_colas, None), 900)

    def pg_colas_mejora(self, p) -> None:
        m = self.modelo_colas.mejorado
        d = self.datos_colas
        mc = self.modelo_colas

        i = tarjeta(p, "MEJORA PROPUESTA (SIN CONTRATAR PERSONAL)", C["verde"])
        parrafo(i, d.MEJORA_DESCRIPCION)
        parrafo(i, "Justificación:")
        parrafo(i, d.MEJORA_JUSTIFICACION, color=C["texto_suave"])
        parrafo(i, f"Tiempo de servicio: {num(d.TIEMPO_SERVICIO_ACTUAL, 0)} s "
                   f"→ {num(m.tiempo_servicio, 0)} s      "
                   f"μ: {num(mc.actual.mu, 4)} → {num(m.mu, 4)} clientes/hora",
                negrita=True, color=C["verde"])

        i = tarjeta(p, "CÁLCULO DE LOS 7 PASOS — SISTEMA MEJORADO", C["azul"])
        parrafo(i, f"λ = {num(m.lambda_, 4)} clientes/hora   ·   "
                   f"μ = {num(m.mu, 4)} clientes/hora   ·   "
                   f"ρ = {pct(m.rho)}", negrita=True, color=C["azul"])

        pasos = [
            ("p0", "1. P0 — Probabilidad de que el sistema esté vacío"),
            ("lq", "2. Lq — Número promedio de clientes en la cola"),
            ("l",  "3. L  — Número promedio de clientes en el sistema"),
            ("wq", "4. Wq — Tiempo promedio de espera en la cola"),
            ("w",  "5. W  — Tiempo promedio en el sistema"),
            ("pw", "6. Pw — Probabilidad de que un cliente tenga que esperar"),
        ]
        for clave, titulo in pasos:
            i = tarjeta(p, titulo, C["verde"])
            formula(i, m.desarrollo[clave])

        i = tarjeta(p, "7. Pn — Probabilidad de n clientes en el sistema",
                    C["morado"])
        filas = [[n, num(m.pn[n], 6), pct(m.pn[n])]
                 for n in sorted(m.pn.keys())]
        tabla(i, ["n", "P(n)", "%"], filas, [80, 180, 180])

    def pg_colas_comparacion(self, p) -> None:
        a = self.modelo_colas.actual
        b = self.modelo_colas.mejorado
        mc = self.modelo_colas

        i = tarjeta(p, "COMPARACIÓN: SISTEMA ACTUAL vs. MEJORADO", C["morado"])
        filas = [
            ["λ (clientes/hora)", num(a.lambda_, 4), num(b.lambda_, 4), "—"],
            ["μ (clientes/hora)", num(a.mu, 4), num(b.mu, 4),
             f"+{num(b.mu - a.mu, 4)}"],
            ["Tiempo servicio (s)", num(a.tiempo_servicio, 0),
             num(b.tiempo_servicio, 0),
             f"−{num(a.tiempo_servicio - b.tiempo_servicio, 0)}"],
            ["ρ (utilización)", pct(a.rho), pct(b.rho), f"−{pct(a.rho - b.rho)}"],
            ["P0 (sistema vacío)", pct(a.p0), pct(b.p0), f"+{pct(b.p0 - a.p0)}"],
            ["Lq (clientes en cola)", num(a.lq, 4), num(b.lq, 4),
             f"−{num(mc.mejora_lq, 2)}%"],
            ["L (clientes en sistema)", num(a.l, 4), num(b.l, 4),
             f"−{num(mc.mejora_l, 2)}%"],
            ["Wq (min en cola)", num(a.wq * 60, 2), num(b.wq * 60, 2),
             f"−{num(mc.mejora_wq, 2)}%"],
            ["W (min en sistema)", num(a.w * 60, 2), num(b.w * 60, 2),
             f"−{num(mc.mejora_w, 2)}%"],
            ["Pw (prob. de esperar)", pct(a.pw), pct(b.pw),
             f"−{pct(a.pw - b.pw)}"],
        ]
        tabla(i, ["Indicador", "Actual", "Mejorado", "Cambio"], filas,
              [280, 150, 150, 150])

        insertar_figura(p, graficas_colas.figura_comparacion(self.modelo_colas, None),
                        1000)
        insertar_figura(p, graficas_colas.figura_pn(self.modelo_colas, None), 1000)
        insertar_figura(p, graficas_colas.figura_resumen_colas(self.modelo_colas, None),
                        1000)

        colores = [C["azul"], C["morado"], C["verde"], C["ambar"], C["rojo"]]
        for k, texto in enumerate(mc.texto_conclusion()):
            titulo, _, cuerpo = texto.partition(". ")
            i = tarjeta(p, titulo if len(titulo) < 70 else "",
                        colores[k % len(colores)])
            parrafo(i, cuerpo or texto)

    # =================================================================
    #  PÁGINA: CALCULADORA DE PROBABILIDADES
    # =================================================================
    def pg_colas_calculadora(self, p) -> None:
        mc = self.modelo_colas
        calc = CalculadoraProbabilidades(mc.actual.lambda_, mc.actual.mu)

        i = tarjeta(p, "CALCULADORA DE PROBABILIDADES — POISSON Y EXPONENCIAL",
                    C["azul"])
        parrafo(i, "Esta calculadora te permite responder preguntas como: "
                "«¿Cuál es la probabilidad de que lleguen 3 o más clientes en "
                "30 minutos?» o «¿Cuál es la probabilidad de que el servicio "
                "tarde menos de 45 segundos?». Útil para demostraciones en clase.",
                color=C["texto_suave"])

        # ---------------- POISSON ----------------
        i = tarjeta(p, "1) DISTRIBUCIÓN DE POISSON (llegadas)", C["morado"])
        formula(i, [
            "P(X = x) = (λ·t)^x · e^(−λ·t) / x!",
            f"λ = {num(mc.actual.lambda_, 4)} clientes/hora",
        ])

        rej = tk.Frame(i, bg=C["panel"]); rej.pack(anchor="w", pady=6)

        tk.Label(rej, text="x (número de llegadas):", bg=C["panel"],
                font=("DejaVu Sans", 10)).grid(row=0, column=0, sticky="w", pady=4)
        var_x = tk.StringVar(value="3")
        tk.Entry(rej, textvariable=var_x, width=10, justify="center").grid(
            row=0, column=1, padx=10, ipady=3)

        tk.Label(rej, text="Intervalo de tiempo (horas):", bg=C["panel"],
                font=("DejaVu Sans", 10)).grid(row=1, column=0, sticky="w", pady=4)
        var_t = tk.StringVar(value="1.0")
        tk.Entry(rej, textvariable=var_t, width=10, justify="center").grid(
            row=1, column=1, padx=10, ipady=3)

        salida_poisson = tk.Label(i, text="", bg=C["panel"], fg=C["texto"],
                                justify="left", anchor="w",
                                font=("DejaVu Sans Mono", 11))
        salida_poisson.pack(fill="x", pady=6)

        def calcular_poisson():
            try:
                x = int(var_x.get())
                factor = float(var_t.get().replace(",", "."))
                if x < 0 or factor <= 0:
                    raise ValueError
            except ValueError:
                salida_poisson.configure(
                    text="⚠ Ingresa x (entero ≥ 0) y un intervalo positivo.",
                    fg=C["rojo"])
                return
            calc = CalculadoraProbabilidades(mc.actual.lambda_, mc.actual.mu)
            px = calc.poisson_exacta(x, factor)
            ple = calc.poisson_acumulada(x, factor)
            pge = calc.poisson_mayor_igual(x, factor)
            lam_ef = mc.actual.lambda_ * factor
            txt = (f"λ efectivo (λ·t) = {num(lam_ef, 4)}\n"
                f"P(X = {x})   = {num(px, 6)}   ({pct(px)})\n"
                f"P(X ≤ {x})   = {num(ple, 6)}   ({pct(ple)})\n"
                f"P(X ≥ {x})   = {num(pge, 6)}   ({pct(pge)})")
            salida_poisson.configure(text=txt, fg=C["texto"])

        tk.Button(i, text="Calcular probabilidad Poisson",
                command=calcular_poisson, bg=C["morado"], fg="white",
                relief="flat", cursor="hand2", font=("DejaVu Sans", 10, "bold"),
                padx=18, pady=8).pack(anchor="w", pady=4)

        # Mostrar valores iniciales
        calcular_poisson()

        insertar_figura(p, graficas_colas.figura_poisson(
            mc, None, x_hasta=15, factor_tiempo=float(var_t.get().replace(",", ".")),
            x_marcado=int(var_x.get())), 1000)

        # ---------------- EXPONENCIAL ----------------
        i = tarjeta(p, "2) DISTRIBUCIÓN EXPONENCIAL (servicio)", C["verde"])
        formula(i, [
            "P(T ≤ t) = 1 − e^(−μ·t)",
            "P(T > t) = e^(−μ·t)",
            f"μ actual = {num(mc.actual.mu, 4)} clientes/hora",
            f"μ mejorado = {num(mc.mejorado.mu, 4)} clientes/hora",
        ])

        rej = tk.Frame(i, bg=C["panel"]); rej.pack(anchor="w", pady=6)

        tk.Label(rej, text="Tiempo t (segundos):", bg=C["panel"],
                font=("DejaVu Sans", 10)).grid(row=0, column=0, sticky="w", pady=4)
        var_tseg = tk.StringVar(value="45")
        tk.Entry(rej, textvariable=var_tseg, width=10, justify="center").grid(
            row=0, column=1, padx=10, ipady=3)

        tk.Label(rej, text="¿Qué sistema?", bg=C["panel"],
                font=("DejaVu Sans", 10)).grid(row=1, column=0, sticky="w", pady=4)
        var_sis = tk.StringVar(value="actual")
        ttk.Combobox(rej, textvariable=var_sis,
                    values=["actual", "mejorado"], width=12,
                    state="readonly").grid(row=1, column=1, padx=10, pady=4)

        salida_exp = tk.Label(i, text="", bg=C["panel"], fg=C["texto"],
                            justify="left", anchor="w",
                            font=("DejaVu Sans Mono", 11))
        salida_exp.pack(fill="x", pady=6)

        def calcular_exponencial():
            try:
                t_s = float(var_tseg.get().replace(",", "."))
                if t_s <= 0:
                    raise ValueError
            except ValueError:
                salida_exp.configure(text="⚠ Ingresa un tiempo positivo (en segundos).",
                                    fg=C["rojo"])
                return
            t_h = t_s / 3600.0
            mu = (mc.mejorado.mu if var_sis.get() == "mejorado"
                else mc.actual.mu)
            calc = CalculadoraProbabilidades(mc.actual.lambda_, mu)
            ple = calc.exponencial_menor(t_h)
            pge = calc.exponencial_mayor(t_h)
            txt = (f"t = {num(t_s, 2)} s = {num(t_h, 6)} h\n"
                f"μ = {num(mu, 4)} clientes/hora\n"
                f"P(T ≤ t) = {num(ple, 6)}   ({pct(ple)})\n"
                f"P(T > t) = {num(pge, 6)}   ({pct(pge)})")
            salida_exp.configure(text=txt, fg=C["texto"])

        tk.Button(i, text="Calcular probabilidad exponencial",
                command=calcular_exponencial, bg=C["verde"], fg="white",
                relief="flat", cursor="hand2", font=("DejaVu Sans", 10, "bold"),
                padx=18, pady=8).pack(anchor="w", pady=4)

        calcular_exponencial()

        insertar_figura(p, graficas_colas.figura_exponencial(
            mc, None, t_max=0.05,
            t_marcado=float(var_tseg.get().replace(",", ".")) / 3600.0), 1000)

        # ---------------- EJEMPLO DEL PROFESOR ----------------
        i = tarjeta(p, "3) EJEMPLO DE LA CLASE (P(X ≥ 3) con λ = ?)", C["ambar"])
        parrafo(i, "En el tablero del profesor se calculó P(X ≥ 3) = 1 − P(X ≤ 2) "
                "= 1 − (P₀ + P₁ + P₂) = 1 − 0.4219 ≈ 0.5781 → ~35 min. "
                "Aquí puedes reproducir ese tipo de cálculo ingresando cualquier "
                "λ y cualquier x.")
        parrafo(i, "Sugerencia: prueba con λ = 2.6256 (el del sistema real) y "
                "x = 3. Verás P(X ≥ 3) en el intervalo de 1 hora.",
                color=C["texto_suave"])

    # =================================================================
    #  PÁGINAS DE DIRECCIÓN DE PROYECTOS
    # =================================================================
    def pg_proyecto_contexto(self, p):
        d, m = self.datos_proyecto, self.modelo_proyecto
        i = tarjeta(p, "DIRECCIÓN DE PROYECTOS — DESPACHO DE UN BUS", C["azul"])
        parrafo(i, d.CONTEXTO_PROYECTO)
        parrafo(i, f"Duración total esperada (Ruta Crítica): {num(m.duracion_total, 2)} minutos.", negrita=True)
        
        i = tarjeta(p, "TABLA DE ACTIVIDADES (PERT)", C["morado"])
        filas = [[a.id, a.nombre, ", ".join(a.pre) or "—", num(a.O,0), num(a.M,0), num(a.P,0), num(a.te, 2)] for a in m.actividades.values()]
        tabla(i, ["ID", "Actividad", "Predecesoras", "O", "M", "P", "TE"], filas, [60, 300, 150, 60, 60, 60, 80])

    def pg_proyecto_red(self, p):
        i = tarjeta(p, "RED DEL PROYECTO Y CÁLCULO DE TIEMPOS", C["verde"])
        parrafo(i, "Las actividades en rojo son críticas. Si se retrasan, el bus sale tarde.")
        insertar_figura(p, graficas_proyectos.figura_red(self.modelo_proyecto, None), 1000)

    def pg_proyecto_gantt(self, p):
        m = self.modelo_proyecto
        i = tarjeta(p, "RUTA CRÍTICA Y HOLGURAS", C["rojo"])
        parrafo(i, f"Ruta Crítica: {' → '.join(m.criticas)}")
        parrafo(i, f"Probabilidad de salir en <= {m.cfg.TIEMPO_META} min: {pct(m.probabilidad)}", negrita=True)
        insertar_figura(p, graficas_proyectos.figura_gantt(m, None), 1000)

    # =================================================================
    #  EXPORTAR
    # =================================================================
    def exportar(self) -> None:
        carpeta = filedialog.askdirectory(title="Carpeta donde guardar el informe")
        if not carpeta:
            return
        try:
            import main as prog
            archivos = graficas.generar_todas(self.modelo, carpeta)
            archivos.update(graficas_colas.generar_todas_colas(self.modelo_colas, carpeta))
            archivos.update(graficas_proyectos.generar_todas_proyectos(self.modelo_proyecto, carpeta))
            
            texto = prog.construir_reporte(self.modelo, archivos, None,
                                           self.modelo_colas, self.modelo_proyecto)
            ruta = os.path.join(carpeta, "reporte.txt")
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(texto)
        except Exception as err:
            messagebox.showerror("Error al exportar", str(err))
            return
        self.etiqueta_pie.configure(text=f"Informe exportado a {carpeta}")
        messagebox.showinfo("Exportación completa",
                            f"Se guardaron todas las figuras (decisiones, colas y "
                            f"proyectos) y el informe completo en:\n{carpeta}")


if __name__ == "__main__":
    Aplicacion().mainloop()