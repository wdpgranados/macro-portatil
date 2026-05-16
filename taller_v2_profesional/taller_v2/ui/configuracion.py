from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME
from services.auth_service import AuthService
from domain.usuario import ROLES


class ConfiguracionTab:

    def __init__(self, parent: ttk.Notebook, auth_svc: AuthService) -> None:
        self._auth = auth_svc
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self) -> None:
        self._build_usuarios()

    def _build_usuarios(self) -> None:
        frm = ttk.LabelFrame(self.frame, text="  👥 Gestión de Usuarios  ", padding=12)
        frm.pack(fill=tk.X, padx=16, pady=(12, 6))

        # Formulario
        ttk.Label(frm, text="Nombre:").grid(
            row=0, column=0, padx=(8, 4), pady=6, sticky=tk.E
        )
        self._ent_nombre = ttk.Entry(frm, width=18)
        self._ent_nombre.grid(row=0, column=1, padx=(0, 8), pady=6)

        ttk.Label(frm, text="Username:").grid(
            row=0, column=2, padx=(8, 4), pady=6, sticky=tk.E
        )
        self._ent_username = ttk.Entry(frm, width=14)
        self._ent_username.grid(row=0, column=3, padx=(0, 8), pady=6)

        ttk.Label(frm, text="Password:").grid(
            row=0, column=4, padx=(8, 4), pady=6, sticky=tk.E
        )
        self._ent_pass = ttk.Entry(frm, width=14, show="●")
        self._ent_pass.grid(row=0, column=5, padx=(0, 8), pady=6)

        ttk.Label(frm, text="Rol:").grid(
            row=0, column=6, padx=(8, 4), pady=6, sticky=tk.E
        )
        self._combo_rol = ttk.Combobox(frm, values=ROLES, width=10, state="readonly")
        self._combo_rol.current(1)
        self._combo_rol.grid(row=0, column=7, padx=(0, 8), pady=6)

        ttk.Button(frm, text="➕ Crear Usuario", command=self._crear_usuario).grid(
            row=0, column=8, padx=8, pady=6
        )

        # Tabla
        cols = ("id", "nombre", "username", "rol", "estado")
        self._tree = ttk.Treeview(frm, columns=cols, show="headings", height=6)
        for col, title, w in [
            ("id", "ID", 90),
            ("nombre", "Nombre", 150),
            ("username", "Usuario", 120),
            ("rol", "Rol", 90),
            ("estado", "Estado", 90),
        ]:
            self._tree.heading(col, text=title)
            self._tree.column(col, width=w, anchor=tk.CENTER)
        self._tree.grid(row=1, column=0, columnspan=9, padx=4, pady=8, sticky=tk.EW)

        ttk.Button(
            frm, text="🗑️ Desactivar seleccionado", command=self._desactivar
        ).grid(row=2, column=0, columnspan=3, pady=4, sticky=tk.W, padx=4)

    def _crear_usuario(self) -> None:
        try:
            usuario = self._auth.crear_usuario(
                nombre=self._ent_nombre.get(),
                username=self._ent_username.get(),
                password=self._ent_pass.get(),
                rol=self._combo_rol.get(),
            )
            self._ent_nombre.delete(0, tk.END)
            self._ent_username.delete(0, tk.END)
            self._ent_pass.delete(0, tk.END)
            self.refresh()
            messagebox.showinfo("OK", f"Usuario '{usuario.username}' creado.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _desactivar(self) -> None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un usuario.")
            return
        id_usr = self._tree.item(sel[0])["values"][0]
        if id_usr == self._auth.usuario.id_usuario:
            messagebox.showerror("Error", "No puedes desactivarte a ti mismo.")
            return
        if messagebox.askyesno("Confirmar", "¿Desactivar este usuario?"):
            self._auth._repo.desactivar(id_usr)
            self.refresh()

    def refresh(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for u in self._auth.listar_usuarios():
            self._tree.insert(
                "",
                tk.END,
                values=(
                    u.id_usuario,
                    u.nombre,
                    u.username,
                    u.rol,
                    "✅ Activo" if u.activo else "❌ Inactivo",
                ),
            )
