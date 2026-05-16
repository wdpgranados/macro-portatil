from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable

from config import THEME
from services.auth_service import AuthService


class LoginWindow(tk.Tk):

    def __init__(self, auth_svc: AuthService, on_success: Callable) -> None:
        super().__init__()
        self._auth = auth_svc
        self._on_success = on_success

        self.title("🔐 MACRO PORTATIL — Iniciar Sesión")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(bg=THEME["bg"])
        self._centrar()
        self._build()
        self.bind("<Return>", lambda e: self._login())

    def _centrar(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"420x340+{x}+{y}")

    def _build(self) -> None:
        tk.Label(
            self,
            text="🖥️  MACRO PORTATIL",
            bg=THEME["bg"],
            fg=THEME["accent"],
            font=("Segoe UI Black", 18),
        ).pack(pady=(30, 4))

        tk.Label(
            self,
            text="Sistema de Gestión de Taller",
            bg=THEME["bg"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 10),
        ).pack(pady=(0, 24))

        frm = tk.Frame(self, bg=THEME["surface"], padx=30, pady=24)
        frm.pack(fill=tk.X, padx=40)

        ttk.Label(frm, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=6)
        self._ent_user = ttk.Entry(frm, width=24, font=("Segoe UI", 11))
        self._ent_user.grid(row=0, column=1, padx=8, pady=6)
        self._ent_user.focus()

        ttk.Label(frm, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=6)
        self._ent_pass = ttk.Entry(frm, width=24, show="●", font=("Segoe UI", 11))
        self._ent_pass.grid(row=1, column=1, padx=8, pady=6)

        ttk.Button(frm, text="🔐  Ingresar", command=self._login).grid(
            row=2, column=0, columnspan=2, pady=(16, 0), sticky=tk.EW
        )

        self._msg_var = tk.StringVar(value="Usuario por defecto: admin / admin123")
        tk.Label(
            self,
            textvariable=self._msg_var,
            bg=THEME["bg"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 9),
            wraplength=380,
        ).pack(pady=12)

    def _login(self) -> None:
        username = self._ent_user.get().strip()
        password = self._ent_pass.get()

        if not username or not password:
            self._msg_var.set("⚠️ Completa usuario y contraseña.")
            return

        exito, mensaje = self._auth.login(username, password)

        if exito:
            self._msg_var.set(mensaje)
            self.after(600, self._abrir_app)
        else:
            self._msg_var.set(mensaje)
            self._ent_pass.delete(0, tk.END)

    def _abrir_app(self) -> None:
        self.destroy()
        self._on_success(self._auth)
