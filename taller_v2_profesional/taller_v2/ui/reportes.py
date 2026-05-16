"""
ui/reportes.py — Tab: Reportes con filtro por fecha.

Genera un gráfico de ingresos diarios y un resumen tabular por pieza
para el rango de fechas seleccionado.
Los filtros de fecha se aplican en SQL (no post-carga en Python).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import THEME
from services import VentasService, InventarioService


class ReportesTab:
    """Tab de reportes: filtro de fechas + gráfico + resumen textual."""

    def __init__(
        self,
        parent: ttk.Notebook,
        ven_svc: VentasService,
        inv_svc: InventarioService,
    ) -> None:
        self._ven = ven_svc
        self._inv = inv_svc
        self.frame = ttk.Frame(parent)
        self._build()

    # ── Construcción ─────────────────────────────────────────────
    def _build(self) -> None:
        self._build_filter_bar()
        self._build_chart()
        self._build_text()

    def _build_filter_bar(self) -> None:
        frm = ttk.Frame(self.frame)
        frm.pack(fill=tk.X, padx=16, pady=12)

        ttk.Label(frm, text="Desde:").pack(side=tk.LEFT)
        self._ent_ini = ttk.Entry(frm, width=12)
        self._ent_ini.pack(side=tk.LEFT, padx=6)

        ttk.Label(frm, text="Hasta:").pack(side=tk.LEFT)
        self._ent_fin = ttk.Entry(frm, width=12)
        self._ent_fin.pack(side=tk.LEFT, padx=6)

        ttk.Button(
            frm, text="📊  Generar Reporte", command=self._generar
        ).pack(side=tk.LEFT, padx=12)

        ttk.Label(
            frm, text="(YYYY-MM-DD  |  vacío = sin límite)",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

    def _build_chart(self) -> None:
        self._fig, self._ax = plt.subplots(
            figsize=(10, 3.5), facecolor=THEME["bg"]
        )
        self._ax.set_facecolor(THEME["surface"])
        for sp in self._ax.spines.values():
            sp.set_edgecolor(THEME["border"])

        self._canvas = FigureCanvasTkAgg(self._fig, master=self.frame)
        self._canvas.get_tk_widget().pack(fill=tk.X, padx=16, pady=4)

    def _build_text(self) -> None:
        self._txt = tk.Text(
            self.frame, height=10,
            state=tk.DISABLED,
            font=("Cascadia Code", 10),
            bg=THEME["surface2"], fg=THEME["text"],
            relief="flat", padx=12, pady=8,
        )
        self._txt.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 12))

    # ── Generación ───────────────────────────────────────────────
    def _generar(self) -> None:
        """
        Genera el reporte para el rango indicado.
        Los filtros se pasan al servicio → repositorio → SQL.
        """
        fecha_ini = self._ent_ini.get().strip() or None
        fecha_fin = self._ent_fin.get().strip() or None

        df  = self._ven.get_df(fecha_ini, fecha_fin)
        kpis = self._ven.kpis(df)

        self._render_chart(df)
        self._render_text(df, kpis, fecha_ini, fecha_fin)

    def _render_chart(self, df) -> None:
        self._ax.clear()
        if not df.empty:
            daily = df.set_index("fecha").resample("D")["total"].sum()
            self._ax.plot(
                daily.index, daily.values,
                color=THEME["accent"], linewidth=2,
                marker="o", markersize=5,
                markerfacecolor=THEME["accent2"],
            )
            self._ax.fill_between(
                daily.index, daily.values,
                alpha=0.15, color=THEME["accent"],
            )
            self._ax.set_title(
                "Ingresos Diarios", color=THEME["text"], fontsize=11
            )
            self._ax.tick_params(colors=THEME["text_dim"], labelsize=8)
            self._ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
            )
            self._ax.set_facecolor(THEME["surface"])
            for sp in self._ax.spines.values():
                sp.set_edgecolor(THEME["border"])
            self._ax.grid(
                color=THEME["border"], linestyle="--", alpha=0.3
            )
        self._fig.tight_layout(pad=1.5)
        self._canvas.draw()

    def _render_text(self, df, kpis, fecha_ini, fecha_fin) -> None:
        if df.empty:
            texto = "📭  No hay ventas en el rango seleccionado."
        else:
            df_inv = self._inv.get_df()
            if not df_inv.empty:
                df = df.merge(
                    df_inv[["id_pieza", "nombre"]], on="id_pieza", how="left"
                )
                df["nombre"] = df["nombre"].fillna(df["id_pieza"])
            else:
                df["nombre"] = df["id_pieza"]

            agr = (
                df.groupby("nombre")
                .agg(
                    unidades=("cantidad", "sum"),
                    ingresos=("total",    "sum"),
                    trans=   ("id_venta", "count"),
                )
                .sort_values("ingresos", ascending=False)
            )

            sep   = "─" * 58
            rango = f"{fecha_ini or 'Inicio'}  →  {fecha_fin or 'Hoy'}"
            texto = f"📊  REPORTE DE VENTAS   |   {rango}\n{sep}\n"
            texto += f"{'Pieza':<24} {'Unidades':>9} {'Ingresos':>14} {'Trans.':>8}\n{sep}\n"

            for nombre, fila in agr.iterrows():
                texto += (
                    f"{str(nombre):<24}"
                    f" {int(fila['unidades']):>9}"
                    f" ${fila['ingresos']:>13,.2f}"
                    f" {int(fila['trans']):>8}\n"
                )

            texto += sep + "\n"
            texto += f"{'💵 Total Ingresos:':<26} ${kpis['total']:>22,.2f}\n"
            texto += f"{'🛒 Transacciones:':<26} {kpis['transacciones']:>24}\n"
            texto += f"{'📦 Unidades Vendidas:':<26} {kpis['unidades']:>24}\n"
            texto += f"{'🧾 Ticket Promedio:':<26} ${kpis['ticket_promedio']:>22,.2f}\n"

        self._txt.config(state=tk.NORMAL)
        self._txt.delete(1.0, tk.END)
        self._txt.insert(tk.END, texto)
        self._txt.config(state=tk.DISABLED)
