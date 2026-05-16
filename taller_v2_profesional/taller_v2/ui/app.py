"""
ui/app.py — Ventana principal de la aplicación.

Responsabilidades:
- Configurar el tema visual de ttk.
- Crear y conectar las capas (repos → servicios → tabs).
- Exponer refresh() global que actualiza todos los tabs.
- Mantener el reloj en tiempo real del header.
"""

from __future__ import annotations

from datetime import datetime

import tkinter as tk
from tkinter import ttk

from config import DB_PATH, THEME
from repositories import SQLiteInventarioRepo, SQLiteVentasRepo
from services import InventarioService, VentasService

from ui.dashboard import DashboardTab
from ui.inventario import InventarioTab
from ui.ventas import VentasTab
from ui.reportes import ReportesTab


# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE TEMA
# ══════════════════════════════════════════════════════════════════
def _apply_theme(root: tk.Tk) -> None:
    """Aplica el tema oscuro a todos los widgets ttk."""
    style = ttk.Style(root)
    style.theme_use("clam")

    base = {
        "background":       THEME["surface"],
        "foreground":       THEME["text"],
        "bordercolor":      THEME["border"],
        "troughcolor":      THEME["bg"],
        "selectbackground": THEME["accent"],
        "selectforeground": THEME["text"],
        "fieldbackground":  THEME["surface2"],
        "font":             ("Segoe UI", 13),
    }
    for widget in (
        "TFrame", "TLabelframe", "TLabelframe.Label",
        "TLabel", "TButton", "TEntry", "TCombobox",
        "TNotebook", "TNotebook.Tab",
        "Treeview", "Treeview.Heading",
    ):
        try:
            style.configure(widget, **base)
        except Exception:
            pass

    style.configure(
        "TButton",
        background=THEME["accent"], foreground="#ffffff",
        padding=(12, 6), relief="flat",
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TButton",
        background=[("active", THEME["accent2"]), ("pressed", THEME["accent2"])],
        relief=[("pressed", "flat")],
    )
    style.configure(
        "Treeview",
        rowheight=30,
        background=THEME["surface2"], fieldbackground=THEME["surface2"],
        foreground=THEME["text"], font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background=THEME["surface"], foreground=THEME["accent"],
        font=("Segoe UI Semibold", 10), relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["accent"])],
        foreground=[("selected", "#ffffff")],
    )
    style.configure(
        "TNotebook", background=THEME["bg"], tabmargins=[2, 5, 0, 0]
    )
    style.configure(
        "TNotebook.Tab",
        background=THEME["surface"], foreground=THEME["text_dim"],
        padding=[16, 8], font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", THEME["surface2"])],
        foreground=[("selected", THEME["accent"])],
    )


# ══════════════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ══════════════════════════════════════════════════════════════════
class TallerApp(tk.Tk):
    """
    Ventana raíz de la aplicación.

    Realiza la inyección de dependencias:
        DB path → Repos → Services → UI Tabs
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("🖥️  Gestión de Taller – v2.0")
        self.geometry("1180x750")
        self.configure(bg=THEME["bg"])
        self.resizable(True, True)

        # ── Inyección de dependencias ──────────────────────────────
        inv_repo = SQLiteInventarioRepo(DB_PATH)
        ven_repo = SQLiteVentasRepo(DB_PATH)
        self.inv_svc = InventarioService(inv_repo)
        self.ven_svc = VentasService(inv_repo, ven_repo)

        _apply_theme(self)
        self._build_header()
        self._build_tabs()
        self._build_statusbar()
        self.refresh()

    # ── Header ────────────────────────────────────────────────────
    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=THEME["surface"], height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(
            hdr, text="🖥️  MACRO PORTATIL",
            bg=THEME["surface"], fg=THEME["accent"],
            font=("Segoe UI Black", 16),
        ).pack(side=tk.LEFT, padx=20)
        #agregagando un botón para actualizar
        ttk.Button(
            hdr, text="🔄 Actualizar", command=self.refresh
        ).pack(side=tk.LEFT, padx=12)

        self._clock_lbl = tk.Label(
            hdr, text="", bg=THEME["surface"],
            fg=THEME["text_dim"], font=("Segoe UI", 13),
        )
        self._clock_lbl.pack(side=tk.RIGHT, padx=20)
        self._tick()

    def _tick(self) -> None:
        ahora = datetime.now()
        dias = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sábado","Domingo"]
        meses = ["Ene","Feb","Mar","Abr","May","Jun",
                 "Jul","Ago","Sep","Oct","Nov","Dic"]
        dia_nombre = dias[ahora.weekday()]
        mes_nombre = meses[ahora.month - 1]
        
        self._clock_lbl.config(
            text=f"📅{dia_nombre} {ahora.day:02d} {mes_nombre} {ahora.year}  🕐 {ahora.strftime('%H:%M:%S')}"
        )
        self.after(1000, self._tick)

    # ── Tabs ──────────────────────────────────────────────────────
    def _build_tabs(self) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self._dash  = DashboardTab(nb,  self.inv_svc, self.ven_svc)
        self._inv   = InventarioTab(nb, self.inv_svc, self)
        self._ven   = VentasTab(nb,     self.ven_svc, self.inv_svc, self)
        self._rep   = ReportesTab(nb,   self.ven_svc, self.inv_svc)

        nb.add(self._dash.frame, text="  📊 Dashboard  ")
        nb.add(self._inv.frame,  text="  📦 Inventario  ")
        nb.add(self._ven.frame,  text="  🛒 Registrar Salida  ")
        nb.add(self._rep.frame,  text="  📈 Reportes  ")

    # ── Status Bar ────────────────────────────────────────────────
    def _build_statusbar(self) -> None:
        bar = tk.Frame(self, bg=THEME["surface"], height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="✅ Sistema listo")
        tk.Label(
            bar, textvariable=self._status_var,
            bg=THEME["surface"], fg=THEME["text_dim"],
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, padx=12)

    def set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    # ── Refresh global ────────────────────────────────────────────
    def refresh(self) -> None:
        """Actualiza todos los tabs con los datos más recientes de la DB."""
        self._inv.refresh()
        self._ven.refresh()
        self._dash.refresh()
