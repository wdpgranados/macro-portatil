"""
ui/inventario.py — Tab: Gestión de Inventario.
Incluye editar, eliminar (soft delete) y alertas de stock mínimo.
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from config import THEME, MONEDA
from services import InventarioService

if TYPE_CHECKING:
    from ui.app import TallerApp


class InventarioTab:

    def __init__(
        self,
        parent: ttk.Notebook,
        inv_svc: InventarioService,
        app: "TallerApp",
    ) -> None:
        self._inv = inv_svc
        self._app = app
        self._modo_edicion = False
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self) -> None:
        self._build_form()
        self._build_search_bar()
        self._build_tree()
        self._build_footer()
        self.frame.bind("<F2>", lambda e: self._guardar())

    # ── Formulario ───────────────────────────────────────────────
    def _build_form(self) -> None:
        frm = ttk.LabelFrame(
            self.frame,
            text="  Agregar / Actualizar Pieza  ",
            padding=12,
        )
        frm.pack(fill=tk.X, padx=16, pady=(12, 6))

        campos = [
            "ID Pieza",
            "Nombre",
            "Categoría",
            "Cantidad",
            "Precio Unit.",
            "Stock Mín.",
        ]
        self._ent: dict[str, ttk.Entry] = {}

        for i, lbl in enumerate(campos):
            col = (i % 3) * 2
            row = i // 3
            ttk.Label(frm, text=lbl + ":").grid(
                row=row,
                column=col,
                padx=(12, 4),
                pady=6,
                sticky=tk.E,
            )
            ent = ttk.Entry(frm, width=16)
            ent.grid(
                row=row,
                column=col + 1,
                padx=(0, 12),
                pady=6,
                sticky=tk.W,
            )
            self._ent[lbl] = ent

        # Indicador de modo
        self._lbl_modo = tk.Label(
            frm,
            text="",
            bg=THEME["surface"],
            fg=THEME["warning"],
            font=("Segoe UI", 9),
        )
        self._lbl_modo.grid(row=2, column=0, columnspan=4, pady=2)

        # Botones
        ttk.Button(
            frm,
            text="💾  Guardar  [F2]",
            command=self._guardar,
        ).grid(row=2, column=4, padx=6, pady=6)

        ttk.Button(
            frm,
            text="✏️  Editar seleccionado",
            command=self._cargar_para_editar,
        ).grid(row=2, column=5, padx=6, pady=6)

        ttk.Button(
            frm,
            text="🗑️  Eliminar",
            command=self._eliminar,
        ).grid(row=2, column=6, padx=6, pady=6)

        ttk.Button(
            frm,
            text="🧹  Limpiar",
            command=self._limpiar_campos,
        ).grid(row=2, column=7, padx=6, pady=6)

    # ── Barra de búsqueda ────────────────────────────────────────
    def _build_search_bar(self) -> None:
        bar = tk.Frame(self.frame, bg=THEME["bg"])
        bar.pack(fill=tk.X, padx=16, pady=4)

        ttk.Label(bar, text="🔍 Buscar:").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ttk.Entry(bar, textvariable=self._search_var, width=30).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(
            bar,
            text="Busca por ID, nombre o categoría",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

        ttk.Button(
            bar,
            text="⚠️ Ver stock crítico",
            command=self._mostrar_stock_critico,
        ).pack(side=tk.LEFT, padx=12)

        ttk.Button(
            bar,
            text="📋 Ver todos",
            command=self.refresh,
        ).pack(side=tk.LEFT, padx=4)

        self._lbl_critico = tk.Label(
            bar, text="",
            bg=THEME["bg"], fg=THEME["danger"],
            font=("Segoe UI Semibold", 9),
        )
        self._lbl_critico.pack(side=tk.RIGHT, padx=12)        

        # Indicador stock crítico
        self._lbl_critico = tk.Label(
            bar,
            text="",
            bg=THEME["bg"],
            fg=THEME["danger"],
            font=("Segoe UI Semibold", 9),
        )
        self._lbl_critico.pack(side=tk.RIGHT, padx=12)


    def _mostrar_stock_critico(self) -> None:
        """Filtra y muestra solo las piezas con stock crítico."""
        piezas = self._inv.get_stock_critico()
        self._populate_tree(piezas)
        if piezas:
            self._app.set_status(f"⚠️ Mostrando {len(piezas)} pieza(s) con stock crítico")
        else:
            self._app.set_status("✅ No hay piezas con stock crítico")
            messagebox.showinfo("Stock OK", "Todas las piezas tienen stock suficiente.")

    # ── Treeview ─────────────────────────────────────────────────
    def _build_tree(self) -> None:
        cols = ("id", "nombre", "cat", "cant", "precio", "stock_min", "valor")
        self._tree = ttk.Treeview(
            self.frame,
            columns=cols,
            show="headings",
            height=14,
        )
        headers = [
            ("id", "ID", 90),
            ("nombre", "Nombre", 200),
            ("cat", "Categoría", 120),
            ("cant", "Stock", 80),
            ("precio", "Precio Unit.", 110),
            ("stock_min", "Stock Mín.", 90),
            ("valor", "Valor Stock", 110),
        ]
        for col, title, width in headers:
            self._tree.heading(col, text=title)
            self._tree.column(col, width=width, anchor=tk.CENTER)

        # Doble clic carga para editar
        self._tree.bind("<Double-1>", lambda e: self._cargar_para_editar())

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
        scr.pack(side=tk.LEFT, fill=tk.Y, pady=4, padx=(0, 16))

    def _build_footer(self) -> None:
        self._lbl_valor = ttk.Label(
            self.frame,
            text="💵 Valor total: S/0.00",
            font=("Segoe UI Semibold", 11),
        )
        self._lbl_valor.pack(pady=6)

    # ── Acciones ─────────────────────────────────────────────────
    def _guardar(self) -> None:
        try:
            data = {k: v.get().strip() for k, v in self._ent.items()}
            if not data["ID Pieza"] or not data["Nombre"]:
                raise ValueError("ID y Nombre son obligatorios.")

            stock_min = int(data.get("Stock Mín.", 5) or 5)

            if self._modo_edicion:
                pieza = self._inv.actualizar_pieza(
                    id_pieza=data["ID Pieza"],
                    nombre=data["Nombre"],
                    categoria=data["Categoría"],
                    cantidad=int(data["Cantidad"]),
                    precio=float(data["Precio Unit."]),
                    stock_minimo=stock_min,
                )
                self._app.set_status(
                    f"✅ Pieza '{pieza.nombre}' actualizada correctamente."
                )
            else:
                pieza = self._inv.guardar_pieza(
                    id_pieza=data["ID Pieza"],
                    nombre=data["Nombre"],
                    categoria=data["Categoría"],
                    cantidad=int(data["Cantidad"]),
                    precio=float(data["Precio Unit."]),
                    stock_minimo=stock_min,
                )
                self._app.set_status(
                    f"✅ Pieza '{pieza.nombre}' guardada correctamente."
                )

            self._limpiar_campos()
            self._app.refresh()

        except (ValueError, sqlite3.Error) as ex:
            messagebox.showerror("Error al guardar", str(ex))

    def _cargar_para_editar(self) -> None:
        """Carga la pieza seleccionada en el formulario para editar."""
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una pieza de la tabla.")
            return
        valores = self._tree.item(sel[0])["values"]
        campos = [
            "ID Pieza",
            "Nombre",
            "Categoría",
            "Cantidad",
            "Precio Unit.",
            "Stock Mín.",
        ]
        datos = [
            str(valores[0]),  # ID
            str(valores[1]),  # Nombre
            str(valores[2]),  # Categoría
            str(valores[3]),  # Cantidad
            str(valores[4]).replace(f"{MONEDA}", "").replace(",", ""),
            str(valores[5]),  # Stock Mín
        ]
        for campo, dato in zip(campos, datos):
            self._ent[campo].delete(0, tk.END)
            self._ent[campo].insert(0, dato)

        self._modo_edicion = True
        self._lbl_modo.config(
            text=f"✏️ MODO EDICIÓN — '{valores[1]}' — modifica y presiona Guardar"
        )
        self._app.set_status(f"✏️ Editando pieza '{valores[1]}'")

    def _eliminar(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una pieza de la tabla.")
            return
        valores = self._tree.item(sel[0])["values"]
        id_pieza = str(valores[0])
        nombre = str(valores[1])

        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la pieza '{nombre}'?\n\n"
            f"No aparecerá más en el inventario pero\n"
            f"se conserva en el historial de ventas.",
        ):
            self._inv.eliminar_pieza(id_pieza)
            self._app.refresh()
            self._app.set_status(f"🗑️ Pieza '{nombre}' eliminada del inventario.")

    def _limpiar_campos(self) -> None:
        for e in self._ent.values():
            e.delete(0, tk.END)
        self._modo_edicion = False
        self._lbl_modo.config(text="")

    def _on_search(self) -> None:
        query = self._search_var.get().strip()
        piezas = self._inv.buscar(query) if query else self._inv.listar()
        self._populate_tree(piezas)

    # ── Render ───────────────────────────────────────────────────
    def _populate_tree(self, piezas) -> None:
        self._tree.delete(*self._tree.get_children())
        for p in piezas:
            tag = "critico" if p.stock_critico else ""
            self._tree.insert(
                "",
                tk.END,
                tags=(tag,),
                values=(
                    p.id_pieza,
                    p.nombre,
                    p.categoria,
                    p.cantidad,
                    f"{MONEDA}{p.precio_unitario:,.2f}",
                    p.stock_minimo,
                    f"{MONEDA}{p.valor_stock:,.2f}",
                ),
            )
        self._tree.tag_configure("critico", foreground=THEME["danger"])

    def refresh(self) -> None:
        piezas = self._inv.listar()
        self._populate_tree(piezas)
        valor = self._inv.valor_total_inventario()
        self._lbl_valor.config(text=f"💵 Valor total inventario: {MONEDA}{valor:,.2f}")

        # Alerta de stock crítico
        criticos = self._inv.get_stock_critico()
        if criticos:
            self._lbl_critico.config(
                text=f"⚠️ {len(criticos)} pieza(s) con stock crítico"
            )
        else:
            self._lbl_critico.config(text="✅ Stock en niveles normales")
