"""
ui/ventas.py — Tab: Registro de Salidas con Carrito de Compras.
"""

from __future__ import annotations

import sqlite3
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional

from config import THEME, MONEDA, DB_PATH
from domain.item_carrito import ItemCarrito
from services import VentasService, InventarioService
from services.comprobante_service import ComprobanteService
from repositories.clientes_repo import SQLiteClientesRepo

if TYPE_CHECKING:
    from ui.app import TallerApp


class VentasTab:

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
        self._carrito: list[ItemCarrito] = []
        self._comprobante_svc = ComprobanteService()
        self._cli_repo = SQLiteClientesRepo(DB_PATH)
        self._clientes_lista = []
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self) -> None:
        self._build_panel_izquierdo()
        self._build_panel_derecho()

    # ══════════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO — Stock
    # ══════════════════════════════════════════════════════════════
    def _build_panel_izquierdo(self) -> None:
        self._panel_izq = ttk.LabelFrame(
            self.frame,
            text="  📦 Stock Disponible — Doble clic para agregar  ",
            padding=8,
        )
        self._panel_izq.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(16, 4),
            pady=12,
        )

        bar = tk.Frame(self._panel_izq, bg=THEME["bg"])
        bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(bar, text="🔍 Buscar:").pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ttk.Entry(bar, textvariable=self._search_var, width=24).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(
            bar,
            text="Por ID, nombre o categoría",
            foreground=THEME["text_dim"],
        ).pack(side=tk.LEFT)

        cols = ("id", "nombre", "cat", "stock", "precio")
        self._tree_stock = ttk.Treeview(
            self._panel_izq,
            columns=cols,
            show="headings",
            height=20,
        )
        for col, title, width in [
            ("id", "ID Pieza", 110),
            ("nombre", "Nombre", 200),
            ("cat", "Categoría", 130),
            ("stock", "Stock", 70),
            ("precio", "Precio", 100),
        ]:
            self._tree_stock.heading(col, text=title)
            self._tree_stock.column(col, width=width, anchor=tk.CENTER)

        self._tree_stock.bind("<Double-1>", self._seleccionar_pieza)

        scr = ttk.Scrollbar(
            self._panel_izq,
            orient=tk.VERTICAL,
            command=self._tree_stock.yview,
        )
        self._tree_stock.configure(yscrollcommand=scr.set)
        self._tree_stock.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr.pack(side=tk.LEFT, fill=tk.Y)

    # ══════════════════════════════════════════════════════════════
    #  PANEL DERECHO
    # ══════════════════════════════════════════════════════════════
    def _build_panel_derecho(self) -> None:
        self._panel_der = tk.Frame(self.frame, bg=THEME["bg"], width=380)
        self._panel_der.pack(side=tk.LEFT, fill=tk.BOTH, padx=(4, 16), pady=12)
        self._panel_der.pack_propagate(False)

        # ── Botón confirmar anclado al fondo ──────────────────────
        frm_bottom = tk.Frame(self._panel_der, bg=THEME["bg"])
        frm_bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))

        ttk.Button(
            frm_bottom,
            text="✅  Confirmar Venta",
            command=self._confirmar_venta,
        ).pack(fill=tk.X, padx=4, pady=4)

        # ── Contenido superior ────────────────────────────────────
        frm_top = tk.Frame(self._panel_der, bg=THEME["bg"])
        frm_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 1. Cliente
        frm_cli = ttk.LabelFrame(frm_top, text="  👤 Cliente  ", padding=6)
        frm_cli.pack(fill=tk.X, pady=(0, 6))

        fila_cli = tk.Frame(frm_cli, bg=THEME["surface"])
        fila_cli.pack(fill=tk.X)

        ttk.Label(fila_cli, text="Seleccionar:").pack(side=tk.LEFT, padx=4)
        self._combo_cli = ttk.Combobox(fila_cli, width=22, state="readonly")
        self._combo_cli.pack(side=tk.LEFT, padx=4, pady=2)
        ttk.Button(
            fila_cli,
            text="🔄",
            width=3,
            command=self._cargar_clientes,
        ).pack(side=tk.LEFT, padx=2)
        self._cargar_clientes()

        # 2. Carrito
        frm_carrito = ttk.LabelFrame(
            frm_top, text="  🛒 Carrito de Compras  ", padding=4
        )
        frm_carrito.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Tabla + scrollbar
        frm_tabla = tk.Frame(frm_carrito, bg=THEME["bg"])
        frm_tabla.pack(fill=tk.BOTH, expand=True)

        cols = ("nombre", "cant", "subtotal")
        self._tree_carrito = ttk.Treeview(
            frm_tabla,
            columns=cols,
            show="headings",
            height=5,
        )
        for col, title, width in [
            ("nombre", "Pieza", 160),
            ("cant", "Cant.", 45),
            ("subtotal", "Subtotal", 100),
        ]:
            self._tree_carrito.heading(col, text=title)
            self._tree_carrito.column(col, width=width, anchor=tk.CENTER)

        self._tree_carrito.bind("<Double-1>", self._editar_cantidad_carrito)

        scr_car = ttk.Scrollbar(
            frm_tabla,
            orient=tk.VERTICAL,
            command=self._tree_carrito.yview,
        )
        self._tree_carrito.configure(yscrollcommand=scr_car.set)
        self._tree_carrito.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr_car.pack(side=tk.LEFT, fill=tk.Y)

        # Botones quitar / limpiar
        btn_row = tk.Frame(frm_carrito, bg=THEME["bg"])
        btn_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(
            btn_row,
            text="🗑️ Quitar",
            command=self._quitar_del_carrito,
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(
            btn_row,
            text="🧹 Limpiar todo",
            command=self._limpiar_carrito,
        ).pack(side=tk.LEFT, padx=4)

        # 3. Descuento
        frm_desc = ttk.LabelFrame(frm_top, text="  🏷️ Descuento  ", padding=6)
        frm_desc.pack(fill=tk.X, pady=(0, 6))

        fila_d = tk.Frame(frm_desc, bg=THEME["surface"])
        fila_d.pack(fill=tk.X)

        ttk.Label(fila_d, text="Desc %:").pack(side=tk.LEFT, padx=4)
        self._ent_descuento = ttk.Entry(fila_d, width=5)
        self._ent_descuento.insert(0, "0")
        self._ent_descuento.pack(side=tk.LEFT, padx=2)
        self._ent_descuento.bind("<KeyRelease>", lambda e: self._actualizar_carrito())

        ttk.Label(fila_d, text="Monto fijo:").pack(side=tk.LEFT, padx=(10, 2))
        self._ent_monto_fijo = ttk.Entry(fila_d, width=7)
        self._ent_monto_fijo.insert(0, "0")
        self._ent_monto_fijo.pack(side=tk.LEFT, padx=2)
        self._ent_monto_fijo.bind("<KeyRelease>", lambda e: self._actualizar_carrito())

        # 4. Totales
        frm_totales = tk.Frame(frm_top, bg=THEME["surface2"])
        frm_totales.pack(fill=tk.X, pady=(0, 4), ipadx=6, ipady=6)

        self._lbl_subtotal = tk.Label(
            frm_totales,
            text=f"Subtotal:       {MONEDA}0.00",
            bg=THEME["surface2"],
            fg=THEME["text"],
            font=("Cascadia Code", 10),
            anchor=tk.W,
        )
        self._lbl_subtotal.pack(fill=tk.X, padx=10, pady=2)

        self._lbl_descuento = tk.Label(
            frm_totales,
            text=f"Descuento:  -{MONEDA}0.00",
            bg=THEME["surface2"],
            fg=THEME["danger"],
            font=("Cascadia Code", 10),
            anchor=tk.W,
        )
        self._lbl_descuento.pack(fill=tk.X, padx=10, pady=2)

        tk.Frame(frm_totales, bg=THEME["border"], height=1).pack(
            fill=tk.X, padx=6, pady=4
        )

        self._lbl_total_final = tk.Label(
            frm_totales,
            text=f"TOTAL:          {MONEDA}0.00",
            bg=THEME["surface2"],
            fg=THEME["success"],
            font=("Cascadia Code", 12, "bold"),
            anchor=tk.W,
        )
        self._lbl_total_final.pack(fill=tk.X, padx=10, pady=4)

    # ══════════════════════════════════════════════════════════════
    #  CLIENTES
    # ══════════════════════════════════════════════════════════════
    def _cargar_clientes(self) -> None:
        clientes = self._cli_repo.get_all()
        self._clientes_lista = [None] + clientes
        valores = ["-- Sin cliente --"] + [
            f"{c.id_cliente} — {c.nombre}" for c in clientes
        ]
        self._combo_cli["values"] = valores
        self._combo_cli.current(0)

    def _get_cliente(self) -> tuple[Optional[str], str]:
        idx = self._combo_cli.current()
        if idx > 0 and len(self._clientes_lista) > idx:
            c = self._clientes_lista[idx]
            return c.id_cliente, c.nombre
        return None, "Publico General"

    # ══════════════════════════════════════════════════════════════
    #  ACCIONES — Stock
    # ══════════════════════════════════════════════════════════════
    def _seleccionar_pieza(self, event=None) -> None:
        sel = self._tree_stock.selection()
        if not sel:
            return
        valores = self._tree_stock.item(sel[0])["values"]
        id_pieza = str(valores[0])
        stock = int(valores[3])

        dialogo = tk.Toplevel(self.frame)
        dialogo.title("Agregar al carrito")
        dialogo.geometry("300x160")
        dialogo.resizable(False, False)
        dialogo.configure(bg=THEME["bg"])
        dialogo.grab_set()

        tk.Label(
            dialogo,
            text=str(valores[1]),
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI Semibold", 11),
        ).pack(pady=(16, 4))
        tk.Label(
            dialogo,
            text=f"Stock disponible: {stock}",
            bg=THEME["bg"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 9),
        ).pack()

        frm = tk.Frame(dialogo, bg=THEME["bg"])
        frm.pack(pady=8)
        ttk.Label(frm, text="Cantidad:").pack(side=tk.LEFT, padx=4)
        ent = ttk.Entry(frm, width=8)
        ent.insert(0, "1")
        ent.pack(side=tk.LEFT, padx=4)
        ent.focus()
        ent.select_range(0, tk.END)

        def confirmar(event=None):
            try:
                cant = int(ent.get())
                dialogo.destroy()
                self._agregar_al_carrito(id_pieza, cant)
            except ValueError:
                messagebox.showerror("Error", "Ingresa una cantidad válida.")

        ent.bind("<Return>", confirmar)
        ttk.Button(dialogo, text="Agregar", command=confirmar).pack(pady=4, ipadx=20)

    # ══════════════════════════════════════════════════════════════
    #  ACCIONES — Carrito
    # ══════════════════════════════════════════════════════════════
    def _agregar_al_carrito(self, id_pieza: str, cant: int) -> None:
        try:
            pieza = self._inv._repo.get(id_pieza)
            if pieza is None:
                raise ValueError(f"La pieza '{id_pieza}' no existe.")

            for item in self._carrito:
                if item.id_pieza == id_pieza:
                    nueva_cant = item.cantidad + cant
                    if pieza.cantidad < nueva_cant:
                        raise ValueError(
                            f"Stock insuficiente. Disponible: {pieza.cantidad}"
                        )
                    item.cantidad = nueva_cant
                    self._actualizar_carrito()
                    return

            if pieza.cantidad < cant:
                raise ValueError(f"Stock insuficiente. Disponible: {pieza.cantidad}")

            self._carrito.append(
                ItemCarrito(
                    id_pieza=id_pieza,
                    nombre=pieza.nombre,
                    cantidad=cant,
                    precio_unitario=pieza.precio_unitario,
                )
            )
            self._actualizar_carrito()

        except ValueError as ex:
            messagebox.showerror("Error", str(ex))

    def _quitar_del_carrito(self) -> None:
        sel = self._tree_carrito.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una pieza del carrito.")
            return
        idx = self._tree_carrito.index(sel[0])
        self._carrito.pop(idx)
        self._actualizar_carrito()

    def _limpiar_carrito(self) -> None:
        if not self._carrito:
            return
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el carrito?"):
            self._carrito.clear()
            self._actualizar_carrito()

    def _editar_cantidad_carrito(self, event=None) -> None:
        sel = self._tree_carrito.selection()
        if not sel:
            return
        idx = self._tree_carrito.index(sel[0])
        item = self._carrito[idx]
        pieza = self._inv._repo.get(item.id_pieza)

        dialogo = tk.Toplevel(self.frame)
        dialogo.title("Editar cantidad")
        dialogo.geometry("280x160")
        dialogo.resizable(False, False)
        dialogo.configure(bg=THEME["bg"])
        dialogo.grab_set()

        tk.Label(
            dialogo,
            text=item.nombre,
            bg=THEME["bg"],
            fg=THEME["text"],
            font=("Segoe UI Semibold", 11),
        ).pack(pady=(16, 4))

        stock_real = pieza.cantidad + item.cantidad
        tk.Label(
            dialogo,
            text=f"Stock disponible: {stock_real}",
            bg=THEME["bg"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 9),
        ).pack()

        frm = tk.Frame(dialogo, bg=THEME["bg"])
        frm.pack(pady=8)
        ttk.Label(frm, text="Nueva cantidad:").pack(side=tk.LEFT, padx=4)
        ent = ttk.Entry(frm, width=8)
        ent.insert(0, str(item.cantidad))
        ent.pack(side=tk.LEFT, padx=4)
        ent.focus()
        ent.select_range(0, tk.END)

        def confirmar(event=None):
            try:
                nueva_cant = int(ent.get())
                if nueva_cant <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0.")
                if nueva_cant > stock_real:
                    raise ValueError(f"Stock insuficiente. Disponible: {stock_real}")
                item.cantidad = nueva_cant
                dialogo.destroy()
                self._actualizar_carrito()
            except ValueError as ex:
                messagebox.showerror("Error", str(ex))

        ent.bind("<Return>", confirmar)
        ttk.Button(dialogo, text="✅ Actualizar", command=confirmar).pack(
            pady=4, ipadx=20
        )

    # ══════════════════════════════════════════════════════════════
    #  ACTUALIZAR TOTALES
    # ══════════════════════════════════════════════════════════════
    def _actualizar_carrito(self) -> None:
        self._tree_carrito.delete(*self._tree_carrito.get_children())
        subtotal = 0.0

        for item in self._carrito:
            self._tree_carrito.insert(
                "",
                tk.END,
                values=(
                    item.nombre,
                    item.cantidad,
                    f"{MONEDA}{item.subtotal:,.2f}",
                ),
            )
            subtotal += item.subtotal

        try:
            pct = float(self._ent_descuento.get() or 0)
            fijo = float(self._ent_monto_fijo.get() or 0)
        except ValueError:
            pct, fijo = 0.0, 0.0

        descuento = subtotal * (pct / 100) + fijo
        total_final = max(subtotal - descuento, 0)

        self._lbl_subtotal.config(text=f"Subtotal:       {MONEDA}{subtotal:,.2f}")
        self._lbl_descuento.config(text=f"Descuento:  -{MONEDA}{descuento:,.2f}")
        self._lbl_total_final.config(text=f"TOTAL:          {MONEDA}{total_final:,.2f}")

    # ══════════════════════════════════════════════════════════════
    #  CONFIRMAR VENTA
    # ══════════════════════════════════════════════════════════════
    def _confirmar_venta(self) -> None:
        if not self._carrito:
            messagebox.showwarning("Carrito vacío", "Agrega piezas al carrito primero.")
            return

        try:
            pct = float(self._ent_descuento.get() or 0)
            fijo = float(self._ent_monto_fijo.get() or 0)
        except ValueError:
            pct, fijo = 0.0, 0.0

        subtotal = sum(i.subtotal for i in self._carrito)
        descuento = subtotal * (pct / 100) + fijo
        total_final = max(subtotal - descuento, 0)

        resumen = tk.Toplevel(self.frame)
        resumen.title("Resumen de Venta")
        resumen.geometry("480x520")
        resumen.resizable(False, False)
        resumen.configure(bg=THEME["bg"])
        resumen.grab_set()

        tk.Label(
            resumen,
            text="RESUMEN DE VENTA",
            bg=THEME["bg"],
            fg=THEME["accent"],
            font=("Segoe UI Black", 14),
        ).pack(pady=(20, 4))

        tk.Label(
            resumen,
            text="Revisa los detalles antes de confirmar",
            bg=THEME["bg"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 9),
        ).pack(pady=(0, 12))

        frm_tabla = tk.Frame(resumen, bg=THEME["surface2"])
        frm_tabla.pack(fill=tk.X, padx=20, pady=(0, 8))

        cols = ("nombre", "cant", "precio", "subtotal")
        tree = ttk.Treeview(
            frm_tabla,
            columns=cols,
            show="headings",
            height=len(self._carrito) + 1,
        )
        for col, title, width in [
            ("nombre", "Pieza", 200),
            ("cant", "Cant.", 50),
            ("precio", "Precio", 90),
            ("subtotal", "Subtotal", 90),
        ]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor=tk.CENTER)

        for item in self._carrito:
            tree.insert(
                "",
                tk.END,
                values=(
                    item.nombre,
                    item.cantidad,
                    f"{MONEDA}{item.precio_unitario:,.2f}",
                    f"{MONEDA}{item.subtotal:,.2f}",
                ),
            )
        tree.pack(fill=tk.X, padx=4, pady=4)

        frm_tot = tk.Frame(resumen, bg=THEME["surface2"])
        frm_tot.pack(fill=tk.X, padx=20, pady=(0, 12))

        tk.Label(
            frm_tot,
            text=f"Subtotal:  {MONEDA}{subtotal:,.2f}",
            bg=THEME["surface2"],
            fg=THEME["text"],
            font=("Cascadia Code", 11),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=12, pady=2)

        tk.Label(
            frm_tot,
            text=f"Descuento: -{MONEDA}{descuento:,.2f}",
            bg=THEME["surface2"],
            fg=THEME["danger"],
            font=("Cascadia Code", 11),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=12, pady=2)

        tk.Frame(frm_tot, bg=THEME["border"], height=1).pack(fill=tk.X, padx=8, pady=4)

        tk.Label(
            frm_tot,
            text=f"TOTAL:     {MONEDA}{total_final:,.2f}",
            bg=THEME["surface2"],
            fg=THEME["success"],
            font=("Cascadia Code", 14, "bold"),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=12, pady=6)

        frm_btn = tk.Frame(resumen, bg=THEME["bg"])
        frm_btn.pack(fill=tk.X, padx=20, pady=8)

        items_venta = list(self._carrito)

        def procesar():
            resumen.destroy()
            try:
                id_cliente, nombre_cliente = self._get_cliente()

                ventas = self._ven.registrar_venta_multiple(
                    items=items_venta,
                    id_cliente=id_cliente,
                )

                num_venta = f"V{uuid.uuid4().hex[:8].upper()}"
                try:
                    pdf = self._comprobante_svc.generar(
                        items=items_venta,
                        subtotal=subtotal,
                        descuento=descuento,
                        total_final=total_final,
                        vendedor=self._app._auth.usuario.nombre,
                        num_venta=num_venta,
                        cliente=nombre_cliente,
                    )
                    pdf_ok = True
                except Exception as pdf_err:
                    pdf_ok = False
                    messagebox.showwarning(
                        "PDF", f"Venta registrada pero error en PDF:\n{pdf_err}"
                    )

                self._carrito.clear()
                self._ent_descuento.delete(0, tk.END)
                self._ent_descuento.insert(0, "0")
                self._ent_monto_fijo.delete(0, tk.END)
                self._ent_monto_fijo.insert(0, "0")
                self._actualizar_carrito()
                self._app.refresh()
                self._app.set_status(
                    f"Venta confirmada | "
                    f"{len(ventas)} piezas | Total: {MONEDA}{total_final:,.2f}"
                )

                if pdf_ok:
                    if messagebox.askyesno(
                        "Comprobante generado",
                        f"PDF guardado en:\n{pdf}\n\n¿Deseas abrir la carpeta?",
                    ):
                        import subprocess

                        subprocess.Popen(["explorer", str(pdf.parent)])

            except (ValueError, sqlite3.Error) as ex:
                messagebox.showerror("Error al confirmar venta", str(ex))

        ttk.Button(
            frm_btn,
            text="Confirmar y procesar",
            command=procesar,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        ttk.Button(
            frm_btn,
            text="Seguir editando",
            command=resumen.destroy,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

    # ══════════════════════════════════════════════════════════════
    #  BÚSQUEDA Y REFRESH
    # ══════════════════════════════════════════════════════════════
    def _on_search(self) -> None:
        query = self._search_var.get().strip()
        piezas = self._inv.buscar(query) if query else self._inv.listar()
        self._poblar_stock(piezas)

    def _poblar_stock(self, piezas) -> None:
        self._tree_stock.delete(*self._tree_stock.get_children())
        for p in piezas:
            tag = "low" if p.cantidad < 5 else ""
            self._tree_stock.insert(
                "",
                tk.END,
                tags=(tag,),
                values=(
                    p.id_pieza,
                    p.nombre,
                    p.categoria,
                    p.cantidad,
                    f"{MONEDA}{p.precio_unitario:,.2f}",
                ),
            )
        self._tree_stock.tag_configure("low", foreground=THEME["danger"])

    def refresh(self) -> None:
        self._poblar_stock(self._inv.listar())
        self._cargar_clientes()
