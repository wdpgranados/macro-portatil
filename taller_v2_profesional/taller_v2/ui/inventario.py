"""
ui/inventario.py — Tab: Gestión de Inventario.

Permite agregar/actualizar piezas y ver el stock con búsqueda en tiempo real.
La búsqueda delega el filtrado a la capa de repositorio (SQL LIKE),
no carga todos los registros y los filtra en Python.
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from config import THEME, STOCK_BAJO_UMBRAL
from services import InventarioService

from config import THEME, STOCK_BAJO_UMBRAL, MONEDA  # ← agrega MONEDA aquí

if TYPE_CHECKING:
    from ui.app import TallerApp


class InventarioTab:
    """Tab de inventario: CRUD de piezas + búsqueda + valor total."""

    def __init__(
        self,
        parent: ttk.Notebook,
        inv_svc: InventarioService,
        app: "TallerApp",
    ) -> None:
        self._inv = inv_svc
        self._app = app
        self.frame = ttk.Frame(parent)
        self._build()

    # ── Construcción ─────────────────────────────────────────────
    def _build(self) -> None:
        self._build_form()
        self._build_search_bar()
        self._build_tree()
        self._build_footer()
        # ← se esta agregando f2 para poder grabar mas rapido los nuevos datos ingresados
        self.frame.bind("<F2>", lambda event: self._guardar())

    def _build_form(self) -> None:
        frm = ttk.LabelFrame(
            self.frame, text="  Agregar / Actualizar Pieza  ", padding=12
        )
        frm.pack(fill=tk.X, padx=16, pady=(12, 6))

        campos = ["ID Pieza", "Nombre", "Categoría", "Cantidad", "Precio Unit."]
        self._ent: dict[str, ttk.Entry] = {}

        for i, lbl in enumerate(campos):
            col = (i % 3) * 2
            row = i // 3
            ttk.Label(frm, text=lbl + ":").grid(
                row=row, column=col, padx=(12, 4), pady=6, sticky=tk.E
            )
            ent = ttk.Entry(frm, width=18)
            ent.grid(row=row, column=col + 1, padx=(0, 12), pady=6, sticky=tk.W)
            self._ent[lbl] = ent

        ttk.Button(
            frm, text="💾  Guardar [F2]", command=self._guardar
        ).grid(row=1, column=5, padx=12, pady=6)

    def _build_search_bar(self) -> None:
        bar = tk.Frame(self.frame, bg=THEME["bg"])
        bar.pack(fill=tk.X, padx=16, pady=4)

        ttk.Label(bar, text="🔍 Buscar:").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        # trace dispara _on_search en cada cambio del campo
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ttk.Entry(bar, textvariable=self._search_var, width=30).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(
            bar,
            text="Busca por ID, nombre o categoría",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

    def _build_tree(self) -> None:
        cols = ("id", "nombre", "cat", "cant", "precio", "valor")
        self._tree = ttk.Treeview(
            self.frame, columns=cols, show="headings", height=14
        )
        headers = [
            ("id",     "ID",          90),
            ("nombre", "Nombre",      200),
            ("cat",    "Categoría",   120),
            ("cant",   "Stock",        80),
            ("precio", "Precio Unit.", 110),
            ("valor",  "Valor Stock",  110),
        ]
        for col, title, width in headers:
            self._tree.heading(col, text=title)
            self._tree.column(col, width=width, anchor=tk.CENTER)

        scr = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self._tree.yview
        )
        self._tree.configure(yscrollcommand=scr.set)
        self._tree.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0), pady=4
        )
        scr.pack(side=tk.LEFT, fill=tk.Y, pady=4, padx=(0, 16))

    def _build_footer(self) -> None:
        self._lbl_valor = ttk.Label(
            self.frame,
            text="💵 Valor total: $0.00",
            font=("Segoe UI Semibold", 11),
        )
        self._lbl_valor.pack(pady=6)

    # ── Acciones ─────────────────────────────────────────────────
    def _guardar(self) -> None:
        try:
            data = {k: v.get().strip() for k, v in self._ent.items()}
            if not data["ID Pieza"] or not data["Nombre"]:
                raise ValueError("ID y Nombre son obligatorios.")
            pieza = self._inv.guardar_pieza(
                id_pieza  = data["ID Pieza"],
                nombre    = data["Nombre"],
                categoria = data["Categoría"],
                cantidad  = int(data["Cantidad"]),
                precio    = float(data["Precio Unit."]),
            )
            for e in self._ent.values():
                e.delete(0, tk.END)
            self._app.refresh()
            self._app.set_status(f"✅ Pieza '{pieza.nombre}' guardada correctamente.")
        except (ValueError, sqlite3.Error) as ex:
            messagebox.showerror("Error al guardar", str(ex))

    def _on_search(self) -> None:
        """
        Dispara la búsqueda delegando el filtrado a SQL (no filtra en Python).
        Si el campo está vacío, carga todas las piezas.
        """
        query = self._search_var.get().strip()
        piezas = self._inv.buscar(query) if query else self._inv.listar()
        self._populate_tree(piezas)

    # ── Render del Treeview ───────────────────────────────────────
    def _populate_tree(self, piezas) -> None:
        self._tree.delete(*self._tree.get_children())
        for p in piezas:
            tag = "low" if p.cantidad < STOCK_BAJO_UMBRAL else ""
            self._tree.insert(
                "", tk.END, tags=(tag,),
                values=(
                    p.id_pieza, p.nombre, p.categoria,
                    p.cantidad,
                    f"{MONEDA}{p.precio_unitario:,.2f}",
                    f"{MONEDA}{p.valor_stock:,.2f}",
                ),
            )
        self._tree.tag_configure("low", foreground=THEME["danger"])

    def refresh(self) -> None:
        """Recarga la tabla completa y actualiza el valor total."""
        piezas = self._inv.listar()
        self._populate_tree(piezas)
        valor = self._inv.valor_total_inventario()
        self._lbl_valor.config(text=f"💵 Valor total inventario: {MONEDA}{valor:,.2f}")
