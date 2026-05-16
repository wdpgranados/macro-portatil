"""
ui/ventas.py — Tab: Registro de Salidas de Inventario.

Permite registrar una venta ingresando ID de pieza y cantidad.
Muestra el historial de ventas recientes con nombre de pieza resuelto.
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from config import THEME, MAX_VENTAS_HISTORIAL, MONEDA
from services import VentasService, InventarioService

if TYPE_CHECKING:
    from ui.app import TallerApp


class VentasTab:
    """Tab de ventas: formulario de salida + historial."""

    def __init__(
        self,
        parent: ttk.Notebook,
        ven_svc: VentasService,
        inv_svc: InventarioService,
        app: "TallerApp",
    ) -> None:

        self._ven = ven_svc
        self._inv = inv_svc
        self._app = app

        self.frame = ttk.Frame(parent)

        self._build()

    # ─────────────────────────────────────────────
    # Construcción UI
    # ─────────────────────────────────────────────

    def _build(self) -> None:
        self._build_form()
        self._build_search_bar()
        self._build_tree()
        self.frame.bind("<F2>", lambda event: self._registrar())#para guardar con f2 las ventas

    def _build_search_bar(self) -> None:

        bar = tk.Frame(self.frame, bg=THEME["bg"])
        bar.pack(fill=tk.X, padx=16, pady=4)

        ttk.Label(bar, text="🔍 Buscar:").pack(side=tk.LEFT)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())

        ttk.Entry(
            bar,
            textvariable=self._search_var,
            width=30,
        ).pack(side=tk.LEFT, padx=8)

        ttk.Label(
            bar,
            text="Busca por ID o nombre",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

    def _build_form(self) -> None:

        frm = ttk.LabelFrame(
            self.frame,
            text="  Registrar Salida de Inventario  ",
            padding=12,
        )

        frm.pack(fill=tk.X, padx=16, pady=12)

        ttk.Label(frm, text="ID Pieza:").grid(
            row=0,
            column=0,
            padx=8,
            pady=6,
            sticky=tk.E,
        )

        self._ent_id = ttk.Entry(frm, width=18)
        self._ent_id.grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(frm, text="Cantidad:").grid(
            row=0,
            column=2,
            padx=8,
            pady=6,
            sticky=tk.E,
        )

        self._ent_cant = ttk.Entry(frm, width=10)
        self._ent_cant.grid(row=0, column=3, padx=8, pady=6)

        ttk.Button(
            frm,
            text="🛒 Registrar Venta [F2]",
            command=self._registrar,
        ).grid(row=0, column=4, padx=12)

    def _build_tree(self) -> None:

        cols = ("idv", "pieza", "cant", "total", "fecha")

        self._tree = ttk.Treeview(
            self.frame,
            columns=cols,
            show="headings",
            height=16,
        )

        columnas = [
            ("idv", "Venta #", 120),
            ("pieza", "Pieza", 180),
            ("cant", "Cant.", 70),
            ("total", f"Total {MONEDA}", 110),
            ("fecha", "Fecha", 150),
        ]

        for col, title, width in columnas:
            self._tree.heading(col, text=title)
            self._tree.column(
                col,
                width=width,
                anchor=tk.CENTER,
            )

        scr = ttk.Scrollbar(
            self.frame,
            orient=tk.VERTICAL,
            command=self._tree.yview,
        )

        self._tree.configure(yscrollcommand=scr.set)

        self._tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(16, 0),
            pady=4,
        )

        scr.pack(
            side=tk.LEFT,
            fill=tk.Y,
            pady=4,
            padx=(0, 16),
        )

    # ─────────────────────────────────────────────
    # Búsqueda
    # ─────────────────────────────────────────────

    def _on_search(self) -> None:

        query = self._search_var.get().strip().lower()

        df = self._ven.get_df()

        if df.empty:
            return

        df_inv = self._inv.get_df()

        # Resolver nombres de piezas
        if not df_inv.empty:

            df = df.merge(
                df_inv[["id_pieza", "nombre"]],
                on="id_pieza",
                how="left",
            )

            df["nombre"] = df["nombre"].fillna(df["id_pieza"])

        else:
            df["nombre"] = df["id_pieza"]

        # Filtro
        if query:

            df = df[
                df["nombre"].str.contains(query, case=False, na=False)
                | df["id_pieza"].str.contains(query, case=False, na=False)
            ]

        self._load_tree(df)

    # ─────────────────────────────────────────────
    # Acciones
    # ─────────────────────────────────────────────

    def _registrar(self) -> None:

        try:

            id_pieza = self._ent_id.get().strip()
            cantidad = int(self._ent_cant.get())

            venta = self._ven.registrar_venta(
                id_pieza,
                cantidad,
            )

            self._ent_id.delete(0, tk.END)
            self._ent_cant.delete(0, tk.END)

            self._app.refresh()

            self._app.set_status(
                f"💰 Venta {venta.id_venta} registrada – "
                f"Total: {MONEDA}{venta.total:,.2f}"
            )

        except (ValueError, sqlite3.Error) as ex:

            messagebox.showerror(
                "Error al registrar venta",
                str(ex),
            )

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _load_tree(self, df) -> None:

        self._tree.delete(*self._tree.get_children())

        for _, row in df.head(MAX_VENTAS_HISTORIAL).iterrows():

            self._tree.insert(
                "",
                tk.END,
                values=(
                    row["id_venta"],
                    row["nombre"],
                    row["cantidad"],
                    f"{MONEDA}{row['total']:,.2f}",
                    row["fecha"].strftime("%Y-%m-%d %H:%M"),
                ),
            )

    # ─────────────────────────────────────────────
    # Refresh
    # ─────────────────────────────────────────────

    def refresh(self) -> None:

        df = self._ven.get_df()

        if df.empty:
            self._tree.delete(*self._tree.get_children())
            return

        df_inv = self._inv.get_df()

        if not df_inv.empty:

            df = df.merge(
                df_inv[["id_pieza", "nombre"]],
                on="id_pieza",
                how="left",
            )

            df["nombre"] = df["nombre"].fillna(df["id_pieza"])

        else:
            df["nombre"] = df["id_pieza"]

        self._load_tree(df)
