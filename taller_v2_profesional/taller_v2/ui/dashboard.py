"""
ui/dashboard.py — Tab: Dashboard principal.

Muestra KPI cards con métricas clave y dos gráficos:
- Barras horizontales: top 8 piezas por stock.
- Pie chart: distribución de ingresos por pieza (top 6).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from config import THEME, MONEDA

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import THEME
from services import InventarioService, VentasService


# ══════════════════════════════════════════════════════════════════
#  WIDGET: KPI Card
# ══════════════════════════════════════════════════════════════════
class KpiCard(tk.Frame):
    """
    Tarjeta visual para un KPI individual.

    Muestra: icono (emoji) + valor grande + etiqueta descriptiva.
    El valor es actualizable sin reconstruir el widget.
    """

    def __init__(
        self,
        parent: tk.Widget,
        icon: str,
        label: str,
        value: str = "–",
        color: str = THEME["accent"],
        **kw,
    ) -> None:
        super().__init__(
            parent,
            bg=THEME["surface2"],
            relief="flat",
            padx=16, pady=12,
            **kw,
        )
        tk.Label(
            self, text=icon,
            bg=THEME["surface2"], fg=color,
            font=("Segoe UI Emoji", 22),
        ).pack()

        self._val_lbl = tk.Label(
            self, text=value,
            bg=THEME["surface2"], fg=THEME["text"],
            font=("Segoe UI Semibold", 18),
        )
        self._val_lbl.pack()

        tk.Label(
            self, text=label,
            bg=THEME["surface2"], fg=THEME["text_dim"],
            font=("Segoe UI", 9),
        ).pack()

    def update_value(self, value: str) -> None:
        self._val_lbl.config(text=value)


# ══════════════════════════════════════════════════════════════════
#  TAB: Dashboard
# ══════════════════════════════════════════════════════════════════
class DashboardTab:
    """Tab del Dashboard: KPIs + gráficos de inventario y ventas."""

    def __init__(
        self,
        parent: ttk.Notebook,
        inv_svc: InventarioService,
        ven_svc: VentasService,
    ) -> None:
        self._inv = inv_svc
        self._ven = ven_svc
        self.frame = ttk.Frame(parent)
        self._build()

    # ── Construcción ─────────────────────────────────────────────
    def _build(self) -> None:
        self._build_kpi_row()
        self._build_charts()

    def _build_kpi_row(self) -> None:
        row = tk.Frame(self.frame, bg=THEME["bg"])
        row.pack(fill=tk.X, padx=16, pady=(16, 8))

        self._kpi_valor    = KpiCard(row, "💵", "Valor Inventario", color=THEME["success"])
        self._kpi_sku      = KpiCard(row, "📦", "SKUs en Stock",    color=THEME["accent"])
        self._kpi_ingresos = KpiCard(row, "📈", "Ingresos Totales", color=THEME["accent2"])
        self._kpi_ventas   = KpiCard(row, "🛒", "Transacciones",    color=THEME["warning"])
        self._kpi_ticket   = KpiCard(row, "🧾", "Ticket Promedio",  color=THEME["danger"])

        for card in (
            self._kpi_valor, self._kpi_sku, self._kpi_ingresos,
            self._kpi_ventas, self._kpi_ticket,
        ):
            card.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6, pady=2)

    def _build_charts(self) -> None:
        charts_row = tk.Frame(self.frame, bg=THEME["bg"])
        charts_row.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        self._fig, (self._ax_bar, self._ax_pie) = plt.subplots(
            1, 2, figsize=(11, 4), facecolor=THEME["bg"]
        )
        for ax in (self._ax_bar, self._ax_pie):
            ax.set_facecolor(THEME["surface"])
            for sp in ax.spines.values():
                sp.set_edgecolor(THEME["border"])

        canvas = FigureCanvasTkAgg(self._fig, master=charts_row)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.get_tk_widget().configure(bg=THEME["bg"])
        self._canvas = canvas

    # ── Refresh ──────────────────────────────────────────────────
    def refresh(self) -> None:
        """Recarga KPIs y gráficos con datos actuales."""
        df_inv = self._inv.get_df()
        df_ven = self._ven.get_df()
        kpis   = self._ven.kpis(df_ven)

        # KPI Cards
        self._kpi_valor.update_value(f"{MONEDA}{self._inv.valor_total_inventario():,.0f}")
        self._kpi_sku.update_value(str(len(df_inv)))
        self._kpi_ingresos.update_value(f"{MONEDA}{kpis['total']:,.0f}")
        self._kpi_ventas.update_value(str(kpis['transacciones']))
        self._kpi_ticket.update_value(f"{MONEDA}{kpis['ticket_promedio']:,.2f}")

        self._ax_bar.clear()
        self._ax_pie.clear()

        # Gráfico de barras: top 8 piezas por stock
        if not df_inv.empty:
            top = df_inv.nlargest(8, "cantidad")
            bars = self._ax_bar.barh(
                top["nombre"], top["cantidad"],
                color=THEME["accent"], alpha=0.85, height=0.6,
            )
            max_cant = top["cantidad"].max()
            for bar in bars:
                w = bar.get_width()
                self._ax_bar.text(
                    w + max_cant * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    str(int(w)), va="center", ha="left",
                    color=THEME["text"], fontsize=8,
                )
            self._ax_bar.set_title(
                "Top Stock por Pieza", color=THEME["text"], fontsize=11, pad=10
            )
            self._ax_bar.tick_params(colors=THEME["text_dim"], labelsize=8)
            self._ax_bar.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{int(x)}")
            )
            self._ax_bar.set_facecolor(THEME["surface"])
            for sp in self._ax_bar.spines.values():
                sp.set_edgecolor(THEME["border"])
            self._ax_bar.grid(axis="x", color=THEME["border"], linestyle="--", alpha=0.4)

        # Pie chart: ingresos por pieza (top 6)
        if not df_ven.empty and not df_inv.empty:
            merged = df_ven.merge(df_inv[["id_pieza", "nombre"]], on="id_pieza", how="left")
            ing = merged.groupby("nombre")["total"].sum().nlargest(6)
            colors = ["#4f8ef7", "#7c4dff", "#22c55e", "#f59e0b", "#ef4444", "#06b6d4"]
            _, _, autotexts = self._ax_pie.pie(
                ing.values, labels=ing.index,
                colors=colors[:len(ing)],
                autopct="%1.1f%%", startangle=140,
                textprops={"color": THEME["text"], "fontsize": 8},
                wedgeprops={"linewidth": 1.5, "edgecolor": THEME["bg"]},
            )
            for at in autotexts:
                at.set_color(THEME["bg"])
                at.set_fontsize(8)
            self._ax_pie.set_title(
                "Ingresos por Pieza", color=THEME["text"], fontsize=11, pad=10
            )

        self._fig.tight_layout(pad=2)
        self._canvas.draw()
