"""
ui/clientes.py — Tab: Gestión de Clientes.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME, DB_PATH
from domain.cliente import Cliente
from repositories.clientes_repo import SQLiteClientesRepo


class ClientesTab:

    def __init__(self, parent: ttk.Notebook) -> None:
        self._repo = SQLiteClientesRepo(DB_PATH)
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self) -> None:
        self._build_form()
        self._build_search_bar()
        self._build_tree()
        self.frame.bind("<F3>", lambda e: self._guardar())

    # ── Formulario ───────────────────────────────────────────────
    def _build_form(self) -> None:
        frm = ttk.LabelFrame(
            self.frame,
            text="  Agregar / Actualizar Cliente  ",
            padding=12,
        )
        frm.pack(fill=tk.X, padx=16, pady=(12, 6))

        campos = [
            ("ID Cliente", 0, 0),
            ("Nombre", 0, 2),
            ("Teléfono", 1, 0),
            ("Dirección", 1, 2),
        ]
        self._ent: dict[str, ttk.Entry] = {}

        for lbl, row, col in campos:
            ttk.Label(frm, text=lbl + ":").grid(
                row=row,
                column=col,
                padx=(12, 4),
                pady=6,
                sticky=tk.E,
            )
            ent = ttk.Entry(frm, width=22)
            ent.grid(
                row=row,
                column=col + 1,
                padx=(0, 12),
                pady=6,
                sticky=tk.W,
            )
            self._ent[lbl] = ent

        ttk.Button(
            frm,
            text="💾  Guardar Cliente  [F3]",
            command=self._guardar,
        ).grid(row=2, column=0, columnspan=2, padx=12, pady=8, sticky=tk.W)

        ttk.Button(
            frm,
            text="🗑️  Eliminar seleccionado",
            command=self._eliminar,
        ).grid(row=2, column=2, columnspan=2, padx=12, pady=8, sticky=tk.W)

        ttk.Button(
            frm,
            text="🧹  Limpiar campos",
            command=self._limpiar_campos,
        ).grid(row=2, column=4, padx=12, pady=8, sticky=tk.W)

    # ── Buscador ─────────────────────────────────────────────────
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
            text="Busca por ID, nombre o teléfono",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

    # ── Tabla ────────────────────────────────────────────────────
    def _build_tree(self) -> None:
        cols = ("id", "nombre", "telefono", "direccion")
        self._tree = ttk.Treeview(
            self.frame,
            columns=cols,
            show="headings",
            height=18,
        )
        for col, title, width in [
            ("id", "ID Cliente", 120),
            ("nombre", "Nombre", 220),
            ("telefono", "Teléfono", 130),
            ("direccion", "Dirección", 300),
        ]:
            self._tree.heading(col, text=title)
            self._tree.column(col, width=width, anchor=tk.CENTER)

        # Doble clic carga el cliente en el formulario
        self._tree.bind("<Double-1>", self._cargar_seleccion)

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

    # ── Acciones ─────────────────────────────────────────────────
    def _guardar(self) -> None:
        try:
            data = {k: v.get().strip() for k, v in self._ent.items()}
            if not data["ID Cliente"]:
                raise ValueError("El ID de cliente es obligatorio.")
            if not data["Nombre"]:
                raise ValueError("El nombre es obligatorio.")

            cliente = Cliente(
                id_cliente=data["ID Cliente"].upper(),
                nombre=data["Nombre"],
                telefono=data["Teléfono"],
                direccion=data["Dirección"],
            )
            self._repo.upsert(cliente)
            self._limpiar_campos()
            self.refresh()
            messagebox.showinfo(
                "OK", f"Cliente '{cliente.nombre}' guardado correctamente."
            )
        except ValueError as ex:
            messagebox.showerror("Error al guardar", str(ex))

    def _eliminar(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un cliente de la tabla.")
            return
        id_cliente = self._tree.item(sel[0])["values"][0]
        nombre = self._tree.item(sel[0])["values"][1]
        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar el cliente '{nombre}'?\nEsta acción no se puede deshacer.",
        ):
            self._repo.eliminar(id_cliente)
            self.refresh()

    def _cargar_seleccion(self, event=None) -> None:
        """Doble clic → carga los datos en el formulario para editar."""
        sel = self._tree.selection()
        if not sel:
            return
        valores = self._tree.item(sel[0])["values"]
        campos = ["ID Cliente", "Nombre", "Teléfono", "Dirección"]
        for campo, valor in zip(campos, valores):
            self._ent[campo].delete(0, tk.END)
            self._ent[campo].insert(0, str(valor))

    def _limpiar_campos(self) -> None:
        for e in self._ent.values():
            e.delete(0, tk.END)

    def _on_search(self) -> None:
        query = self._search_var.get().strip()
        clientes = self._repo.buscar(query) if query else self._repo.get_all()
        self._poblar_tree(clientes)

    # ── Render ───────────────────────────────────────────────────
    def _poblar_tree(self, clientes) -> None:
        self._tree.delete(*self._tree.get_children())
        for c in clientes:
            self._tree.insert(
                "",
                tk.END,
                values=(
                    c.id_cliente,
                    c.nombre,
                    c.telefono,
                    c.direccion,
                ),
            )

    def refresh(self) -> None:
        self._poblar_tree(self._repo.get_all())
